"""
Vision Model Factory for creating AI vision models.

This factory creates and configures different AI vision models
for image analysis in the ONI AI system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseVisionModel(ABC):
    """Base class for vision models."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize vision model with configuration."""
        self.config = config
    
    @abstractmethod
    async def generate_with_vision(self, prompt: str, image_data: bytes) -> str:
        """
        Generate text response based on image and prompt.
        
        Args:
            prompt: Text prompt for the model
            image_data: Raw image bytes
            
        Returns:
            Generated text response
        """
        pass


class OpenAIVisionModel(BaseVisionModel):
    """OpenAI vision model implementation."""
    
    async def generate_with_vision(self, prompt: str, image_data: bytes) -> str:
        """Generate response using OpenAI vision model."""
        # This would integrate with OpenAI's GPT-4V API
        # For now, return a mock response
        return f"OpenAI Vision Analysis: {prompt[:50]}..."


class AnthropicVisionModel(BaseVisionModel):
    """Anthropic vision model implementation."""
    
    async def generate_with_vision(self, prompt: str, image_data: bytes) -> str:
        """Generate response using Anthropic vision model."""
        # This would integrate with Anthropic's Claude 3.5 Sonnet API
        # For now, return a mock response
        return f"Anthropic Vision Analysis: {prompt[:50]}..."


class LocalVisionModel(BaseVisionModel):
    """Local vision model implementation."""
    
    async def generate_with_vision(self, prompt: str, image_data: bytes) -> str:
        """Generate response using local vision model."""
        # This would integrate with local models like LLaVA via Ollama
        # For now, return a mock response
        return f"Local Vision Analysis: {prompt[:50]}..."


class VisionModelFactory:
    """Factory for creating vision models."""
    
    _providers = {
        "openai": OpenAIVisionModel,
        "anthropic": AnthropicVisionModel,
        "local": LocalVisionModel,
    }
    
    @classmethod
    def create(cls, provider: str, config: Dict[str, Any]) -> BaseVisionModel:
        """
        Create a vision model instance.
        
        Args:
            provider: Model provider (openai, anthropic, local)
            config: Model configuration
            
        Returns:
            Vision model instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider not in cls._providers:
            raise ValueError(f"Unsupported vision model provider: {provider}")
        
        model_class = cls._providers[provider]
        return model_class(config)
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported providers."""
        return list(cls._providers.keys())
    
    @classmethod
    def is_provider_supported(cls, provider: str) -> bool:
        """Check if a provider is supported."""
        return provider in cls._providers 