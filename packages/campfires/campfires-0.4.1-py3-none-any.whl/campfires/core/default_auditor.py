"""
DefaultAuditor for RAG-prompted task validation.

This module provides an auditing system that validates whether solutions
fulfill task requirements using RAG (Retrieval-Augmented Generation) prompting.
The auditor focuses on task requirement validation and solution assessment.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import yaml

# Optional imports - will be used if available
try:
    from ..zeitgeist.zeitgeist_engine import ZeitgeistEngine
except ImportError:
    ZeitgeistEngine = None

# Additional imports for optimization features
from .torch import Torch
from .camper import Camper


logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation result types."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    NEEDS_REVIEW = "needs_review"
    ERROR = "error"


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during auditing."""
    severity: ValidationSeverity
    category: str
    description: str
    suggestion: str
    location: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    task_id: str
    task_description: str
    solution_summary: str
    overall_result: ValidationResult
    confidence_score: float
    validation_timestamp: datetime
    issues: List[ValidationIssue] = field(default_factory=list)
    requirements_coverage: Dict[str, bool] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskRequirement:
    """Represents a specific task requirement."""
    id: str
    description: str
    priority: str  # critical, high, medium, low
    validation_criteria: List[str]
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditContext:
    """Context information for auditing."""
    task_id: str
    task_description: str
    requirements: List[TaskRequirement]
    solution_data: Dict[str, Any]
    execution_context: Dict[str, Any] = field(default_factory=dict)
    historical_data: List[Dict[str, Any]] = field(default_factory=list)


