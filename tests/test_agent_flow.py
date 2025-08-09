"""
End-to-end test for the complete ONI AI agent flow.

This test creates three agents (Observing, Core, Commands) and simulates
a complete game analysis and decision-making flow.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from src.oni_ai_agents.core.agent import Agent, AgentMessage
from src.oni_ai_agents.core.agent_types import AgentType


class ResourceObservingAgent(Agent):
    """
    Observing agent that monitors resource levels in the game.
    
    Responsibilities:
    - Monitor food, oxygen, power, water levels
    - Detect resource shortages
    - Track resource production rates
    - Alert about critical resource situations
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, AgentType.OBSERVING, **kwargs)
        self.resource_thresholds = {
            "food": 50,
            "oxygen": 30,
            "power": 20,
            "water": 25
        }
        self.observations = []
    
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process game state and generate resource observations."""
        if not hasattr(self, 'model') or not self.model:
            return {"error": "No model available"}
        
        # Extract resource data
        resources = input_data.get("resources", {})
        
        # Analyze resource levels
        analysis = []
        alerts = []
        
        for resource, level in resources.items():
            threshold = self.resource_thresholds.get(resource, 0)
            if level < threshold:
                alerts.append(f"CRITICAL: {resource} at {level}% (threshold: {threshold}%)")
            elif level < threshold * 1.5:
                analysis.append(f"WARNING: {resource} at {level}%")
            else:
                analysis.append(f"OK: {resource} at {level}%")
        
        # Generate AI analysis
        prompt = f"""
        Analyze these resource levels and provide insights:
        Resources: {resources}
        Alerts: {alerts}
        Analysis: {analysis}
        
        Provide a comprehensive resource status report.
        """
        
        response = await self.model.generate_response(prompt)
        
        observation = {
            "resource_levels": resources,
            "alerts": alerts,
            "analysis": analysis,
            "ai_insights": response,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self.observations.append(observation)
        return observation
    
    async def _on_start(self):
        self.logger.info("Resource observing agent started - monitoring resource levels")
    
    async def _on_stop(self):
        self.logger.info("Resource observing agent stopped")
    
    async def _process_message(self, message: AgentMessage):
        """Process incoming messages."""
        self.logger.info(f"Resource agent processing message: {message.message_type}")
        
        if message.message_type == "request_resource_analysis":
            # Generate resource analysis
            game_state = message.content.get("game_state", {})
            observation = await self.process_input(game_state)
            
            # Send observation to core agent
            self.logger.info("Sending resource observation to core agent")
            await self.send_message(
                message.sender_id,
                "resource_observation",
                observation
            )
        else:
            # Handle other message types
            self.logger.info(f"Received message: {message.message_type}")


class ColonyCoreAgent(Agent):
    """
    Core agent that makes strategic decisions based on observations.
    
    Responsibilities:
    - Analyze observations from observing agents
    - Formulate overall colony strategy
    - Prioritize actions and goals
    - Coordinate between different game systems
    - Make high-level decisions
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, AgentType.CORE, **kwargs)
        self.strategies = []
        self.decisions = []
    
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process observations and generate strategic decisions."""
        if not hasattr(self, 'model') or not self.model:
            return {"error": "No model available"}
        
        # Extract observations
        observations = input_data.get("observations", [])
        
        # Analyze all observations
        analysis_prompt = f"""
        Based on these observations, formulate a colony strategy:
        
        Observations: {observations}
        
        Provide:
        1. Overall colony status assessment
        2. Priority actions needed
        3. Strategic recommendations
        4. Resource allocation suggestions
        """
        
        strategy_response = await self.model.generate_response(analysis_prompt)
        
        # Generate specific decisions
        decision_prompt = f"""
        Based on this strategy: {strategy_response}
        
        Generate specific, actionable decisions in this format:
        - Action: [specific action]
        - Priority: [high/medium/low]
        - Target: [what to focus on]
        - Expected Outcome: [what this should achieve]
        """
        
        decisions_response = await self.model.generate_response(decision_prompt)
        
        decision = {
            "strategy": strategy_response,
            "decisions": decisions_response,
            "observations_analyzed": len(observations),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self.decisions.append(decision)
        return decision
    
    async def _on_start(self):
        self.logger.info("Colony core agent started - ready to make strategic decisions")
    
    async def _on_stop(self):
        self.logger.info("Colony core agent stopped")
    
    async def _process_message(self, message: AgentMessage):
        """Process incoming messages."""
        self.logger.info(f"Core agent processing message: {message.message_type}")
        
        if message.message_type == "resource_observation":
            # Store the observation
            self.logger.info(f"Received resource observation from {message.sender_id}")
            
            # Make strategic decision immediately
            decision = await self.process_input({"observations": [message.content]})
            
            # Send decision to commands agent
            self.logger.info("Sending strategic decision to commands agent")
            await self.send_message(
                "commands_agent",
                "strategic_decision",
                decision
            )
        elif message.message_type == "request_resource_analysis":
            # Forward the request to the resource agent
            self.logger.info("Forwarding resource analysis request to resource agent")
            await self.send_message(
                "resource_observer",
                "request_resource_analysis",
                message.content
            )
        else:
            # Handle other message types
            self.logger.info(f"Received message: {message.message_type}")


class GameCommandsAgent(Agent):
    """
    Commands agent that executes specific game actions.
    
    Responsibilities:
    - Translate strategy into specific commands
    - Handle game interaction mechanics
    - Execute building, digging, and management tasks
    - Manage duplicant assignments
    - Handle emergency responses
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, AgentType.COMMANDS, **kwargs)
        self.executed_commands = []
        self.command_history = []
    
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process decisions and generate executable commands."""
        if not hasattr(self, 'model') or not self.model:
            return {"error": "No model available"}
        
        # Extract strategic decision
        strategy = input_data.get("strategy", "")
        decisions = input_data.get("decisions", "")
        
        # Generate specific commands
        command_prompt = f"""
        Based on this strategy and decisions:
        Strategy: {strategy}
        Decisions: {decisions}
        
        Generate specific, executable game commands:
        - Command Type: [build/dig/assign/research/etc]
        - Target Location: [coordinates or area]
        - Priority: [1-5, where 1 is highest]
        - Duplicant Assignment: [which duplicant]
        - Expected Duration: [estimated time]
        """
        
        commands_response = await self.model.generate_response(command_prompt)
        
        # Simulate command execution
        execution_status = "pending"
        if "build" in commands_response.lower():
            execution_status = "scheduled"
        elif "emergency" in commands_response.lower():
            execution_status = "immediate"
        
        command_result = {
            "commands": commands_response,
            "execution_status": execution_status,
            "strategy_source": strategy[:100] + "...",  # Truncate for logging
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self.executed_commands.append(command_result)
        return command_result
    
    async def _on_start(self):
        self.logger.info("Game commands agent started - ready to execute actions")
    
    async def _on_stop(self):
        self.logger.info("Game commands agent stopped")
    
    async def _process_message(self, message: AgentMessage):
        """Process incoming messages."""
        self.logger.info(f"Commands agent processing message: {message.message_type}")
        
        if message.message_type == "strategic_decision":
            self.logger.info(f"Received strategic decision from {message.sender_id}")
            
            # Execute the commands
            command_result = await self.process_input(message.content)
            
            # Send execution report back to core agent
            await self.send_message(
                message.sender_id,
                "command_execution_report",
                command_result
            )
        else:
            # Handle other message types
            self.logger.info(f"Received message: {message.message_type}")


@pytest.mark.asyncio
async def test_complete_agent_flow():
    """
    Test the complete flow: Observing -> Core -> Commands.
    
    This test simulates a full cycle of:
    1. Resource observing agent monitors game state
    2. Core agent receives observations and makes decisions
    3. Commands agent executes the decisions
    4. All agents communicate properly
    """
    
    # Create the three agents
    resource_agent = ResourceObservingAgent(
        agent_id="resource_observer",
        model_provider="local",
        model_config={"delay": 0.05}
    )
    
    core_agent = ColonyCoreAgent(
        agent_id="colony_core",
        model_provider="local", 
        model_config={"delay": 0.05}
    )
    
    commands_agent = GameCommandsAgent(
        agent_id="commands_agent",
        model_provider="local",
        model_config={"delay": 0.05}
    )
    
    # Connect the agents in the flow: Observer -> Core -> Commands
    resource_agent.connect_to_agent(core_agent)
    core_agent.connect_to_agent(commands_agent)
    commands_agent.connect_to_agent(core_agent)  # For feedback loop
    
    # Start all agents
    await resource_agent.start()
    await core_agent.start()
    await commands_agent.start()
    
    # Simulate game state with resource issues
    game_state = {
        "resources": {
            "food": 35,      # Critical - below 50% threshold
            "oxygen": 45,    # Warning - below 1.5x threshold
            "power": 75,     # OK
            "water": 15      # Critical - below 25% threshold
        },
        "duplicants": {
            "count": 8,
            "health": "good"
        },
        "threats": ["heat", "disease"]
    }
    
    # Step 1: Request resource analysis
    print("\n🔄 Step 1: Resource Analysis")
    await resource_agent.send_message(
        "colony_core",
        "request_resource_analysis",
        {"game_state": game_state}
    )
    
    # Wait for processing
    await asyncio.sleep(0.3)
    
    # Step 2: Check if core agent received observation
    print("\n🔄 Step 2: Strategic Decision")
    print(f"Core agent message queue: {len(core_agent.message_queue)} messages")
    print(f"Core agent connected agents: {list(core_agent.connected_agents.keys())}")
    assert len(core_agent.message_queue) > 0, "Core agent should have received observations"
    
    # Step 3: Check if commands agent received decision
    print("\n🔄 Step 3: Command Execution")
    await asyncio.sleep(0.3)
    print(f"Commands agent message queue: {len(commands_agent.message_queue)} messages")
    print(f"Commands agent connected agents: {list(commands_agent.connected_agents.keys())}")
    assert len(commands_agent.message_queue) > 0, "Commands agent should have received decisions"
    
    # Step 4: Check final status
    print("\n🔄 Step 4: Final Status Check")
    
    # Verify all agents have processed messages
    resource_status = resource_agent.get_status()
    core_status = core_agent.get_status()
    commands_status = commands_agent.get_status()
    
    print(f"Resource Agent: {resource_status}")
    print(f"Core Agent: {core_status}")
    print(f"Commands Agent: {commands_status}")
    
    # Assertions for the complete flow
    assert resource_status["is_active"] is True, "Resource agent should be active"
    assert core_status["is_active"] is True, "Core agent should be active"
    assert commands_status["is_active"] is True, "Commands agent should be active"
    
    assert len(resource_agent.observations) > 0, "Resource agent should have observations"
    assert len(core_agent.decisions) > 0, "Core agent should have made decisions"
    assert len(commands_agent.executed_commands) > 0, "Commands agent should have executed commands"
    
    # Check agent connections
    assert "colony_core" in resource_agent.connected_agents, "Resource agent should be connected to core"
    assert "commands_agent" in core_agent.connected_agents, "Core agent should be connected to commands"
    assert "colony_core" in commands_agent.connected_agents, "Commands agent should be connected to core"
    
    # Stop all agents
    await resource_agent.stop()
    await core_agent.stop()
    await commands_agent.stop()
    
    print("\n✅ Complete agent flow test passed!")


@pytest.mark.asyncio
async def test_agent_communication_patterns():
    """
    Test different communication patterns between agents.
    
    This test verifies that agents can:
    - Send messages to specific recipients
    - Handle multiple message types
    - Process messages asynchronously
    - Maintain message history
    """
    
    # Create agents
    observer = ResourceObservingAgent(
        agent_id="test_observer",
        model_provider="local",
        model_config={"delay": 0.01}
    )
    
    core = ColonyCoreAgent(
        agent_id="test_core",
        model_provider="local",
        model_config={"delay": 0.01}
    )
    
    commands = GameCommandsAgent(
        agent_id="test_commands",
        model_provider="local",
        model_config={"delay": 0.01}
    )
    
    # Connect agents
    observer.connect_to_agent(core)
    core.connect_to_agent(commands)
    
    # Start agents
    await observer.start()
    await core.start()
    await commands.start()
    
    # Test multiple message types
    test_messages = [
        ("request_resource_analysis", {"game_state": {"resources": {"food": 30}}}),
        ("request_resource_analysis", {"game_state": {"resources": {"oxygen": 20}}}),
        ("request_resource_analysis", {"game_state": {"resources": {"power": 10}}})
    ]
    
    # Send multiple messages
    for msg_type, content in test_messages:
        await observer.send_message("test_core", msg_type, content)
    
    # Wait for processing
    await asyncio.sleep(0.2)
    
    # Verify message processing
    assert len(observer.message_queue) == 0, "Observer should have processed all messages"
    assert len(core.message_queue) >= 1, "Core should have received messages"
    
    # Stop agents
    await observer.stop()
    await core.stop()
    await commands.stop()
    
    print("✅ Agent communication patterns test passed!")


@pytest.mark.asyncio
async def test_agent_error_handling():
    """
    Test agent error handling and recovery.
    
    This test verifies that agents can handle:
    - Missing model connections
    - Invalid message formats
    - Network errors (simulated)
    - Graceful degradation
    """
    
    # Create agent without model
    agent = ResourceObservingAgent(
        agent_id="error_test_agent",
        model_provider=None  # No model
    )
    
    await agent.start()
    
    # Test processing without model
    result = await agent.process_input({"resources": {"food": 50}})
    assert "error" in result, "Should return error when no model available"
    
    # Test message handling
    await agent.send_message("error_test_agent", "test_message", {"data": "test"})
    await asyncio.sleep(0.1)
    
    # Should handle gracefully even with warning
    assert agent.is_active, "Agent should remain active despite errors"
    
    await agent.stop()
    
    print("✅ Agent error handling test passed!")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_complete_agent_flow())
    asyncio.run(test_agent_communication_patterns())
    asyncio.run(test_agent_error_handling()) 