"""
Tests for the Agent class.
"""


import pytest

from src.oni_ai_agents.core.agent import Agent
from src.oni_ai_agents.core.agent_types import AgentType


class MockAgent(Agent):
    """Mock agent for testing."""
    
    async def process_input(self, input_data):
        return {"response": f"Processed: {input_data}"}
    
    async def _on_start(self):
        pass
    
    async def _on_stop(self):
        pass
    
    async def _process_message(self, message):
        pass


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initialization."""
    agent = MockAgent(
        agent_id="test_agent",
        agent_type=AgentType.OBSERVING,
        model_provider="local",
        model_config={"delay": 0.01}
    )
    
    assert agent.agent_id == "test_agent"
    assert agent.agent_type == AgentType.OBSERVING
    assert agent.model_provider == "local"
    assert not agent.is_active


@pytest.mark.asyncio
async def test_agent_start_stop():
    """Test agent start and stop functionality."""
    agent = MockAgent(
        agent_id="test_agent",
        agent_type=AgentType.OBSERVING
    )
    
    await agent.start()
    assert agent.is_active
    
    await agent.stop()
    assert not agent.is_active


@pytest.mark.asyncio
async def test_agent_message_passing():
    """Test message passing between agents."""
    agent1 = MockAgent(
        agent_id="agent1",
        agent_type=AgentType.OBSERVING
    )
    
    agent2 = MockAgent(
        agent_id="agent2",
        agent_type=AgentType.CORE
    )
    
    # Connect agents
    agent1.connect_to_agent(agent2)
    
    # Send message
    await agent1.send_message("agent2", "test_message", {"data": "test"})
    
    # Check message was received
    assert len(agent2.message_queue) == 1
    message = agent2.message_queue[0]
    assert message.sender_id == "agent1"
    assert message.recipient_id == "agent2"
    assert message.message_type == "test_message"
    assert message.content == {"data": "test"}


@pytest.mark.asyncio
async def test_agent_process_input():
    """Test agent input processing."""
    agent = MockAgent(
        agent_id="test_agent",
        agent_type=AgentType.OBSERVING
    )
    
    result = await agent.process_input({"test": "data"})
    assert result == {"response": "Processed: {'test': 'data'}"}


@pytest.mark.asyncio
async def test_agent_status():
    """Test agent status reporting."""
    agent = MockAgent(
        agent_id="test_agent",
        agent_type=AgentType.OBSERVING,
        model_provider="local"
    )
    
    status = agent.get_status()
    assert status["agent_id"] == "test_agent"
    assert status["agent_type"] == "observing"
    assert status["is_active"] is False
    assert status["model_provider"] == "local"
    assert status["connected_agents"] == []
    assert status["message_queue_size"] == 0 