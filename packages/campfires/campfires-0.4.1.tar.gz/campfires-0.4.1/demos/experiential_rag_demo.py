import asyncio
import os
import datetime
import aiofiles
import time
from pathlib import Path
from typing import List, Dict, Any

from campfires.core.camper import Camper
from campfires.core.campfire import Campfire
from campfires.core.torch import Torch
from campfires.party_box.local_driver import LocalDriver


class ExperientialCamper(Camper):
    """
    Lightweight camper for experiential demo.
    Uses system prompt, psychological state, and RAG document to craft a job-search plan.
    """
    def __init__(self, party_box: LocalDriver, config: Dict[str, Any]):
        super().__init__(party_box=party_box, config=config)

    async def override_prompt(self, raw_prompt: str, system_prompt: Any = None) -> Dict[str, Any]:
        # Stub implementation to satisfy abstract base. Not used in this demo.
        return {
            'claim': f"[{self.name}] override_prompt not used; see process() for experiential plan.",
            'confidence': 0.5,
            'metadata': {'method': 'override_prompt_stub'}
        }

    async def process(self, torch: Torch) -> List[Torch]:
        path_label = torch.metadata.get("experiential_path", "neutral")
        psych: Dict[str, Any] = self.get_psychological_state() or {}
        sys_prompt: str = self.get_system_prompt() or ""
        rag_path: str = self.get_rag_document_path() or ""

        rag_summary = ""
        try:
            if rag_path and Path(rag_path).exists():
                rag_text = Path(rag_path).read_text(encoding="utf-8")
                rag_summary = rag_text[:600]
        except Exception:
            rag_summary = "(unable to load RAG document)"

        # Compose a concise plan using current state
        plan_lines = [
            f"[Camper: {self.name}] Path: {path_label}",
            f"System Prompt: {sys_prompt[:120]}" if sys_prompt else "System Prompt: (default)",
            f"Psychological State: {psych}" if psych else "Psychological State: {}",
            "Baseline Persona (excerpt):",
            rag_summary if rag_summary else "(no persona baseline)",
            "\nAction Plan:",
            "- Morning: review 3 listings, tailor resume for 1 role",
            "- Afternoon: submit 1 application, reach out to 1 contact",
            "- Evening: journal 3 things done, prep micro-plan",
            "- Coping: breathing (2m), micro-walk (20m), message safe contact",
        ]

        result = Torch(
            claim="\n".join(plan_lines),
            confidence=0.85,
            metadata={
                "processed_by": self.name,
                "experiential_path": path_label,
                "persona_loaded": bool(rag_summary),
            },
            source_campfire="experiential_demo",
            channel="local",
        )
        return [result]