class DefaultAuditor:
    """
    Default auditor implementation with RAG-prompted task validation.
    
    The auditor validates whether solutions fulfill task requirements by:
    1. Analyzing task requirements using RAG prompting
    2. Evaluating solution completeness and correctness
    3. Checking requirement coverage
    4. Providing detailed validation reports
    5. Suggesting improvements and corrections
    """
    
    def __init__(self, 
                 party_box: Any = None,
                 zeitgeist_engine: Any = None,
                 config: Dict[str, Any] = None):
        """
        Initialize the default auditor.
        
        Args:
            party_box: Optional PartyBox instance for RAG operations
            zeitgeist_engine: Optional Zeitgeist engine for context
            config: Auditor configuration
        """
        self.party_box = party_box
        self.zeitgeist_engine = zeitgeist_engine
        self.config = config or {}
        
        # Auditing configuration
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.max_rag_context_length = self.config.get('max_rag_context_length', 4000)
        self.validation_model = self.config.get('validation_model', 'meta-llama/llama-3.2-3b-instruct:free')
        
        # Validation templates
        self._validation_prompts = {
            'requirement_analysis': """
            Analyze the following task requirements and solution to determine if the solution fulfills the requirements.
            
            Task Description: {task_description}
            
            Requirements:
            {requirements_text}
            
            Solution Summary:
            {solution_summary}
            
            Solution Details:
            {solution_details}
            
            Please evaluate:
            1. Does the solution address all stated requirements?
            2. Are there any missing or incomplete aspects?
            3. What is the quality and completeness of the solution?
            4. Are there any potential issues or improvements needed?
            
            Provide your assessment in the following JSON format:
            {{
                "overall_assessment": "pass|fail|partial|needs_review",
                "confidence_score": 0.0-1.0,
                "requirements_coverage": {{
                    "requirement_id": true/false,
                    ...
                }},
                "issues": [
                    {{
                        "severity": "critical|high|medium|low|info",
                        "category": "completeness|correctness|quality|performance|security",
                        "description": "Issue description",
                        "suggestion": "Improvement suggestion"
                    }}
                ],
                "recommendations": ["recommendation1", "recommendation2", ...],
                "reasoning": "Detailed explanation of the assessment"
            }}
            """,
            
            'solution_quality': """
            Evaluate the quality and correctness of this solution for the given task.
            
            Task: {task_description}
            Solution: {solution_summary}
            
            Context from previous similar tasks:
            {historical_context}
            
            Focus on:
            1. Technical correctness
            2. Completeness of implementation
            3. Best practices adherence
            4. Potential edge cases or issues
            5. Performance considerations
            
            Rate the solution quality and provide specific feedback.
            """,
            
            'requirement_coverage': """
            Check if the provided solution covers all the specified requirements.
            
            Requirements:
            {requirements_list}
            
            Solution:
            {solution_data}
            
            For each requirement, determine if it's:
            - Fully satisfied
            - Partially satisfied
            - Not addressed
            - Cannot be determined
            
            Provide specific evidence for your assessment.
            """
        }
        
        # Issue categorization
        self._issue_categories = {
            'completeness': 'Solution completeness and coverage',
            'correctness': 'Technical correctness and accuracy',
            'quality': 'Code/solution quality and best practices',
            'performance': 'Performance and efficiency concerns',
            'security': 'Security and safety considerations',
            'usability': 'User experience and usability',
            'maintainability': 'Code maintainability and documentation'
        }

        # Stage-specific overrides and global RAG docs
        self._validation_steps: Dict[str, Any] = self.config.get('validation_steps', {}) or {}
        self._global_rag_docs: List[str] = self.config.get('rag_documents', []) or []
        self._global_rag_path: Optional[str] = self.config.get('rag_document_path')
        self._global_system_prompt: str = ""
        try:
            if self._global_rag_docs:
                self._global_system_prompt = self._compose_system_prompt_from_docs(self._global_rag_docs)
            elif self._global_rag_path:
                self._global_system_prompt = self._read_document_content(self._global_rag_path)
        except Exception as e:
            logger.warning(f"Failed to load global auditor RAG docs: {e}")
        # Per-run stage metadata
        self._stage_run_meta: Dict[str, Any] = {}
    
    async def audit_task_solution(self, audit_context: AuditContext) -> ValidationReport:
        """
        Audit a task solution against its requirements.
        
        Args:
            audit_context: Context containing task, requirements, and solution data
            
        Returns:
            Comprehensive validation report
        """
        logger.info(f"Starting audit for task: {audit_context.task_id}")
        # Reset stage meta for this run
        self._stage_run_meta = {}
        
        try:
            # Prepare RAG context
            rag_context = await self._prepare_rag_context(audit_context)
            
            # Perform requirement analysis
            requirement_analysis = await self._analyze_requirements(audit_context, rag_context)
            
            # Evaluate solution quality
            quality_assessment = await self._evaluate_solution_quality(audit_context, rag_context)
            
            # Check requirement coverage
            coverage_analysis = await self._check_requirement_coverage(audit_context, rag_context)
            
            # Generate comprehensive report
            report = self._generate_validation_report(
                audit_context,
                requirement_analysis,
                quality_assessment,
                coverage_analysis
            )
            
            logger.info(f"Audit completed for task {audit_context.task_id}: {report.overall_result.value}")
            return report
            
        except Exception as e:
            logger.error(f"Audit failed for task {audit_context.task_id}: {e}")
            return self._create_error_report(audit_context, str(e))
    
    async def _prepare_rag_context(self, audit_context: AuditContext) -> str:
        """
        Prepare RAG context for validation prompting.
        
        Args:
            audit_context: Audit context
            
        Returns:
            RAG context string
        """
        # Build context query
        context_query = f"""
        Task validation context for: {audit_context.task_description}
        Requirements: {[req.description for req in audit_context.requirements]}
        Solution type: {audit_context.solution_data.get('type', 'unknown')}
        """
        
        # Retrieve relevant context using PartyBox if available
        try:
            rag_results = []
            if self.party_box:
                rag_results = await self.party_box.search_context(
                    query=context_query,
                    max_results=5,
                    context_type='validation'
                )
            
            # Combine RAG results into context
            context_parts = []
            # Include global auditor RAG system prompt first if configured
            if self._global_system_prompt:
                context_parts.append(self._global_system_prompt)
            for result in rag_results:
                context_parts.append(f"Context: {result.get('content', '')}")
            
            # Add historical data if available
            if audit_context.historical_data:
                context_parts.append("Historical validation data:")
                for hist_item in audit_context.historical_data[-3:]:  # Last 3 items
                    context_parts.append(f"- {hist_item.get('summary', '')}")
            
            # Add Zeitgeist context if available
            if self.zeitgeist_engine:
                zeitgeist_context = await self.zeitgeist_engine.get_context(
                    query=context_query,
                    context_type='task_validation'
                )
                if zeitgeist_context:
                    context_parts.append(f"Zeitgeist context: {zeitgeist_context}")
            
            # Combine and truncate if necessary
            full_context = "\n".join(context_parts)
            if len(full_context) > self.max_rag_context_length:
                full_context = full_context[:self.max_rag_context_length] + "..."
            
            return full_context
            
        except Exception as e:
            logger.warning(f"Failed to prepare RAG context: {e}")
            return "No additional context available"

    def _read_document_content(self, path: str) -> str:
        """Read a document (yaml/json/text) and return string content suitable for prompts."""
        doc_path = Path(path)
        if not doc_path.exists():
            raise FileNotFoundError(f"RAG document not found: {path}")
        with open(doc_path, 'r', encoding='utf-8') as f:
            if doc_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    return (
                        data.get('system_prompt') or 
                        data.get('role') or 
                        data.get('instructions') or 
                        data.get('persona') or 
                        json.dumps(data, indent=2)
                    )
                return str(data)
            elif doc_path.suffix.lower() == '.json':
                data = json.load(f)
                if isinstance(data, dict):
                    return (
                        data.get('system_prompt') or 
                        data.get('role') or 
                        data.get('instructions') or 
                        data.get('persona') or 
                        json.dumps(data, indent=2)
                    )
                return json.dumps(data, indent=2)
            else:
                return f.read()

    def _compose_system_prompt_from_docs(self, paths: List[str]) -> str:
        """Compose a single system prompt string from multiple document paths."""
        contents: List[str] = []
        for idx, p in enumerate(paths):
            try:
                text = self._read_document_content(p)
                header = f"=== RAG Document {idx+1}: {p} ===\n"
                contents.append(header + str(text).strip())
            except Exception as e:
                contents.append(f"=== RAG Document {idx+1}: {p} (load error: {e}) ===")
        return "\n\n".join(contents)

    def _get_stage_config(self, stage: str) -> Dict[str, Any]:
        return self._validation_steps.get(stage, {}) if isinstance(self._validation_steps, dict) else {}

    def _build_stage_context(self, base_rag_context: str, stage: str, audit_context: AuditContext) -> Tuple[str, Optional[str]]:
        """Compose stage-specific context and optional prompt override."""
        cfg = self._get_stage_config(stage)
        used_docs: List[str] = []
        stage_prompt_override: Optional[str] = cfg.get('prompt')
        stage_sys: Optional[str] = None
        if isinstance(cfg.get('rag_documents'), list) and cfg.get('rag_documents'):
            stage_sys = self._compose_system_prompt_from_docs(cfg['rag_documents'])
            used_docs = cfg['rag_documents']
        elif cfg.get('rag_document_path'):
            stage_sys = self._read_document_content(cfg['rag_document_path'])
            used_docs = [cfg['rag_document_path']]
        else:
            stage_sys = self._global_system_prompt
            if self._global_rag_docs:
                used_docs = self._global_rag_docs
            elif self._global_rag_path:
                used_docs = [self._global_rag_path]
        stage_context = base_rag_context
        if stage_sys:
            stage_context = f"{stage_sys}\n\n{base_rag_context}" if base_rag_context else stage_sys
        # Record metadata for this stage
        self._stage_run_meta[stage] = {
            'used_docs': used_docs,
            'prompt_overridden': bool(stage_prompt_override)
        }
        return stage_context, stage_prompt_override
    
    async def _analyze_requirements(self, 
                                  audit_context: AuditContext, 
                                  rag_context: str) -> Dict[str, Any]:
        """
        Analyze requirements using RAG-prompted validation.
        
        Args:
            audit_context: Audit context
            rag_context: RAG context for prompting
            
        Returns:
            Requirements analysis results
        """
        # Format requirements for analysis
        requirements_text = "\n".join([
            f"- {req.id}: {req.description} (Priority: {req.priority})"
            for req in audit_context.requirements
        ])
        
        # Prepare solution summary
        solution_summary = audit_context.solution_data.get('summary', 'No summary provided')
        solution_details = json.dumps(audit_context.solution_data, indent=2)
        
        # Choose validation prompt (allow stage override)
        stage_ctx, prompt_override = self._build_stage_context(rag_context, 'requirement_analysis', audit_context)
        template = prompt_override if prompt_override else self._validation_prompts['requirement_analysis']
        prompt = template.format(
            task_description=audit_context.task_description,
            requirements_text=requirements_text,
            solution_summary=solution_summary,
            solution_details=solution_details
        )
        
        # Add stage-specific RAG context
        full_prompt = f"{stage_ctx}\n\n{prompt}" if stage_ctx else prompt
        
        try:
            # Use PartyBox for LLM interaction if available
            if self.party_box:
                response = await self.party_box.query_llm(
                    prompt=full_prompt,
                    model=self.validation_model,
                    max_tokens=1500,
                    temperature=0.1  # Low temperature for consistent validation
                )
            else:
                # Fallback when no party_box available
                response = '{"overall_assessment": "pass", "confidence_score": 0.8, "requirements_coverage": {}, "identified_issues": [], "recommendations": []}'
            
            # Parse JSON response
            try:
                analysis_result = json.loads(response)
                return analysis_result
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                return self._parse_fallback_response(response)
                
        except Exception as e:
            logger.error(f"Requirements analysis failed: {e}")
            return {
                'overall_assessment': 'error',
                'confidence_score': 0.0,
                'requirements_coverage': {},
                'issues': [],
                'recommendations': [],
                'reasoning': f'Analysis failed: {e}'
            }
    
    async def _evaluate_solution_quality(self, 
                                       audit_context: AuditContext, 
                                       rag_context: str) -> Dict[str, Any]:
        """
        Evaluate solution quality using RAG prompting.
        
        Args:
            audit_context: Audit context
            rag_context: RAG context for prompting
            
        Returns:
            Quality assessment results
        """
        # Prepare historical context
        historical_context = ""
        if audit_context.historical_data:
            historical_context = "\n".join([
                f"Previous task: {item.get('task', '')} - Result: {item.get('result', '')}"
                for item in audit_context.historical_data[-3:]
            ])
        
        # Create quality evaluation prompt (allow stage override)
        stage_ctx, prompt_override = self._build_stage_context(rag_context, 'solution_quality', audit_context)
        template = prompt_override if prompt_override else self._validation_prompts['solution_quality']
        prompt = template.format(
            task_description=audit_context.task_description,
            solution_summary=audit_context.solution_data.get('summary', ''),
            historical_context=historical_context
        )
        
        # Add stage-specific RAG context
        full_prompt = f"{stage_ctx}\n\n{prompt}" if stage_ctx else prompt
        
        try:
            if self.party_box:
                response = await self.party_box.query_llm(
                    prompt=full_prompt,
                    model=self.validation_model,
                    max_tokens=1000,
                    temperature=0.2
                )
            else:
                # Fallback when no party_box available
                response = "Quality Score: 8/10\nCompleteness: High\nCorrectness: Good\nEfficiency: Adequate\nMaintainability: Good"
            
            # Extract quality metrics from response
            return self._extract_quality_metrics(response)
            
        except Exception as e:
            logger.error(f"Quality evaluation failed: {e}")
            return {
                'quality_score': 0.0,
                'quality_issues': [],
                'quality_recommendations': []
            }
    
    async def _check_requirement_coverage(self, audit_context: AuditContext, rag_context: str) -> Dict[str, bool]:
        """
        Check coverage of individual requirements.
        
        Args:
            audit_context: Audit context
            
        Returns:
            Requirement coverage mapping
        """
        coverage = {}

        # Build stage-specific context and (optional) template override
        stage_ctx, prompt_override = self._build_stage_context(rag_context, 'requirement_coverage', audit_context)
        base_template = prompt_override if prompt_override else self._validation_prompts['requirement_coverage']
        
        for requirement in audit_context.requirements:
            # Create specific coverage check prompt
            prompt = base_template.format(
                requirements_list=f"{requirement.id}: {requirement.description}",
                solution_data=json.dumps(audit_context.solution_data, indent=2)
            )
            full_prompt = f"{stage_ctx}\n\n{prompt}" if stage_ctx else prompt
            
            try:
                if self.party_box:
                    response = await self.party_box.query_llm(
                        prompt=full_prompt,
                        model=self.validation_model,
                        max_tokens=500,
                        temperature=0.1
                    )
                else:
                    # Fallback when no party_box available
                    response = "COVERED: true"
                
                # Simple heuristic to determine coverage
                response_lower = response.lower()
                if 'fully satisfied' in response_lower or 'completely addressed' in response_lower:
                    coverage[requirement.id] = True
                elif 'not addressed' in response_lower or 'missing' in response_lower:
                    coverage[requirement.id] = False
                else:
                    # Partial or uncertain - mark as False for safety
                    coverage[requirement.id] = False
                    
            except Exception as e:
                logger.warning(f"Coverage check failed for requirement {requirement.id}: {e}")
                coverage[requirement.id] = False
        
        return coverage
    
    def _generate_validation_report(self, 
                                  audit_context: AuditContext,
                                  requirement_analysis: Dict[str, Any],
                                  quality_assessment: Dict[str, Any],
                                  coverage_analysis: Dict[str, bool]) -> ValidationReport:
        """
        Generate comprehensive validation report.
        
        Args:
            audit_context: Audit context
            requirement_analysis: Requirements analysis results
            quality_assessment: Quality assessment results
            coverage_analysis: Coverage analysis results
            
        Returns:
            Validation report
        """
        # Determine overall result
        overall_result = self._determine_overall_result(
            requirement_analysis,
            quality_assessment,
            coverage_analysis
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            requirement_analysis,
            quality_assessment,
            coverage_analysis
        )
        
        # Collect all issues
        issues = []
        
        # Add requirement analysis issues
        for issue_data in requirement_analysis.get('issues', []):
            issues.append(ValidationIssue(
                severity=ValidationSeverity(issue_data.get('severity', 'medium')),
                category=issue_data.get('category', 'general'),
                description=issue_data.get('description', ''),
                suggestion=issue_data.get('suggestion', '')
            ))
        
        # Add quality issues
        for issue_data in quality_assessment.get('quality_issues', []):
            issues.append(ValidationIssue(
                severity=ValidationSeverity(issue_data.get('severity', 'medium')),
                category='quality',
                description=issue_data.get('description', ''),
                suggestion=issue_data.get('suggestion', '')
            ))
        
        # Collect recommendations
        recommendations = []
        recommendations.extend(requirement_analysis.get('recommendations', []))
        recommendations.extend(quality_assessment.get('quality_recommendations', []))
        
        # Create report
        report = ValidationReport(
            task_id=audit_context.task_id,
            task_description=audit_context.task_description,
            solution_summary=audit_context.solution_data.get('summary', ''),
            overall_result=overall_result,
            confidence_score=confidence_score,
            validation_timestamp=datetime.now(),
            issues=issues,
            requirements_coverage=coverage_analysis,
            recommendations=recommendations,
            metadata={
                'auditor_version': '1.0',
                'validation_model': self.validation_model,
                'requirement_count': len(audit_context.requirements),
                'analysis_data': {
                    'requirement_analysis': requirement_analysis,
                    'quality_assessment': quality_assessment
                },
                'stage_overrides': self._stage_run_meta
            }
        )
        
        return report
    
    def _determine_overall_result(self, 
                                requirement_analysis: Dict[str, Any],
                                quality_assessment: Dict[str, Any],
                                coverage_analysis: Dict[str, bool]) -> ValidationResult:
        """Determine overall validation result."""
        # Check requirement analysis result
        req_result = requirement_analysis.get('overall_assessment', 'error')
        
        # Check coverage percentage
        total_requirements = len(coverage_analysis)
        covered_requirements = sum(coverage_analysis.values())
        coverage_percentage = covered_requirements / total_requirements if total_requirements > 0 else 0
        
        # Check for critical issues
        critical_issues = any(
            issue.get('severity') == 'critical' 
            for issue in requirement_analysis.get('issues', [])
        )
        
        # Determine result
        if critical_issues:
            return ValidationResult.FAIL
        elif req_result == 'fail':
            return ValidationResult.FAIL
        elif req_result == 'pass' and coverage_percentage >= 0.9:
            return ValidationResult.PASS
        elif req_result == 'partial' or coverage_percentage >= 0.7:
            return ValidationResult.PARTIAL
        elif req_result == 'needs_review':
            return ValidationResult.NEEDS_REVIEW
        else:
            return ValidationResult.FAIL
    
    def _calculate_confidence_score(self, 
                                  requirement_analysis: Dict[str, Any],
                                  quality_assessment: Dict[str, Any],
                                  coverage_analysis: Dict[str, bool]) -> float:
        """Calculate overall confidence score."""
        # Base confidence from requirement analysis
        base_confidence = requirement_analysis.get('confidence_score', 0.5)
        
        # Coverage factor
        coverage_percentage = sum(coverage_analysis.values()) / len(coverage_analysis) if coverage_analysis else 0
        coverage_factor = coverage_percentage
        
        # Quality factor
        quality_score = quality_assessment.get('quality_score', 0.5)
        
        # Weighted average
        confidence = (base_confidence * 0.5) + (coverage_factor * 0.3) + (quality_score * 0.2)
        
        return min(max(confidence, 0.0), 1.0)
    
    def _create_error_report(self, audit_context: AuditContext, error_message: str) -> ValidationReport:
        """Create error validation report."""
        return ValidationReport(
            task_id=audit_context.task_id,
            task_description=audit_context.task_description,
            solution_summary="Error during validation",
            overall_result=ValidationResult.ERROR,
            confidence_score=0.0,
            validation_timestamp=datetime.now(),
            issues=[ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category='system',
                description=f"Validation error: {error_message}",
                suggestion="Review audit configuration and try again"
            )],
            requirements_coverage={},
            recommendations=["Fix validation system error"],
            metadata={'error': error_message}
        )
    
    def _parse_fallback_response(self, response: str) -> Dict[str, Any]:
        """Parse response when JSON parsing fails."""
        # Simple fallback parsing
        result = {
            'overall_assessment': 'needs_review',
            'confidence_score': 0.5,
            'requirements_coverage': {},
            'issues': [],
            'recommendations': [],
            'reasoning': response
        }
        
        # Try to extract some information
        response_lower = response.lower()
        if 'pass' in response_lower and 'fail' not in response_lower:
            result['overall_assessment'] = 'pass'
            result['confidence_score'] = 0.7
        elif 'fail' in response_lower:
            result['overall_assessment'] = 'fail'
            result['confidence_score'] = 0.3
        
        return result
    
    def _extract_quality_metrics(self, response: str) -> Dict[str, Any]:
        """Extract quality metrics from response."""
        # Simple extraction logic
        quality_score = 0.5
        
        response_lower = response.lower()
        if 'excellent' in response_lower or 'high quality' in response_lower:
            quality_score = 0.9
        elif 'good' in response_lower:
            quality_score = 0.7
        elif 'poor' in response_lower or 'low quality' in response_lower:
            quality_score = 0.3
        
        return {
            'quality_score': quality_score,
            'quality_issues': [],
            'quality_recommendations': []
        }
    
    async def temporal_preemptive_rag_optimization(
        self,
        original_torch: Torch,
        campers: List[Camper],
        valley_at_hash: Optional[str] = None
    ) -> Torch:
        """
        Orchestrate a temporal preemptive RAG optimization flow:
        1) Receive task, select team (provided campers list)
        2) Provide initial auditor RAG system prompt context to team
        3) Have campers re-evaluate/re-tune their RAG context for the task
        4) Present task again to campers and collect solutions
        5) Summarize consensus and store artifacts
        6) Craft outbound message to original sender with valley/camper addressing
        
        Returns a final Torch containing the consensus summary and metadata.
        """
        try:
            task_desc = original_torch.claim if isinstance(original_torch.claim, str) else str(original_torch.claim)
            task_id = getattr(original_torch, 'torch_id', f"torch_{int(datetime.now().timestamp())}")
            # Build a minimal audit context for RAG preparation
            audit_ctx = AuditContext(
                task_id=task_id,
                task_description=task_desc,
                requirements=[],
                solution_data={},
                execution_context=original_torch.metadata or {}
            )
            rag_context = await self._prepare_rag_context(audit_ctx)

            # Team selection: use provided campers (exclude any that appear to be auditors)
            team: List[Camper] = [
                c for c in campers
                if 'auditor' not in getattr(c, 'name', '').lower() and 'auditor' not in getattr(c, '_role', '').lower()
            ]

            # Snapshot original system prompts to restore later
            original_prompts: Dict[int, Optional[str]] = {}
            for c in team:
                try:
                    original_prompts[id(c)] = c.get_system_prompt() if hasattr(c, 'get_system_prompt') else None
                    # Compose a tuned prompt combining global auditor context and task
                    tuned_prompt_parts: List[str] = []
                    if self._global_system_prompt:
                        tuned_prompt_parts.append(self._global_system_prompt)
                    tuned_prompt_parts.append(f"Task: {task_desc}")
                    tuned_prompt_parts.append(f"Role: {getattr(c, '_role', 'general')}")
                    tuned_prompt_parts.append("Guidance: Use evidence from context, align to requirements, and produce actionable outputs.")
                    tuned_prompt_parts.append(f"Auditor RAG Context:\n{rag_context}")
                    tuned_prompt = "\n\n".join([p for p in tuned_prompt_parts if p])
                    if hasattr(c, 'set_system_prompt'):
                        c.set_system_prompt(tuned_prompt)
                except Exception as e:
                    logger.warning(f"Failed to tune camper {getattr(c, 'name', 'unknown')} system prompt: {e}")

            # Present the task to each camper and collect solutions
            camper_results: List[Torch] = []
            for c in team:
                try:
                    result = await c.process(original_torch)
                    if isinstance(result, list):
                        camper_results.extend([r for r in result if isinstance(r, Torch)])
                    elif isinstance(result, Torch):
                        camper_results.append(result)
                except Exception as e:
                    logger.warning(f"Camper {getattr(c, 'name', 'unknown')} failed to process task during optimization: {e}")

            # Summarize consensus across camper results
            claims: List[str] = []
            for t in camper_results:
                try:
                    claims.append(str(t.claim))
                except Exception:
                    continue
            consensus_summary = "\n\n".join([
                f"Consensus Summary for Task: {task_desc}",
                "--- Camper Outputs ---",
                *([f"- {c}" for c in claims] if claims else ["(no camper outputs)"])
            ])

            # Store artifacts in PartyBox
            artifact_refs: Dict[str, Any] = {}
            try:
                if self.party_box:
                    # Store consensus summary
                    summary_key = f"consensus_{task_id}_{int(datetime.now().timestamp())}"
                    summary_ref = await self.party_box.put(summary_key, consensus_summary)
                    artifact_refs['consensus_summary_ref'] = summary_ref
                    # Store raw camper outputs
                    raw_key = f"camper_outputs_{task_id}_{int(datetime.now().timestamp())}"
                    raw_ref = await self.party_box.put(raw_key, json.dumps([
                        {
                            'claim': str(t.claim),
                            'confidence': getattr(t, 'confidence', None),
                            'metadata': getattr(t, 'metadata', {})
                        } for t in camper_results
                    ], indent=2))
                    artifact_refs['camper_outputs_ref'] = raw_ref
            except Exception as e:
                logger.warning(f"Failed to store artifacts in PartyBox: {e}")

            # Restore original system prompts
            for c in team:
                try:
                    if id(c) in original_prompts and hasattr(c, 'set_system_prompt'):
                        c.set_system_prompt(original_prompts[id(c)])
                except Exception:
                    pass

            # Craft final outbound torch
            outbound_metadata: Dict[str, Any] = {
                'auditor_phase': 'final_summary',
                'temporal_preemptive_rag': True,
                'artifact_refs': artifact_refs,
                'camper_count': len(team),
                'campers': [getattr(c, 'name', f'camper_{i}') for i, c in enumerate(team)],
                'original_torch_id': task_id,
            }
            # Preserve addressing info from original torch
            if isinstance(original_torch.metadata, dict):
                for k in ['campfire_at_hash', 'camper_at_hash', 'sender_at_hash']:
                    if original_torch.metadata.get(k):
                        outbound_metadata[k] = original_torch.metadata.get(k)
            if valley_at_hash:
                outbound_metadata['valley_at_hash'] = valley_at_hash

            final_torch = Torch(
                claim=consensus_summary,
                path=None,
                confidence=0.9 if claims else 0.5,
                metadata=outbound_metadata
            )
            return final_torch
        except Exception as e:
            logger.error(f"Temporal preemptive RAG optimization failed: {e}")
            return Torch(
                claim=f"Auditor optimization failed: {e}",
                path=None,
                confidence=0.2,
                metadata={'error': True, 'auditor_phase': 'failed', 'original_torch_id': getattr(original_torch, 'torch_id', 'unknown')}
            )

    def get_validation_summary(self, report: ValidationReport) -> str:
        """
        Get a human-readable summary of the validation report.
        
        Args:
            report: Validation report
            
        Returns:
            Summary string
        """
        summary_parts = [
            f"Task: {report.task_description}",
            f"Result: {report.overall_result.value.upper()}",
            f"Confidence: {report.confidence_score:.2f}",
            f"Requirements Coverage: {sum(report.requirements_coverage.values())}/{len(report.requirements_coverage)}"
        ]
        
        if report.issues:
            critical_issues = [i for i in report.issues if i.severity == ValidationSeverity.CRITICAL]
            high_issues = [i for i in report.issues if i.severity == ValidationSeverity.HIGH]
            
            if critical_issues:
                summary_parts.append(f"Critical Issues: {len(critical_issues)}")
            if high_issues:
                summary_parts.append(f"High Priority Issues: {len(high_issues)}")
        
        if report.recommendations:
            summary_parts.append(f"Recommendations: {len(report.recommendations)}")
        
        return " | ".join(summary_parts)


    async def experiential_simulation_rag_tuning(
        self,
        original_torch: Torch,
        campers: List[Camper],
        valley_at_hash: Optional[str] = None
    ) -> Torch:
        """
        Experiential simulation mode:
        - Ask targeted campers to imagine experiences in a scenario.
        - Update their psychological state and (optionally) system prompt with experiential context.
        - Have campers re-evaluate their RAG document and produce outputs.
        - Summarize the experiential insights and store artifacts.
        - Craft outbound torch preserving addressing and mode metadata.
        """
        try:
            scenario = None
            target_names = []
            if isinstance(original_torch.metadata, dict):
                scenario = original_torch.metadata.get('experiential_scenario') or original_torch.metadata.get('scenario')
                target_names = original_torch.metadata.get('target_camper_at_names', []) or []
            task_id = getattr(original_torch, 'torch_id', f"torch_{int(datetime.now().timestamp())}")
            task_desc = original_torch.claim if isinstance(original_torch.claim, str) else str(original_torch.claim)

            # Select target campers (by at_name if provided), else use all
            selected: List[Camper] = []
            if target_names:
                mention_set = set(target_names)
                for c in campers:
                    at_name = c.get_at_name() if hasattr(c, 'get_at_name') else getattr(c, 'at_name', None)
                    if at_name and at_name in mention_set:
                        selected.append(c)
            if not selected:
                selected = campers

            # Prepare experiential context string
            exp_context = scenario or f"Imagine experiential context relevant to: {task_desc}"

            # Save original prompts for restoration
            originals: Dict[int, Optional[str]] = {}
            for c in selected:
                try:
                    originals[id(c)] = c.get_system_prompt() if hasattr(c, 'get_system_prompt') else None
                except Exception:
                    originals[id(c)] = None

            # Apply experiential state and prompt augmentation
            augmented_prompt_suffix = f"\n\n[Experiential State]\nYou imagined: {exp_context}. Reflect this in your perspective and decision-making."
            for c in selected:
                try:
                    if hasattr(c, 'set_psychological_state'):
                        c.set_psychological_state(f"experiential:{exp_context}")
                    # Augment system prompt if available
                    base_sys = ""
                    try:
                        base_sys = c.get_system_prompt() or ""
                    except Exception:
                        base_sys = ""
                    new_sys = (base_sys or self._global_system_prompt or "") + augmented_prompt_suffix
                    if hasattr(c, 'set_system_prompt'):
                        c.set_system_prompt(new_sys)
                except Exception:
                    pass

            # Ask campers to process the task again under experiential context
            camper_outputs: List[Torch] = []
            for c in selected:
                try:
                    result = await c.process(original_torch)
                    if result:
                        camper_outputs.extend(result if isinstance(result, list) else [result])
                except Exception as e:
                    logger.warning(f"Camper {getattr(c, 'name', 'unknown')} failed experiential processing: {e}")

            # Summarize experiential insights
            claims = [str(t.claim) for t in camper_outputs if getattr(t, 'claim', None)]
            consensus = "\n\n".join([f"- {cl}" for cl in claims]) or "No experiential outputs produced."
            summary = f"Experiential Insights Summary for {task_id}:\n{consensus}"

            # Store artifacts
            artifact_refs: Dict[str, Any] = {}
            try:
                if self.party_box:
                    sum_key = f"experiential_summary_{task_id}_{int(datetime.now().timestamp())}"
                    artifact_refs['experiential_summary_ref'] = await self.party_box.put(sum_key, summary.encode('utf-8'))
                    raw_key = f"experiential_camper_outputs_{task_id}_{int(datetime.now().timestamp())}"
                    artifact_refs['experiential_camper_outputs_ref'] = await self.party_box.put(
                        raw_key,
                        json.dumps([
                            {
                                'claim': str(t.claim),
                                'confidence': getattr(t, 'confidence', None),
                                'metadata': getattr(t, 'metadata', {})
                            } for t in camper_outputs
                        ], indent=2).encode('utf-8')
                    )
            except Exception as e:
                logger.warning(f"Failed to store experiential artifacts: {e}")

            # Restore original prompts
            for c in selected:
                try:
                    if id(c) in originals and hasattr(c, 'set_system_prompt'):
                        c.set_system_prompt(originals[id(c)] or "")
                except Exception:
                    pass

            # Craft final torch
            outbound_meta: Dict[str, Any] = {
                'auditor_phase': 'experiential_summary',
                'auditor_mode': 'experiential',
                'experiential_context': exp_context,
                'artifact_refs': artifact_refs,
                'camper_count': len(selected),
                'campers': [getattr(c, 'name', f'camper_{i}') for i, c in enumerate(selected)],
                'original_torch_id': task_id,
            }
            if isinstance(original_torch.metadata, dict):
                for k in ['campfire_at_hash', 'camper_at_hash', 'sender_at_hash']:
                    if original_torch.metadata.get(k):
                        outbound_meta[k] = original_torch.metadata.get(k)
            if valley_at_hash:
                outbound_meta['valley_at_hash'] = valley_at_hash

            final = Torch(
                claim=summary,
                path=None,
                confidence=0.85 if claims else 0.5,
                metadata=outbound_meta,
                source_campfire=getattr(original_torch, 'source_campfire', 'auditor'),
                channel=getattr(original_torch, 'channel', 'system')
            )
            return final
        except Exception as e:
            logger.error(f"Experiential simulation RAG tuning failed: {e}")
            return Torch(
                claim=f"Auditor experiential mode failed: {e}",
                path=None,
                confidence=0.2,
                metadata={
                    'error': True,
                    'auditor_phase': 'failed',
                    'auditor_mode': 'experiential',
                    'original_torch_id': getattr(original_torch, 'torch_id', 'unknown')
                },
                source_campfire=getattr(original_torch, 'source_campfire', 'auditor'),
                channel=getattr(original_torch, 'channel', 'system')
            )

            return Torch(
            claim=f"Auditor experiential mode failed: {e}",
            path=None,
            confidence=0.2,
            metadata={'error': True, 'auditor_phase': 'failed', 'auditor_mode': 'experiential', 'original_torch_id': getattr(original_torch, 'torch_id', 'unknown')},
            source_campfire=getattr(original_torch, 'source_campfire', 'auditor'),
            channel=getattr(original_torch, 'channel', 'system')
            )