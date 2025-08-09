"""
Core Agent class for the ONI AI system.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from .agent_types import AgentType


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""
    
    sender_id: str
    recipient_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    message_id: str = field(default_factory=lambda: str(uuid4()))


class Agent(ABC):
    """
    Base Agent class for the ONI AI system.
    
    This abstract class defines the interface and common functionality
    for all agents in the system.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        model_provider: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize the agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type of agent (observing, core, commands)
            model_provider: AI model provider (openai, anthropic, local, etc.)
            model_config: Configuration for the AI model
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.model_provider = model_provider
        self.model_config = model_config or {}
        
        # Communication
        self.message_queue: List[AgentMessage] = []
        self.connected_agents: Dict[str, 'Agent'] = {}
        
        # State
        self.is_active = False
        self.logger = logging.getLogger(f"Agent.{agent_id}")
        
        # Initialize model connection if provider is specified
        if model_provider:
            self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize the AI model connection."""
        try:
            from ..models.model_factory import ModelFactory
            self.model = ModelFactory.create_model(self.model_provider, self.model_config)
            self.logger.info(f"Model initialized: {self.model_provider}")
        except Exception as e:
            self.logger.error(f"Failed to initialize model {self.model_provider}: {e}")
            self.model = None
    
    async def start(self) -> None:
        """Start the agent."""
        self.is_active = True
        self.logger.info(f"Agent {self.agent_id} started")
        await self._on_start()
    
    async def stop(self) -> None:
        """Stop the agent."""
        self.is_active = False
        self.logger.info(f"Agent {self.agent_id} stopped")
        await self._on_stop()
    
    async def send_message(self, recipient_id: str, message_type: str, content: Dict[str, Any]) -> None:
        """Send a message to another agent."""
        message = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content
        )
        
        if recipient_id in self.connected_agents:
            await self.connected_agents[recipient_id].receive_message(message)
        else:
            self.logger.warning(f"Recipient {recipient_id} not found")
    
    async def receive_message(self, message: AgentMessage) -> None:
        """Receive a message from another agent."""
        self.message_queue.append(message)
        self.logger.debug(f"Received message from {message.sender_id}: {message.message_type}")
        await self._process_message(message)
    
    def connect_to_agent(self, agent: 'Agent') -> None:
        """Connect to another agent for direct communication."""
        self.connected_agents[agent.agent_id] = agent
        agent.connected_agents[self.agent_id] = self
        self.logger.info(f"Connected to agent {agent.agent_id}")
    
    def disconnect_from_agent(self, agent_id: str) -> None:
        """Disconnect from an agent."""
        if agent_id in self.connected_agents:
            agent = self.connected_agents.pop(agent_id)
            if self.agent_id in agent.connected_agents:
                agent.connected_agents.pop(self.agent_id)
            self.logger.info(f"Disconnected from agent {agent_id}")
    
    @abstractmethod
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return output.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            Processed output data
        """
        pass
    
    @abstractmethod
    async def _on_start(self) -> None:
        """Called when the agent starts."""
        pass
    
    @abstractmethod
    async def _on_stop(self) -> None:
        """Called when the agent stops."""
        pass
    
    @abstractmethod
    async def _process_message(self, message: AgentMessage) -> None:
        """Process a received message."""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.name.lower(),
            "is_active": self.is_active,
            "model_provider": self.model_provider,
            "connected_agents": list(self.connected_agents.keys()),
            "message_queue_size": len(self.message_queue)
        } 