"""
Campfire class for orchestrating multimodal LLM workflows.
"""

import asyncio
import logging
import yaml
import re
from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from pathlib import Path

from .torch import Torch
from .camper import Camper
from ..party_box.box_driver import BoxDriver
from ..mcp.protocol import MCPProtocol
from ..utils.hash_utils import generate_uuid_hash
from .default_auditor import DefaultAuditor


logger = logging.getLogger(__name__)


class Campfire:
    """
    A Campfire orchestrates a group of Campers (models/tools) to process
    torches (data) and pass results via MCP to other campfires.
    
    Each campfire has a specific purpose and contains one or more campers
    that work together to process incoming torches and generate new ones.
    """
    
    def __init__(
        self,
        name: str,
        campers: List[Camper],
        party_box: BoxDriver,
        mcp_protocol: Optional[MCPProtocol] = None,
        config: Dict[str, Any] = None
    ):
        """
        Initialize a Campfire.
        
        Args:
            name: Unique name for this campfire
            campers: List of campers in this campfire
            party_box: Storage driver for assets
            mcp_protocol: MCP protocol for communication
            config: Additional configuration
        """
        self.name = name
        self.campers = campers
        self.party_box = party_box
        self.mcp_protocol = mcp_protocol
        self.config = config or {}
        
        # State management
        self.is_running = False
        self.processed_torches: Dict[str, Torch] = {}
        self.torch_queue: asyncio.Queue = asyncio.Queue()
        
        # Configuration
        self.max_concurrent_tasks = self.config.get('max_concurrent_tasks', 3)
        self.torch_ttl = self.config.get('torch_ttl_hours', 24)
        self.auto_cleanup = self.config.get('auto_cleanup', True)
        
        # Callbacks
        self.on_torch_processed: Optional[Callable[[Torch], None]] = None
        self.on_error: Optional[Callable[[Exception, Torch], None]] = None
        
        # Setup campers
        for camper in self.campers:
            camper.set_party_box(self.party_box)
            camper.set_campfire_name(self.name)

        # Establish a stable campfire address (at-hash) and map auditor
        self.at_hash = self.config.get('at_hash') or generate_uuid_hash(self.name)
        self.config['at_hash'] = self.at_hash
        # Global routing policy: by default, route all inbound to auditor
        self.route_all_to_auditor = bool(self.config.get('route_all_to_auditor', True))

        # Try to locate the auditor camper
        self.auditor_camper = None
        auditor_name = self.config.get('auditor_camper_name')
        if auditor_name:
            for c in self.campers:
                if getattr(c, 'name', '').lower() == str(auditor_name).lower():
                    self.auditor_camper = c
                    break
        if not self.auditor_camper:
            for c in self.campers:
                role = getattr(c, '_role', '')
                if 'auditor' in str(role).lower() or 'auditor' in getattr(c, 'name', '').lower():
                    self.auditor_camper = c
                    break
        if self.auditor_camper and hasattr(self.auditor_camper, 'set_at_name'):
            # Ensure the auditor responds to the campfire address
            self.auditor_camper.set_at_name(self.at_hash)
        
        # Create auditor engine for orchestration
        try:
            self.auditor_engine = DefaultAuditor(
                party_box=self.party_box,
                zeitgeist_engine=None,
                config=self.config.get('auditor_config', {})
            )
        except Exception:
            self.auditor_engine = None
    
    async def start(self) -> None:
        """Start the campfire processing loop."""
        if self.is_running:
            logger.warning(f"Campfire {self.name} is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting campfire: {self.name}")
        
        # Start processing tasks
        tasks = []
        for i in range(self.max_concurrent_tasks):
            task = asyncio.create_task(self._processing_loop())
            tasks.append(task)
        
        # Start cleanup task if enabled
        if self.auto_cleanup:
            cleanup_task = asyncio.create_task(self._cleanup_loop())
            tasks.append(cleanup_task)
        
        # Subscribe to MCP channels if protocol is available
        if self.mcp_protocol:
            await self._setup_mcp_subscriptions()
        
        # Wait for all tasks to complete
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info(f"Campfire {self.name} processing cancelled")
        finally:
            self.is_running = False
    
    async def stop(self) -> None:
        """Stop the campfire processing."""
        logger.info(f"Stopping campfire: {self.name}")
        self.is_running = False
        
        # Cancel any pending tasks
        for task in asyncio.all_tasks():
            if not task.done() and task.get_name().startswith(f"campfire_{self.name}"):
                task.cancel()
    
    async def process_torch(self, torch: Torch) -> List[Torch]:
        """
        Process a single torch through campers, with @mention routing.
        - If `route_all_to_auditor` is True and an auditor engine exists, run temporal preemptive RAG optimization.
        - Else, if `torch.metadata['target_camper_at_names']` includes the campfire's at-hash,
          route exclusively to the auditor camper.
        - Otherwise, if mentions exist, route to matching campers by their `at_name`.
        - If no mentions or no matches, broadcast to all campers.
        """
        logger.info(f"Processing torch {torch.torch_id} in campfire {self.name}")

        try:
            # Temporal preemptive path: auditor orchestrates team and returns consensus
            if self.route_all_to_auditor and self.auditor_engine:
                mode = 'temporal'
                try:
                    mode = str(torch.metadata.get('auditor_mode', 'temporal')).lower()
                except Exception:
                    pass
                if mode == 'experiential' and hasattr(self.auditor_engine, 'experiential_simulation_rag_tuning'):
                    final = await self.auditor_engine.experiential_simulation_rag_tuning(
                        original_torch=torch,
                        campers=self.campers,
                        valley_at_hash=self.at_hash
                    )
                else:
                    final = await self.auditor_engine.temporal_preemptive_rag_optimization(
                        original_torch=torch,
                        campers=self.campers,
                        valley_at_hash=self.at_hash
                    )
                # Ensure campfire address is present in metadata
                try:
                    final.metadata = final.metadata or {}
                    final.metadata['campfire_at_hash'] = self.at_hash
                except Exception:
                    pass
                return [final] if isinstance(final, Torch) else []

            output_torches: List[Torch] = []

            # Resolve target mentions
            mentions = torch.metadata.get('target_camper_at_names') or []
            if not mentions and isinstance(torch.claim, str):
                # Fallback direct parse for safety
                mentions = [m.lstrip('@') for m in re.findall(r'@([A-Za-z0-9_.\-]+)', torch.claim or '')]
                if mentions:
                    existing = torch.metadata.get('target_camper_at_names', [])
                    torch.metadata['target_camper_at_names'] = list(set(existing) | set(mentions))

            # Decide target campers
            target_campers: List[Camper] = []
            if self.at_hash and any(m == self.at_hash for m in mentions):
                # Messages to the campfire address go to the auditor
                if self.auditor_camper:
                    target_campers = [self.auditor_camper]
                else:
                    target_campers = []  # No auditor found; fall back to default broadcast below
            elif mentions:
                # Route to campers whose at_name matches a mention
                mention_set = set(mentions)
                for c in self.campers:
                    at_name = c.get_at_name() if hasattr(c, 'get_at_name') else getattr(c, 'at_name', None)
                    if at_name and at_name in mention_set:
                        target_campers.append(c)

            # If no specific targets, broadcast to all campers
            campers_to_process = target_campers if target_campers else self.campers

            for camper in campers_to_process:
                logger.debug(f"Processing torch with camper: {camper.__class__.__name__}")
                try:
                    result_torches = await camper.process(torch)
                    if result_torches:
                        if isinstance(result_torches, Torch):
                            result_torches = [result_torches]
                        for result in result_torches:
                            result.source_campfire = self.name
                            result.metadata['processed_by'] = camper.__class__.__name__
                            # Ensure campfire address propagates
                            try:
                                result.metadata['campfire_at_hash'] = self.at_hash
                            except Exception:
                                pass
                            output_torches.append(result)
                except Exception as e:
                    logger.error(f"Error processing torch with camper {camper.__class__.__name__}: {str(e)}")
                    if self.on_error:
                        self.on_error(e, torch)

            # Track processed torches
            for t in output_torches:
                self.processed_torches[t.torch_id] = t
                if self.on_torch_processed:
                    self.on_torch_processed(t)

            return output_torches
        except Exception as e:
            logger.error(f"Failed to process torch in campfire {self.name}: {e}")
            if self.on_error:
                self.on_error(e, torch)
            return []