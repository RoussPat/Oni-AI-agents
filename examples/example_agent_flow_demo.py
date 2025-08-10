"""
Demo script for the complete agent flow test.

This script runs the end-to-end agent flow test and shows
the communication between all three agent types.
"""

import asyncio
import logging

# This demo depends on a separate test module that might not exist in every environment.
# Provide built-in fallbacks if unavailable so the demo remains runnable offline.
try:
    from tests.test_agent_flow import (
        ResourceObservingAgent as _ResourceObservingAgent,
        ColonyCoreAgent as _ColonyCoreAgent,
        GameCommandsAgent as _GameCommandsAgent,
    )
except Exception:  # pragma: no cover - demo-only fallback
    _ResourceObservingAgent = None
    _ColonyCoreAgent = None
    _GameCommandsAgent = None

from src.oni_ai_agents.core.agent import Agent, AgentMessage
from src.oni_ai_agents.core.agent_types import AgentType


class _FallbackResourceObservingAgent(Agent):
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, AgentType.OBSERVING, **kwargs)
        self.resource_thresholds = {"food": 50, "oxygen": 30, "power": 20, "water": 25}
        self.observations = []

    async def _on_start(self) -> None:
        self.logger.info("Fallback Resource agent started")

    async def _on_stop(self) -> None:
        self.logger.info("Fallback Resource agent stopped")

    async def process_input(self, input_data):
        resources = input_data.get("resources", {})
        analysis, alerts = [], []
        for res, lvl in resources.items():
            thr = self.resource_thresholds.get(res, 0)
            if lvl < thr:
                alerts.append(f"CRITICAL: {res} at {lvl}% (threshold: {thr}%)")
            elif lvl < thr * 1.5:
                analysis.append(f"WARNING: {res} at {lvl}%")
            else:
                analysis.append(f"OK: {res} at {lvl}%")
        # Use model if available, otherwise mock
        text = (
            await self.model.generate_response(f"Analyze resources: {resources}")
            if self.model
            else "local-mock"
        )
        obs = {"resource_levels": resources, "alerts": alerts, "analysis": analysis, "ai_insights": text}
        self.observations.append(obs)
        return obs

    async def _process_message(self, message: AgentMessage):
        if message.message_type == "request_resource_analysis":
            obs = await self.process_input(message.content.get("game_state", {}))
            await self.send_message(message.sender_id, "resource_observation", obs)


class _FallbackColonyCoreAgent(Agent):
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, AgentType.CORE, **kwargs)
        self.decisions = []

    async def _on_start(self) -> None:
        self.logger.info("Fallback Core agent started")

    async def _on_stop(self) -> None:
        self.logger.info("Fallback Core agent stopped")

    async def process_input(self, input_data):
        observations = input_data.get("observations", [])
        strategy = (
            await self.model.generate_response(f"Make strategy from: {observations}")
            if self.model
            else "local-mock-strategy"
        )
        decision = {"strategy": strategy, "decisions": "Build farm, dig oxygen", "observations_analyzed": len(observations)}
        self.decisions.append(decision)
        return decision

    async def _process_message(self, message: AgentMessage):
        if message.message_type == "resource_observation":
            decision = await self.process_input({"observations": [message.content]})
            await self.send_message("commands_agent", "strategic_decision", decision)
        elif message.message_type == "request_resource_analysis":
            await self.send_message("resource_observer", "request_resource_analysis", message.content)


class _FallbackGameCommandsAgent(Agent):
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, AgentType.COMMANDS, **kwargs)
        self.executed_commands = []

    async def _on_start(self) -> None:
        self.logger.info("Fallback Commands agent started")

    async def _on_stop(self) -> None:
        self.logger.info("Fallback Commands agent stopped")

    async def process_input(self, input_data):
        cmds = (
            await self.model.generate_response("Generate commands") if self.model else "queue: build, dig"
        )
        out = {"commands": cmds, "execution_status": "queued"}
        self.executed_commands.append(out)
        return out

    async def _process_message(self, message: AgentMessage):
        if message.message_type == "strategic_decision":
            await self.process_input(message.content)


# Choose test-provided classes if present, otherwise fall back
ResourceObservingAgent = _ResourceObservingAgent or _FallbackResourceObservingAgent
ColonyCoreAgent = _ColonyCoreAgent or _FallbackColonyCoreAgent
GameCommandsAgent = _GameCommandsAgent or _FallbackGameCommandsAgent


async def run_agent_flow_demo():
    """Run a demonstration of the complete agent flow."""

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    print("🤖 ONI AI Agents - Complete Flow Demo")
    print("=" * 50)

    # Create the three agents
    print("\n📋 Creating agents...")
    resource_agent = ResourceObservingAgent(agent_id="resource_observer", model_provider="local", model_config={"delay": 0.05})
    core_agent = ColonyCoreAgent(agent_id="colony_core", model_provider="local", model_config={"delay": 0.05})
    commands_agent = GameCommandsAgent(agent_id="commands_agent", model_provider="local", model_config={"delay": 0.05})

    # Connect the agents
    print("🔗 Connecting agents...")
    resource_agent.connect_to_agent(core_agent)
    core_agent.connect_to_agent(commands_agent)
    commands_agent.connect_to_agent(core_agent)

    # Start all agents
    print("🚀 Starting agents...")
    await resource_agent.start()
    await core_agent.start()
    await commands_agent.start()

    # Simulate a critical game state
    print("\n🎮 Simulating game state...")
    game_state = {
        "resources": {"food": 25, "oxygen": 35, "power": 80, "water": 10},
        "duplicants": {"count": 8, "health": "good"},
        "threats": ["heat", "disease"],
    }
    print(f"Game State: {game_state}")

    # Step 1: Resource Analysis
    print("\n🔄 Step 1: Resource Analysis")
    await resource_agent.send_message("colony_core", "request_resource_analysis", {"game_state": game_state})
    await asyncio.sleep(0.3)

    # Step 2: Strategic Decision
    print("\n🔄 Step 2: Strategic Decision")
    await asyncio.sleep(0.3)

    # Step 3: Command Execution
    print("\n🔄 Step 3: Command Execution")
    await asyncio.sleep(0.3)

    # Final Status Report
    print("\n📈 Final Status Report")
    print("-" * 30)
    print(f"Resource observations: {len(getattr(resource_agent, 'observations', []))}")
    print(f"Strategic decisions: {len(getattr(core_agent, 'decisions', []))}")
    print(f"Commands executed: {len(getattr(commands_agent, 'executed_commands', []))}")

    # Stop all agents
    print("\n🛑 Stopping agents...")
    await resource_agent.stop()
    await core_agent.stop()
    await commands_agent.stop()

    print("\n✅ Agent flow demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_agent_flow_demo()) 