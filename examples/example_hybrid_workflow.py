#!/usr/bin/env python3
"""
Example Hybrid Workflow Usage

Demonstrates the complete pause-save-analyze-act workflow with specialized observer agents.
"""

import asyncio
import logging
from pathlib import Path

from src.oni_ai_agents.services.hybrid_workflow import HybridWorkflowManager
from src.oni_ai_agents.agents.resource_observer_agent import ResourceObserverAgent
from src.oni_ai_agents.agents.duplicant_observer_agent import DuplicantObserverAgent
from src.oni_ai_agents.agents.threat_observer_agent import ThreatObserverAgent
from src.oni_ai_agents.agents.image_observer_agent import ImageObserverAgent
from example_usage import CoreAgent  # Reuse the core agent from example

# New: Extractor for sectioned data from real saves
from src.oni_ai_agents.services.save_file_data_extractor import SaveFileDataExtractor


async def main():
    """Demonstrate the hybrid workflow system."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("🤖 ONI AI Hybrid Workflow Demo")
    print("=" * 50)
    
    workflow = HybridWorkflowManager()

    # Create specialized observer agents
    resource_observer = ResourceObserverAgent(
        agent_id="resource_observer",
        model_provider="local",
        model_config={"delay": 0.1}
    )
    duplicant_observer = DuplicantObserverAgent(
        agent_id="duplicant_observer",
        model_provider="local",
        model_config={"delay": 0.1}
    )
    threat_observer = ThreatObserverAgent(
        agent_id="threat_observer",
        model_provider="local",
        model_config={"delay": 0.1}
    )
    image_observer = ImageObserverAgent(
        agent_id="image_observer",
        model_provider="local",
        model_config={"delay": 0.1}
    )

    core_agent = CoreAgent(
        agent_id="hybrid_core",
        model_provider="local",
        model_config={"delay": 0.1}
    )

    # Start agents
    print("\n🚀 Starting agents...")
    agents = [resource_observer, duplicant_observer, threat_observer, image_observer, core_agent]
    for agent in agents:
        await agent.start()

    # Register with workflow
    workflow.register_observer_agent("resources", resource_observer)
    workflow.register_observer_agent("duplicants", duplicant_observer)
    workflow.register_observer_agent("threats", threat_observer)
    workflow.register_core_agent(core_agent)

    # Use real save
    real_save = Path("test_data/clone_laboratory.sav")
    if not real_save.exists():
        print("❌ Real save not found at test_data/clone_laboratory.sav")
        return

    # Extract section data and run agents manually for now
    extractor = SaveFileDataExtractor()
    sections = extractor.get_all_sections(real_save)

    print("\n📦 Extracted sections:")
    for k in sections.keys():
        print(f" - {k}")

    # Feed sections to each observer explicitly
    print("\n📊 Running observers on real save sections...")
    resource_result = await resource_observer.process_input({
        "save_file_path": str(real_save),
        "resource_data": sections.get("resources", {})
    })
    duplicant_result = await duplicant_observer.process_input({
        "save_file_path": str(real_save),
        "duplicant_data": sections.get("duplicants", {})
    })
    threat_result = await threat_observer.process_input({
        "save_file_path": str(real_save),
        "threat_data": sections.get("threats", {})
    })

    # Synthesize with core agent
    core_input = {
        "observer_results": {
            "resources": resource_result,
            "duplicants": duplicant_result,
            "threats": threat_result,
        },
        "save_file_path": str(real_save)
    }
    core_result = await core_agent.process_input(core_input)

    # Persist consolidated output
    out_dir = Path("test_data/hybrid_results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "summary.json"
    import json
    with open(out_file, "w") as f:
        json.dump({
            "resource": resource_result,
            "duplicant": duplicant_result,
            "threat": threat_result,
            "core": core_result,
        }, f, indent=2)

    print(f"\n💾 Hybrid results saved to: {out_file}")

    # Optional image analysis
    image_path = Path("test_data/clone_laboratory.png")
    if image_path.exists():
        img_result = await image_observer.process_input({
            "image_path": str(image_path),
            "analysis_type": "base_overview"
        })
        img_file = out_dir / "image_analysis.json"
        with open(img_file, "w") as f:
            json.dump(img_result, f, indent=2)
        print(f"🖼️  Image analysis saved to: {img_file}")

    # Stop agents
    print("\n🛑 Stopping agents...")
    for agent in agents:
        await agent.stop()

    print("✅ Hybrid workflow run complete")


if __name__ == "__main__":
    asyncio.run(main())
