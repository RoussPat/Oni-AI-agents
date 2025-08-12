"""
Image Observer Agent for analyzing ONI base screenshots.

This agent takes PNG images as input and uses AI vision models to generate
text summaries of the base state for the core agent.
"""

import base64
import hashlib
import io
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image

from ..core.agent import Agent
from ..core.agent_types import AgentType
from ..models.vision_model_factory import VisionModelFactory


@dataclass
class ImageAnalysisResult:
    """Result of image analysis."""
    
    summary: str
    timestamp: float
    image_hash: str
    confidence: Optional[float] = None
    analysis_type: Optional[str] = None


class ImageObserverAgent(Agent):
    """
    Observer agent that analyzes ONI base screenshots using AI vision models.
    
    This agent takes PNG images as input and returns text summaries
    describing the base state for the core agent to process.
    """
    
    def __init__(
        self,
        agent_id: str,
        model_provider: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize the image observer agent.
        
        Args:
            agent_id: Unique identifier for this agent
            model_provider: AI vision model provider (openai, anthropic, local)
            model_config: Configuration for the AI vision model
        """
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.OBSERVING,
            model_provider=model_provider,
            model_config=model_config,
            **kwargs
        )
        
        # Initialize vision model if provider is specified
        if model_provider:
            self._initialize_vision_model()
        else:
            self.vision_model = None
    
    def _initialize_vision_model(self) -> None:
        """Initialize the AI vision model."""
        try:
            self.vision_model = VisionModelFactory.create(
                self.model_provider, 
                self.model_config
            )
            self.logger.info(f"Vision model initialized: {self.model_provider}")
            # Expose on .model as well for compatibility with tests/utilities
            # that expect a 'model' attribute to have generate_with_vision
            self.model = self.vision_model
        except Exception as e:
            self.logger.error(f"Failed to initialize vision model {self.model_provider}: {e}")
            # Fallback to a local stub so tests/integration can run without API keys
            try:
                self.vision_model = VisionModelFactory.create("local", self.model_config or {})
                self.model = self.vision_model
                self.logger.warning("Falling back to local vision model for ImageObserverAgent")
            except Exception:
                self.vision_model = None
                self.model = None
    
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process image input and return analysis result.
        
        Args:
            input_data: Dictionary containing image data and analysis type
                - image: base64 encoded image or bytes
                - image_path: path to image file
                - analysis_type: type of analysis to perform
                
        Returns:
            Dictionary containing analysis result with summary, timestamp, and image hash
        """
        # Extract image data
        image_data = self._extract_image_data(input_data)
        if not image_data:
            raise ValueError("No image data provided")
        
        # Validate image format
        self._validate_image_format(image_data)
        
        # Get analysis type
        analysis_type = input_data.get("analysis_type", "base_overview")
        
        # Generate image hash for tracking
        image_hash = self._hash_image(image_data)
        
        # Analyze image with AI model
        if not self.vision_model:
            raise RuntimeError("No vision model available for image analysis")
        
        try:
            summary, confidence = await self._analyze_image_with_ai(image_data, analysis_type)
            
            # Create result
            result = ImageAnalysisResult(
                summary=summary,
                timestamp=time.time(),
                image_hash=image_hash,
                confidence=confidence,
                analysis_type=analysis_type
            )
            
            return self._format_output(result)
            
        except Exception as e:
            self.logger.error(f"Error analyzing image: {e}")
            raise
    
    def _extract_image_data(self, input_data: Dict[str, Any]) -> Optional[bytes]:
        """Extract image data from input."""
        # Try base64 encoded image
        if "image" in input_data:
            image_input = input_data["image"]
            if isinstance(image_input, str):
                # Base64 encoded string
                try:
                    return base64.b64decode(image_input)
                except Exception as e:
                    self.logger.error(f"Failed to decode base64 image: {e}")
                    return None
            elif isinstance(image_input, bytes):
                # Raw bytes
                return image_input
        
        # Try file path
        if "image_path" in input_data:
            image_path = Path(input_data["image_path"])
            if image_path.exists():
                try:
                    return image_path.read_bytes()
                except Exception as e:
                    self.logger.error(f"Failed to read image file {image_path}: {e}")
                    return None
        
        return None
    
    def _validate_image_format(self, image_data: bytes) -> None:
        """Validate that the image data is in a supported format."""
        try:
            # Try to open with PIL to validate format
            image = Image.open(io.BytesIO(image_data))
            image.verify()  # Verify the image data
            
            # Check if it's a supported format (PNG, JPG, etc.)
            if image.format not in ['PNG', 'JPEG', 'JPG']:
                raise ValueError(f"Unsupported image format: {image.format}")
                
        except Exception as e:
            raise ValueError(f"Invalid image format: {e}")
    
    def _hash_image(self, image_data: bytes) -> str:
        """Generate SHA-256 hash of image data for tracking changes."""
        return hashlib.sha256(image_data).hexdigest()
    
    async def _analyze_image_with_ai(self, image_data: bytes, analysis_type: str) -> Tuple[str, Optional[float]]:
        """
        Analyze image using AI vision model.
        
        Args:
            image_data: Raw image bytes
            analysis_type: Type of analysis to perform
            
        Returns:
            Text summary of the image analysis
        """
        # Create appropriate prompt based on analysis type
        prompt = self._create_analysis_prompt(analysis_type)
        
        # Call vision model
        result = await self.vision_model.generate_with_vision(prompt, image_data)
        
        # Handle different response formats
        if isinstance(result, dict):
            summary = result.get("summary", str(result))
            confidence = result.get("confidence")
            return summary, confidence
        else:
            return str(result), None
    
    def _create_analysis_prompt(self, analysis_type: str) -> str:
        """Create analysis prompt based on type."""
        base_prompt = "Analyze this Oxygen Not Included base screenshot and provide a concise summary."
        
        if analysis_type == "base_overview":
            return f"{base_prompt} Focus on: overall base state and layout, key resources (food, oxygen, power, water), any obvious issues or threats, notable buildings or structures."
        
        elif analysis_type == "resource_analysis":
            return f"{base_prompt} Focus specifically on: food storage and production, oxygen generation and distribution, power generation and consumption, water systems, resource efficiency and bottlenecks."
        
        elif analysis_type == "threat_assessment":
            return f"{base_prompt} Focus specifically on: immediate dangers or threats, heat management issues, disease outbreaks, resource shortages, structural problems, duplicant health and stress."
        
        elif analysis_type == "efficiency_analysis":
            return f"{base_prompt} Focus specifically on: production efficiency, idle duplicants, resource waste, optimization opportunities, workflow bottlenecks, automation potential."
        
        else:
            return base_prompt
    
    def _format_output(self, result: ImageAnalysisResult) -> Dict[str, Any]:
        """Format the analysis result for output."""
        output = {
            "summary": result.summary,
            "timestamp": result.timestamp,
            "image_hash": result.image_hash,
        }
        
        if result.confidence is not None:
            output["confidence"] = result.confidence
        
        if result.analysis_type:
            output["analysis_type"] = result.analysis_type
        
        return output
    
    async def _on_start(self) -> None:
        """Called when the agent starts."""
        self.logger.info(f"Image Observer Agent {self.agent_id} started")
    
    async def _on_stop(self) -> None:
        """Called when the agent stops."""
        self.logger.info(f"Image Observer Agent {self.agent_id} stopped")
    
    async def _process_message(self, message) -> None:
        """Process a received message."""
        if message.message_type == "analyze_image":
            # Process image analysis request
            try:
                result = await self.process_input(message.content)
                
                # Send result back to sender
                await self.send_message(
                    recipient_id=message.sender_id,
                    message_type="image_analysis_complete",
                    content=result
                )
                
            except Exception as e:
                self.logger.error(f"Error processing image analysis request: {e}")
                # Send error response
                await self.send_message(
                    recipient_id=message.sender_id,
                    message_type="image_analysis_error",
                    content={"error": str(e)}
                )
        
        else:
            self.logger.warning(f"Unknown message type: {message.message_type}") 