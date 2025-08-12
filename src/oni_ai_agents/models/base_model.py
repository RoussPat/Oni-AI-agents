"""
Base model interface for AI model connectivity.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseModel(ABC):
    """
    Base class for AI model implementations.
    
    This abstract class defines the interface that all model
    implementations must follow.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the model.
        
        Args:
            config: Model configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f"Model.{self.__class__.__name__}")
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the model connection.
        
        Returns:
            True if initialization successful, False otherwise
        """
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated response text
        """
    
    @abstractmethod
    async def generate_structured_response(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a structured response following a schema.
        
        Args:
            prompt: The input prompt
            schema: JSON schema defining the expected response structure
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional model-specific parameters
            
        Returns:
            Structured response as dictionary
        """
    
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_type": self.__class__.__name__,
            "is_initialized": self.is_initialized,
            "config": self.config
        }
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the model.
        
        Returns:
            True if model is healthy, False otherwise
        """
        try:
            # Simple test prompt
            response = await self.generate_response(
                "Hello, this is a health check.",
                temperature=0.0,
                max_tokens=10
            )
            return bool(response and len(response.strip()) > 0)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False 