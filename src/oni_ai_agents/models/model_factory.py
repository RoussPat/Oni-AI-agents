"""
Model factory for creating different AI model instances.
"""

import logging
from typing import Any, Dict, Optional

from .base_model import BaseModel
from .openai_model import OpenAIModel
from .anthropic_model import AnthropicModel
from .local_model import LocalModel
from .rate_limiter import RateLimiter, RateLimitConfig, RateLimitedModel, RateLimitStrategy


class ModelFactory:
    """
    Factory class for creating AI model instances.
    
    Supports multiple providers and handles configuration
    for different model types.
    """
    
    _models = {
        "openai": OpenAIModel,
        "anthropic": AnthropicModel,
        "local": LocalModel,
    }
    
    @classmethod
    def create_model(cls, provider: str, config: Dict[str, Any]) -> BaseModel:
        """
        Create a model instance for the specified provider.
        
        Args:
            provider: Model provider (openai, anthropic, local, etc.)
            config: Model configuration
            
        Returns:
            Model instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()
        
        if provider not in cls._models:
            raise ValueError(f"Unsupported model provider: {provider}")
        
        model_class = cls._models[provider]
        base_model = model_class(config)
        
        # Add rate limiting if configured
        rate_limit_config = config.get("rate_limit")
        if rate_limit_config:
            # Convert string strategy to enum if needed
            if "strategy" in rate_limit_config and isinstance(rate_limit_config["strategy"], str):
                strategy_str = rate_limit_config["strategy"]
                try:
                    rate_limit_config["strategy"] = RateLimitStrategy(strategy_str)
                except ValueError:
                    raise ValueError(f"Invalid rate limit strategy: {strategy_str}")
            
            rate_limiter = RateLimiter(RateLimitConfig(**rate_limit_config))
            return RateLimitedModel(base_model, rate_limiter)
        
        return base_model
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported model providers."""
        return list(cls._models.keys())
    
    @classmethod
    def register_provider(cls, name: str, model_class: type) -> None:
        """
        Register a new model provider.
        
        Args:
            name: Provider name
            model_class: Model class that inherits from BaseModel
        """
        if not issubclass(model_class, BaseModel):
            raise ValueError(f"Model class must inherit from BaseModel")
        
        cls._models[name.lower()] = model_class
        logging.getLogger(__name__).info(f"Registered model provider: {name}")
    
    @classmethod
    def get_model_info(cls, provider: str) -> Dict[str, Any]:
        """
        Get information about a model provider.
        
        Args:
            provider: Model provider name
            
        Returns:
            Dictionary with provider information
        """
        provider = provider.lower()
        
        if provider not in cls._models:
            return {"error": f"Provider {provider} not found"}
        
        model_class = cls._models[provider]
        return {
            "provider": provider,
            "class": model_class.__name__,
            "module": model_class.__module__,
            "doc": model_class.__doc__
        } 