async def run_demo() -> None:
    # Setup Party Box local storage under demos
    party_box = LocalDriver(base_path=str(Path(__file__).parent / "party_box"))

    # Create campers representing different experiential branches
    campers: List[ExperientialCamper] = [
        ExperientialCamper(party_box, {"name": "Supportive_Path", "role": "audited_camper"}),
        ExperientialCamper(party_box, {"name": "Challenging_Path", "role": "audited_camper"}),
        ExperientialCamper(party_box, {"name": "Neutral_Path", "role": "audited_camper"}),
    ]

    # Attach baseline persona RAG document and psychological state
    rag_doc_path = str(Path(__file__).parent / "rag_examples" / "trauma_job_seeker.yaml")
    baseline_psych = {
        "energy": "medium",
        "stress": "medium",
        "optimism": "medium",
        "self_efficacy": "variable",
    }

    for c in campers:
        c.set_rag_document_path(rag_doc_path)
        c.set_psychological_state(dict(baseline_psych))
        c.set_system_prompt(
            "You are a supportive job-search coach. Emphasize step-by-step actions and emotional regulation."
        )

    # Create campfire with route-all-to-auditor enabled (default True)
    campfire = Campfire(
        name="ExperientialCampfire",
        campers=campers,
        party_box=party_box,
        config={
            "route_all_to_auditor": True,
        },
    )

    # Define experiential branches to explore
    branches = [
        {
            "label": "supportive",
            "description": "Quiet space, helpful friend feedback, small team leads",
            "psych_adjust": {"stress": "lower", "optimism": "higher"},
        },
        {
            "label": "challenging",
            "description": "Noisy environment, two rejections, pending landlord issues",
            "psych_adjust": {"stress": "higher", "optimism": "lower"},
        },
        {
            "label": "neutral",
            "description": "Average day, one application, no major events",
            "psych_adjust": {},
        },
    ]

    print("\n=== Experiential RAG Demo: Persona branches ===\n")
    for branch in branches:
        # Adjust each camper's psych state to reflect branch context
        for c in campers:
            current = c.get_psychological_state()
            if not isinstance(current, dict):
                current = {}
            adjusted = {**current, **branch.get("psych_adjust", {})}
            c.set_psychological_state(adjusted)

        # Create inbound torch requesting experiential mode
        inbound = Torch(
            claim=(
                "Simulate and tune prompts based on imagined experiences for job search while settling into a new home."
                f"\nBranch: {branch['label']} - {branch['description']}"
            ),
            confidence=0.7,
            metadata={
                "auditor_mode": "experiential",
                "experiential_path": branch["label"],
            },
            source_campfire="experiential_demo",
            channel="local",
        )

        # Process through campfire; auditor orchestrates experiential workflow
        results = await campfire.process_torch(inbound)

        print(f"\n--- Branch: {branch['label']} ---")
        if not results:
            print("No output from auditor.")
            continue

        final = results[0]
        print("Final Claim (consensus):")
        print(final.claim)
        print("\nMetadata:")
        print(final.metadata)

        # Generate per-branch HTML summary and store via Party Box
        # Create meaningful filename based on branch and timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        meaningful_filename = f"alex_job_search_{branch['label']}_experience_{timestamp}.html"

        # Analyze psychological impact and create narrative/outlook
        psych_impact = analyze_psychological_impact(branch, baseline_psych, final)
        narrative = create_experience_narrative(branch, psych_impact, final)
        mental_health_outlook = generate_mental_health_outlook(psych_impact, branch)

        # Construct the HTML content
        html_header = create_html_header(meaningful_filename)
        persona_badge = create_persona_badge(final.metadata.get("persona_loaded", False))
        final_claim_html = create_final_claim(final.claim, final.metadata)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{meaningful_filename}</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Roboto', sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 20px auto; padding: 0 15px; background-color: #f4f4f4; }}
        h1, h2, h3 {{ color: #0056b3; }}
        .container {{ background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section {{ margin-bottom: 25px; padding: 20px; background-color: #e9ecef; border-radius: 5px; }}
        .section-header {{ border-bottom: 2px solid #0056b3; padding-bottom: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }}
        .metadata-item {{ background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; padding: 8px 12px; margin-right: 10px; margin-bottom: 10px; display: inline-block; font-size: 0.9em; color: #0056b3; }}
        .impact-positive {{ color: #28a745; font-weight: bold; }}
        .impact-negative {{ color: #dc3545; font-weight: bold; }}
        .impact-neutral {{ color: #ffc107; font-weight: bold; }}
        .persona-badge {{ background-color: #6c757d; color: #fff; padding: 5px 10px; border-radius: 5px; font-size: 0.8em; margin-left: 10px; }}
        .footer {{ margin-top: 40px; font-size: 0.8em; text-align: center; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="section-header">
            <h1>Experience Report: {meaningful_filename}</h1>
            {persona_badge}
        </div>

        <div class="section">
            <h2>Narrative Storytelling</h2>
            {narrative}
        </div>

        <div class="section">
            <h2>Mental Health Outlook Summary</h2>
            {mental_health_outlook}
        </div>

        <div class="section">
            <h2>Final Claim & Metadata</h2>
            {final_claim_html}
        </div>
    </div>
    <div class="footer">
        Generated by Campfires Experiential RAG Demo on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
        """

        # Construct the full path for the HTML report in the 'other' subdirectory
        report_dir = Path(__file__).parent / "party_box" / "other"
        report_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        full_report_path = report_dir / meaningful_filename

        # Write the HTML content directly to the file
        async with aiofiles.open(full_report_path, 'wb') as f:
            await f.write(html.encode('utf-8'))

        # Update html_path and preview_url to use the meaningful filename
        html_path = str(full_report_path)
        relative_dir = "other" # Since we are explicitly saving to 'other'
        filename = meaningful_filename
        preview_url = f"http://localhost:8000/{relative_dir}/{filename}"
        print(f"📄 Experience Report: {meaningful_filename}")
        print(f"📁 Saved to: {html_path}")
        print(f"Preview URL: {preview_url}")


def analyze_psychological_impact(branch, baseline_psych, final_torch):
    """Analyze the psychological impact of the experiential branch."""
    psych_adjustments = branch.get("psych_adjust", {})
    
    impact = {
        "stress_change": "increased" if psych_adjustments.get("stress") == "higher" else 
                        "decreased" if psych_adjustments.get("stress") == "lower" else "stable",
        "optimism_change": "increased" if psych_adjustments.get("optimism") == "higher" else 
                          "decreased" if psych_adjustments.get("optimism") == "lower" else "stable",
        "overall_sentiment": "positive" if branch["label"] == "supportive" else 
                           "challenging" if branch["label"] == "challenging" else "neutral",
        "coping_mechanisms_used": ["breathing exercises", "micro-walks", "safe contact messaging"],
        "resilience_factors": []
    }
    
    # Determine resilience factors based on branch
    if branch["label"] == "supportive":
        impact["resilience_factors"] = ["supportive environment", "positive feedback", "manageable workload"]
    elif branch["label"] == "challenging":
        impact["resilience_factors"] = ["stress management skills", "trauma-informed coping", "persistence"]
    else:
        impact["resilience_factors"] = ["routine maintenance", "steady progress", "emotional regulation"]
    
    return impact


def create_experience_narrative(branch, psych_impact, final_torch):
    """Create a narrative story of the camper's experience."""
    branch_stories = {
        "supportive": """
        <p><strong>Alex started the day in a quiet, comfortable space.</strong> The environment felt safe and conducive to focused work. 
        A friend provided encouraging feedback on their resume, boosting confidence levels. The small team leads they researched 
        seemed approachable and aligned with their preference for supportive work environments.</p>
        
        <p><strong>Throughout the experience:</strong> Alex felt their stress levels <span class="impact-positive">decrease</span> 
        and optimism <span class="impact-positive">increase</span>. The supportive conditions allowed them to engage their 
        job search activities without triggering significant trauma responses. They were able to maintain focus and felt 
        genuinely hopeful about potential opportunities.</p>
        
        <p><strong>Key moments:</strong> The positive friend feedback served as a crucial validation point, reinforcing 
        Alex's self-efficacy. The quiet environment prevented overstimulation, allowing for clear thinking and planning.</p>
        """,
        
        "challenging": """
        <p><strong>Alex faced a difficult day with multiple stressors.</strong> The environment was noisy and distracting, 
        making concentration challenging. Two job rejections arrived, triggering feelings of inadequacy and self-doubt. 
        Additionally, pending issues with their landlord created housing insecurity anxiety.</p>
        
        <p><strong>Throughout the experience:</strong> Alex felt their stress levels <span class="impact-negative">increase</span> 
        and optimism <span class="impact-negative">decrease</span>. The challenging conditions activated trauma responses, 
        including hypervigilance and emotional dysregulation. However, they demonstrated resilience by implementing 
        learned coping strategies.</p>
        
        <p><strong>Key moments:</strong> The rejections initially felt overwhelming, but Alex recognized the trauma response 
        and engaged breathing exercises. The housing concerns added complexity, but they managed to compartmentalize and 
        focus on actionable job search steps.</p>
        """,
        
        "neutral": """
        <p><strong>Alex experienced a typical day with balanced conditions.</strong> The environment was neither particularly 
        supportive nor challenging - just an average day in their job search journey. They submitted one application and 
        had no major positive or negative events to process.</p>
        
        <p><strong>Throughout the experience:</strong> Alex maintained <span class="impact-neutral">stable</span> stress and 
        optimism levels. This represented a healthy baseline day where trauma responses remained manageable and they could 
        engage in consistent, sustainable job search activities.</p>
        
        <p><strong>Key moments:</strong> The steady progress felt reassuring. Alex was able to maintain their routine without 
        significant emotional peaks or valleys, demonstrating growing emotional regulation skills.</p>
        """
    }
    
    return branch_stories.get(branch["label"], "<p>Experience narrative not available.</p>")


def generate_mental_health_outlook(psych_impact, branch):
    """Generate a mental health outlook summary."""
    outlook_templates = {
        "supportive": """
        <p><strong>🌟 Overall Outlook: Positive and Encouraging</strong></p>
        <ul>
            <li><strong>Stress Management:</strong> <span class="impact-positive">Improved</span> - The supportive environment 
            allowed Alex to operate from a place of calm, reducing cortisol levels and enabling clearer decision-making.</li>
            <li><strong>Self-Efficacy:</strong> <span class="impact-positive">Enhanced</span> - Positive feedback reinforced 
            Alex's belief in their capabilities, crucial for someone with trauma history.</li>
            <li><strong>Trauma Response:</strong> <span class="impact-positive">Minimal activation</span> - The safe environment 
            prevented triggering of hypervigilance or emotional dysregulation.</li>
            <li><strong>Future Resilience:</strong> This experience builds confidence for handling future job search challenges 
            and reinforces the importance of seeking supportive environments.</li>
        </ul>
        <p><em>Recommendation: Continue seeking similar supportive conditions when possible, as they optimize Alex's 
        performance and well-being.</em></p>
        """,
        
        "challenging": """
        <p><strong>⚠️ Overall Outlook: Resilient but Requires Support</strong></p>
        <ul>
            <li><strong>Stress Management:</strong> <span class="impact-negative">Elevated</span> - Multiple stressors activated 
            trauma responses, but Alex demonstrated learned coping skills.</li>
            <li><strong>Self-Efficacy:</strong> <span class="impact-negative">Temporarily shaken</span> - Rejections triggered 
            self-doubt, but underlying resilience remained intact.</li>
            <li><strong>Trauma Response:</strong> <span class="impact-negative">Activated but managed</span> - Hypervigilance 
            and emotional dysregulation occurred but were addressed through coping strategies.</li>
            <li><strong>Future Resilience:</strong> This experience, while difficult, demonstrates Alex's growing ability to 
            navigate challenges while maintaining functionality.</li>
        </ul>
        <p><em>Recommendation: Prioritize self-care and trauma-informed support. Consider spacing out high-stress activities 
        and ensuring access to safe spaces for recovery.</em></p>
        """,
        
        "neutral": """
        <p><strong>🔄 Overall Outlook: Stable and Sustainable</strong></p>
        <ul>
            <li><strong>Stress Management:</strong> <span class="impact-neutral">Maintained</span> - Alex demonstrated ability 
            to maintain emotional equilibrium during routine activities.</li>
            <li><strong>Self-Efficacy:</strong> <span class="impact-neutral">Steady</span> - Consistent progress reinforced 
            Alex's sense of capability without overwhelming them.</li>
            <li><strong>Trauma Response:</strong> <span class="impact-neutral">Well-regulated</span> - No significant triggers 
            activated, allowing for smooth functioning.</li>
            <li><strong>Future Resilience:</strong> This represents a healthy baseline that Alex can build upon, showing 
            sustainable job search practices.</li>
        </ul>
        <p><em>Recommendation: This balanced approach appears sustainable long-term. Continue building on this foundation 
        while gradually introducing more challenging elements as confidence grows.</em></p>
        """
    }
    
    return outlook_templates.get(branch["label"], "<p>Mental health outlook analysis not available.</p>")


def create_html_header(title: str) -> str:
    return f"<h1>{title}</h1>"

def create_persona_badge(persona_loaded: bool) -> str:
    if persona_loaded:
        return "<span class=\"persona-badge\">Persona Loaded</span>"
    return "<span class=\"persona-badge\">No Persona</span>"

def create_final_claim(claim: str, metadata: Dict[str, Any]) -> str:
    metadata_badges = "".join([f"<span class=\"metadata-item\">{{k}}: {{v}}</span>" for k, v in metadata.items()])
    return f"<p>{{claim}}</p><div style=\"margin-top: 15px;\">{{metadata_badges}}</div>"


if __name__ == "__main__":
    asyncio.run(run_demo())