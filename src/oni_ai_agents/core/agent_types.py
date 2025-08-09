"""
Agent types for the ONI AI system.
"""

from enum import Enum, auto


class AgentType(Enum):
    """Types of agents in the ONI AI system."""
    
    OBSERVING = auto()  # Monitors game state
    CORE = auto()       # Central decision maker
    COMMANDS = auto()    # Executes game actions 