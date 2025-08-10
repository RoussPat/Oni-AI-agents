"""
Tests for the Image Observer Agent.

This module tests the image observer agent functionality, including
image processing, AI model integration, and message handling.
"""

import asyncio
import base64
import hashlib
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from src.oni_ai_agents.core.agent import AgentMessage
from src.oni_ai_agents.core.agent_types import AgentType


# Module-level fixtures used by multiple classes
@pytest.fixture
def sample_image_path():
    """Provide path to sample ONI base image (shared)."""
    return "The Clone Laboratory.png"


@pytest.fixture
def sample_image_data(sample_image_path):
    """Load sample image as bytes (shared)."""
    with open(sample_image_path, 'rb') as f:
        return f.read()


@pytest.fixture
def sample_image_base64(sample_image_data):
    """Convert sample image to base64 (shared)."""
    return base64.b64encode(sample_image_data).decode('utf-8')


class TestImageObserverAgent:
    """Test suite for the Image Observer Agent."""
    
    # Class-scoped fixtures moved to module-level for reuse
    
    @pytest.fixture
    def mock_ai_model(self):
        """Mock AI model for testing."""
        mock_model = AsyncMock()
        mock_model.generate_with_vision.return_value = (
            "The base appears to be in good condition with multiple rooms, "
            "adequate food storage, and a stable oxygen system. "
            "No immediate threats detected."
        )
        return mock_model
    
    @pytest.fixture
    def image_observer_agent(self, mock_ai_model):
        """Create image observer agent with mocked dependencies."""
        with patch('src.oni_ai_agents.agents.image_observer_agent.VisionModelFactory') as mock_factory:
            mock_factory.create.return_value = mock_ai_model
            
            from src.oni_ai_agents.agents.image_observer_agent import ImageObserverAgent
            
            agent = ImageObserverAgent(
                agent_id="test_image_observer",
                model_provider="openai",
                model_config={"model": "gpt-4-vision-preview"}
            )
            return agent
    
    def test_agent_initialization(self, image_observer_agent):
        """Test that the image observer agent initializes correctly."""
        assert image_observer_agent.agent_id == "test_image_observer"
        assert image_observer_agent.agent_type == AgentType.OBSERVING
        assert image_observer_agent.model_provider == "openai"
        assert image_observer_agent.is_active is False
    
    def test_agent_start_stop(self, image_observer_agent):
        """Test agent start and stop functionality."""
        asyncio.run(image_observer_agent.start())
        assert image_observer_agent.is_active is True
        
        asyncio.run(image_observer_agent.stop())
        assert image_observer_agent.is_active is False
    
    @pytest.mark.asyncio
    async def test_process_image_input_base64(self, image_observer_agent, sample_image_base64, mock_ai_model):
        """Test processing image input in base64 format."""
        input_data = {
            "image": sample_image_base64,
            "analysis_type": "base_overview"
        }
        
        result = await image_observer_agent.process_input(input_data)
        
        # Verify AI model was called
        mock_ai_model.generate_with_vision.assert_called_once()
        call_args = mock_ai_model.generate_with_vision.call_args
        assert "analyze" in call_args[0][0].lower()
        assert "oxygen not included" in call_args[0][0].lower()
        
        # Verify output structure
        assert "summary" in result
        assert "timestamp" in result
        assert "image_hash" in result
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0
    
    @pytest.mark.asyncio
    async def test_process_image_input_bytes(self, image_observer_agent, sample_image_data, mock_ai_model):
        """Test processing image input as bytes."""
        input_data = {
            "image": sample_image_data,
            "analysis_type": "base_overview"
        }
        
        result = await image_observer_agent.process_input(input_data)
        
        # Verify AI model was called
        mock_ai_model.generate_with_vision.assert_called_once()
        
        # Verify output structure
        assert "summary" in result
        assert "timestamp" in result
        assert "image_hash" in result
    
    @pytest.mark.asyncio
    async def test_process_image_input_file_path(self, image_observer_agent, sample_image_path, mock_ai_model):
        """Test processing image input as file path."""
        input_data = {
            "image_path": sample_image_path,
            "analysis_type": "base_overview"
        }
        
        result = await image_observer_agent.process_input(input_data)
        
        # Verify AI model was called
        mock_ai_model.generate_with_vision.assert_called_once()
        
        # Verify output structure
        assert "summary" in result
        assert "timestamp" in result
        assert "image_hash" in result
    
    @pytest.mark.asyncio
    async def test_image_validation_invalid_format(self, image_observer_agent):
        """Test handling of invalid image format."""
        input_data = {
            "image": "invalid_image_data",
            "analysis_type": "base_overview"
        }
        
        with pytest.raises(ValueError, match="Invalid image format"):
            await image_observer_agent.process_input(input_data)
    
    @pytest.mark.asyncio
    async def test_image_validation_missing_image(self, image_observer_agent):
        """Test handling of missing image data."""
        input_data = {
            "analysis_type": "base_overview"
        }
        
        with pytest.raises(ValueError, match="No image data provided"):
            await image_observer_agent.process_input(input_data)
    
    @pytest.mark.asyncio
    async def test_ai_model_error_handling(self, image_observer_agent, sample_image_base64):
        """Test handling of AI model errors."""
        # Mock AI model to raise an exception
        image_observer_agent.vision_model.generate_with_vision.side_effect = Exception("AI model error")
        
        input_data = {
            "image": sample_image_base64,
            "analysis_type": "base_overview"
        }
        
        with pytest.raises(Exception, match="AI model error"):
            await image_observer_agent.process_input(input_data)
    
    @pytest.mark.asyncio
    async def test_message_processing(self, image_observer_agent, sample_image_base64):
        """Test processing messages from other agents."""
        message = AgentMessage(
            sender_id="core_agent",
            recipient_id="test_image_observer",
            message_type="analyze_image",
            content={
                "image": sample_image_base64,
                "analysis_type": "base_overview"
            }
        )
        
        await image_observer_agent.receive_message(message)
        
        # Verify message was processed
        assert len(image_observer_agent.message_queue) == 1
        assert image_observer_agent.message_queue[0].message_type == "analyze_image"
    
    @pytest.mark.asyncio
    async def test_agent_communication(self, image_observer_agent, sample_image_base64):
        """Test communication between agents."""
        # Create a mock core agent
        mock_core_agent = MagicMock()
        mock_core_agent.agent_id = "core_agent"
        mock_core_agent.receive_message = AsyncMock()
        
        # Connect agents
        image_observer_agent.connect_to_agent(mock_core_agent)
        
        # Send message to core agent
        await image_observer_agent.send_message(
            recipient_id="core_agent",
            message_type="image_analysis_complete",
            content={"summary": "Test analysis"}
        )
        
        # Verify message was sent
        mock_core_agent.receive_message.assert_called_once()
        sent_message = mock_core_agent.receive_message.call_args[0][0]
        assert sent_message.message_type == "image_analysis_complete"
        assert sent_message.content["summary"] == "Test analysis"
    
    def test_image_hash_generation(self, image_observer_agent, sample_image_data):
        """Test image hash generation for tracking changes."""
        hash1 = image_observer_agent._hash_image(sample_image_data)
        hash2 = image_observer_agent._hash_image(sample_image_data)
        
        # Same image should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hash length
        
        # Different data should produce different hash
        different_data = b"different_image_data"
        hash3 = image_observer_agent._hash_image(different_data)
        assert hash1 != hash3
    
    @pytest.mark.asyncio
    async def test_different_analysis_types(self, image_observer_agent, sample_image_base64, mock_ai_model):
        """Test different analysis types with appropriate prompts."""
        analysis_types = [
            "base_overview",
            "resource_analysis", 
            "threat_assessment",
            "efficiency_analysis"
        ]
        
        for analysis_type in analysis_types:
            input_data = {
                "image": sample_image_base64,
                "analysis_type": analysis_type
            }
            
            result = await image_observer_agent.process_input(input_data)
            
            # Verify AI model was called with appropriate prompt
            call_args = mock_ai_model.generate_with_vision.call_args
            prompt = call_args[0][0]
            
            if analysis_type == "resource_analysis":
                assert "resource" in prompt.lower()
            elif analysis_type == "threat_assessment":
                assert "threat" in prompt.lower() or "danger" in prompt.lower()
            elif analysis_type == "efficiency_analysis":
                assert "efficiency" in prompt.lower()
            
            # Reset mock for next iteration
            mock_ai_model.generate_with_vision.reset_mock()
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, image_observer_agent, sample_image_base64):
        """Test confidence scoring in analysis results."""
        # Mock AI model to return confidence score
        image_observer_agent.vision_model.generate_with_vision.return_value = {
            "summary": "Test analysis",
            "confidence": 0.85
        }
        
        input_data = {
            "image": sample_image_base64,
            "analysis_type": "base_overview"
        }
        
        result = await image_observer_agent.process_input(input_data)
        
        assert "confidence" in result
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1
    
    def test_agent_status(self, image_observer_agent):
        """Test agent status reporting."""
        status = image_observer_agent.get_status()
        
        assert "agent_id" in status
        assert "agent_type" in status
        assert "is_active" in status
        assert "model_provider" in status
        assert status["agent_id"] == "test_image_observer"
        assert status["agent_type"] == "observing"
    
    @pytest.mark.asyncio
    async def test_concurrent_image_processing(self, image_observer_agent, sample_image_base64):
        """Test concurrent processing of multiple images."""
        input_data = {
            "image": sample_image_base64,
            "analysis_type": "base_overview"
        }
        
        # Process multiple images concurrently
        tasks = [
            image_observer_agent.process_input(input_data)
            for _ in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all results are valid
        for result in results:
            assert "summary" in result
            assert "timestamp" in result
            assert "image_hash" in result
    
    def test_image_format_validation(self, image_observer_agent):
        """Test validation of different image formats."""
        # Test invalid data
        invalid_data = b'invalid_image_data'
        
        with pytest.raises(ValueError, match="Invalid image format"):
            image_observer_agent._validate_image_format(invalid_data)
        
        # Note: Valid PNG testing is complex due to checksums
        # We'll test with actual image files in integration tests
    
    @pytest.mark.asyncio
    async def test_error_logging(self, image_observer_agent, sample_image_base64, caplog):
        """Test that errors are properly logged."""
        # Mock AI model to raise an exception
        image_observer_agent.vision_model.generate_with_vision.side_effect = Exception("Test error")
        
        input_data = {
            "image": sample_image_base64,
            "analysis_type": "base_overview"
        }
        
        with pytest.raises(Exception):
            await image_observer_agent.process_input(input_data)
        
        # Verify error was logged
        assert "Test error" in caplog.text
        assert "ERROR" in caplog.text


class TestImageObserverAgentIntegration:
    """Integration tests for the Image Observer Agent."""
    
    @pytest.fixture
    def real_image_observer_agent(self):
        """Create image observer agent with real model configuration."""
        from src.oni_ai_agents.agents.image_observer_agent import ImageObserverAgent
        
        return ImageObserverAgent(
            agent_id="integration_test_observer",
            model_provider="openai",  # Will use mock in tests
            model_config={"model": "gpt-4-vision-preview"}
        )
    
    @pytest.mark.asyncio
    async def test_end_to_end_image_analysis(self, real_image_observer_agent, sample_image_path):
        """Test complete end-to-end image analysis workflow."""
        # Load image as base64
        with open(sample_image_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        input_data = {
            "image": image_base64,
            "analysis_type": "base_overview"
        }
        
        # Mock the AI model for integration test
        with patch.object(real_image_observer_agent.model, 'generate_with_vision') as mock_generate:
            mock_generate.return_value = "Integration test analysis result"
            
            result = await real_image_observer_agent.process_input(input_data)
            
            # Verify complete workflow
            assert "summary" in result
            assert "timestamp" in result
            assert "image_hash" in result
            assert result["summary"] == "Integration test analysis result"
            
            # Verify AI model was called with proper parameters
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert len(call_args[0]) == 2  # prompt and image
            assert "analyze" in call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_agent_network_communication(self, real_image_observer_agent, sample_image_base64):
        """Test communication in a network of agents."""
        # Create mock core agent
        mock_core_agent = MagicMock()
        mock_core_agent.agent_id = "core_agent"
        mock_core_agent.receive_message = AsyncMock()
        
        # Connect agents
        real_image_observer_agent.connect_to_agent(mock_core_agent)
        
        # Mock AI model
        with patch.object(real_image_observer_agent.model, 'generate_with_vision') as mock_generate:
            mock_generate.return_value = "Network test analysis"
            
            # Process image and send result to core agent
            input_data = {
                "image": sample_image_base64,
                "analysis_type": "base_overview"
            }
            
            result = await real_image_observer_agent.process_input(input_data)
            
            # Send result to core agent
            await real_image_observer_agent.send_message(
                recipient_id="core_agent",
                message_type="image_analysis_complete",
                content=result
            )
            
            # Verify communication
            mock_core_agent.receive_message.assert_called_once()
            sent_message = mock_core_agent.receive_message.call_args[0][0]
            assert sent_message.message_type == "image_analysis_complete"
            assert "summary" in sent_message.content
            assert sent_message.content["summary"] == "Network test analysis"


if __name__ == "__main__":
    pytest.main([__file__]) 