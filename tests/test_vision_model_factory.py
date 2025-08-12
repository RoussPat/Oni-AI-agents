"""
Tests for the Vision Model Factory.

This module tests the vision model factory functionality for creating
and configuring different AI vision models.
"""


import pytest

from src.oni_ai_agents.models.vision_model_factory import (
    AnthropicVisionModel,
    LocalVisionModel,
    OpenAIVisionModel,
    VisionModelFactory,
)


class TestVisionModelFactory:
    """Test suite for the Vision Model Factory."""
    
    def test_create_openai_vision_model(self):
        """Test creating OpenAI vision model."""
        config = {
            "model": "gpt-4-vision-preview",
            "api_key": "test_key",
            "max_tokens": 1000
        }
        
        model = VisionModelFactory.create("openai", config)
        
        assert isinstance(model, OpenAIVisionModel)
        assert model.config == config
    
    def test_create_anthropic_vision_model(self):
        """Test creating Anthropic vision model."""
        config = {
            "model": "claude-3-5-sonnet-20241022",
            "api_key": "test_key",
            "max_tokens": 1000
        }
        
        model = VisionModelFactory.create("anthropic", config)
        
        assert isinstance(model, AnthropicVisionModel)
        assert model.config == config
    
    def test_create_local_vision_model(self):
        """Test creating local vision model."""
        config = {
            "model": "llava",
            "endpoint": "http://localhost:11434",
            "max_tokens": 1000
        }
        
        model = VisionModelFactory.create("local", config)
        
        assert isinstance(model, LocalVisionModel)
        assert model.config == config
    
    def test_create_unsupported_provider(self):
        """Test creating model with unsupported provider."""
        config = {"model": "test_model"}
        
        with pytest.raises(ValueError, match="Unsupported vision model provider"):
            VisionModelFactory.create("unsupported_provider", config)
    
    def test_create_with_empty_config(self):
        """Test creating model with empty configuration."""
        model = VisionModelFactory.create("openai", {})
        
        assert isinstance(model, OpenAIVisionModel)
        assert model.config == {}
    
    def test_create_with_none_config(self):
        """Test creating model with None configuration."""
        model = VisionModelFactory.create("openai", None)
        
        assert isinstance(model, OpenAIVisionModel)
        assert model.config is None
    
    def test_supported_providers(self):
        """Test that all supported providers are listed."""
        providers = VisionModelFactory.get_supported_providers()
        
        assert "openai" in providers
        assert "anthropic" in providers
        assert "local" in providers
        assert len(providers) >= 3
    
    def test_provider_validation(self):
        """Test provider validation functionality."""
        # Valid providers
        assert VisionModelFactory.is_provider_supported("openai")
        assert VisionModelFactory.is_provider_supported("anthropic")
        assert VisionModelFactory.is_provider_supported("local")
        
        # Invalid providers
        assert not VisionModelFactory.is_provider_supported("invalid")
        assert not VisionModelFactory.is_provider_supported("")
        assert not VisionModelFactory.is_provider_supported(None)


class TestVisionModelFactoryIntegration:
    """Integration tests for the Vision Model Factory."""
    
    def test_openai_model_creation_integration(self):
        """Test OpenAI model creation with real configuration."""
        config = {
            "model": "gpt-4-vision-preview",
            "api_key": "test_key",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        model = VisionModelFactory.create("openai", config)
        
        # Verify model was created with correct config
        assert isinstance(model, OpenAIVisionModel)
        assert model.config == config
    
    def test_anthropic_model_creation_integration(self):
        """Test Anthropic model creation with real configuration."""
        config = {
            "model": "claude-3-5-sonnet-20241022",
            "api_key": "test_key",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        model = VisionModelFactory.create("anthropic", config)
        
        # Verify model was created with correct config
        assert isinstance(model, AnthropicVisionModel)
        assert model.config == config
    
    def test_local_model_creation_integration(self):
        """Test local model creation with real configuration."""
        config = {
            "model": "llava",
            "endpoint": "http://localhost:11434",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        model = VisionModelFactory.create("local", config)
        
        # Verify model was created with correct config
        assert isinstance(model, LocalVisionModel)
        assert model.config == config


if __name__ == "__main__":
    pytest.main([__file__]) 