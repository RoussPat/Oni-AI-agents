"""
Example usage of the ONI AI Agents system.
"""

import asyncio
import logging
from src.oni_ai_agents.core.agent import Agent, AgentMessage
from src.oni_ai_agents.core.agent_types import AgentType


class ObservingAgent(Agent):
    """Example observing agent that monitors game state."""
    
    async def process_input(self, input_data):
        """Process game state input and generate observations."""
        if self.model:
            prompt = f"Analyze this game state and provide observations: {input_data}"
            response = await self.model.generate_response(prompt)
            return {"observations": response, "raw_data": input_data}
        else:
            return {"observations": "No model available", "raw_data": input_data}
    
    async def _on_start(self):
        self.logger.info("Observing agent started - ready to monitor game state")
    
    async def _on_stop(self):
        self.logger.info("Observing agent stopped")
    
    async def _process_message(self, message: AgentMessage):
        """Process incoming messages."""
        if message.message_type == "request_observation":
            # Generate observation and send back
            observation = await self.process_input(message.content.get("game_state", {}))
            await self.send_message(
                message.sender_id,
                "observation_result",
                observation
            )


class CoreAgent(Agent):
    """Example core agent that makes decisions."""
    
    async def process_input(self, input_data):
        """Process observations and make decisions."""
        if self.model:
            prompt = f"Based on these observations, what should we do? {input_data}"
            response = await self.model.generate_response(prompt)
            return {"decision": response, "reasoning": input_data}
        else:
            return {"decision": "No model available", "reasoning": input_data}
    
    async def _on_start(self):
        self.logger.info("Core agent started - ready to make decisions")
    
    async def _on_stop(self):
        self.logger.info("Core agent stopped")
    
    async def _process_message(self, message: AgentMessage):
        """Process incoming messages."""
        if message.message_type == "observation_result":
            # Process observation and make decision
            decision = await self.process_input(message.content)
            await self.send_message(
                message.sender_id,
                "decision_result",
                decision
            )


async def main():
    """Main example function."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create agents
    observing_agent = ObservingAgent(
        agent_id="observer_1",
        agent_type=AgentType.OBSERVING,
        model_provider="local",
        model_config={"delay": 0.1}
    )
    
    core_agent = CoreAgent(
        agent_id="core_1",
        agent_type=AgentType.CORE,
        model_provider="local",
        model_config={"delay": 0.1}
    )
    
    # Connect agents
    observing_agent.connect_to_agent(core_agent)
    
    # Start agents
    await observing_agent.start()
    await core_agent.start()
    
    # Simulate game state
    game_state = {
        "resources": {"food": 100, "oxygen": 85, "power": 60},
        "duplicants": {"count": 8, "health": "good"},
        "threats": ["heat", "disease"]
    }
    
    print("🤖 ONI AI Agents System Demo")
    print("=" * 40)
    
    # Request observation
    print(f"\n📊 Requesting observation for game state...")
    await observing_agent.send_message(
        "core_1",
        "request_observation",
        {"game_state": game_state}
    )
    
    # Wait a bit for processing
    await asyncio.sleep(0.5)
    
    # Check agent statuses
    print(f"\n📈 Agent Status:")
    print(f"Observer: {observing_agent.get_status()}")
    print(f"Core: {core_agent.get_status()}")
    
    # Stop agents
    await observing_agent.stop()
    await core_agent.stop()
    
    print(f"\n✅ Demo completed!")


if __name__ == "__main__":
    asyncio.run(main()) 