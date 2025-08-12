"""
Local model implementation for testing and development.
"""

import random
from typing import Any, Dict, List, Optional

from .base_model import BaseModel


class LocalModel(BaseModel):
    """
    Local model implementation for testing and development.
    
    This is a mock implementation that returns predefined responses
    for testing the agent system without requiring external APIs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize local model.
        
        Args:
            config: Configuration dictionary with:
                - responses: Optional predefined responses
                - delay: Optional artificial delay in seconds
        """
        super().__init__(config)
        self.responses = config.get("responses", {})
        self.delay = config.get("delay", 0.1)
        self.response_count = 0
    
    async def initialize(self) -> bool:
        """Initialize the local model."""
        self.is_initialized = True
        self.logger.info("Local model initialized")
        return True
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a mock response.
        
        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (affects randomness)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Simulate processing delay
        import asyncio
        await asyncio.sleep(self.delay)
        
        # Use predefined responses if available
        if prompt in self.responses:
            response = self.responses[prompt]
        else:
            # Generate a mock response based on the prompt
            response = self._generate_mock_response(prompt, temperature)
        
        self.response_count += 1
        return response
    
    async def generate_structured_response(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a mock structured response.
        
        Args:
            prompt: The input prompt
            schema: JSON schema for the response structure
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Structured response as dictionary
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Simulate processing delay
        import asyncio
        await asyncio.sleep(self.delay)
        
        # Generate mock structured response based on schema
        response = self._generate_mock_structured_response(prompt, schema, temperature)
        
        self.response_count += 1
        return response
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate mock embeddings.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of mock embedding vectors
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Simulate processing delay
        import asyncio
        await asyncio.sleep(self.delay)
        
        # Generate mock embeddings (random vectors)
        embeddings = []
        for text in texts:
            # Generate a random embedding vector of dimension 384
            embedding = [random.uniform(-1, 1) for _ in range(384)]
            embeddings.append(embedding)
        
        return embeddings
    
    def _generate_mock_response(self, prompt: str, temperature: float) -> str:
        """Generate a mock response based on the prompt."""
        prompt_lower = prompt.lower()
        
        # Simple keyword-based responses
        if "hello" in prompt_lower or "hi" in prompt_lower:
            return "Hello! I'm a local AI model for testing."
        elif "how are you" in prompt_lower:
            return "I'm functioning well, thank you for asking!"
        elif "game" in prompt_lower or "oni" in prompt_lower:
            return "I'm ready to help with Oxygen Not Included game analysis."
        elif "resource" in prompt_lower:
            return "I can analyze resource levels and suggest optimizations."
        elif "colony" in prompt_lower:
            return "I can monitor colony status and health metrics."
        else:
            # Generic response with some randomness based on temperature
            responses = [
                "I understand your request and will process it accordingly.",
                "Based on the information provided, I can assist with this.",
                "Let me analyze this and provide a suitable response.",
                "I'm processing your input and generating a response.",
                "This is within my capabilities to handle."
            ]
            
            if temperature > 0.5:
                # Add some randomness for higher temperature
                responses.append("I'm feeling quite creative today!")
                responses.append("Let me think about this in a different way.")
            
            return random.choice(responses)
    
    def _generate_mock_structured_response(self, prompt: str, schema: Dict[str, Any], temperature: float) -> Dict[str, Any]:
        """Generate a mock structured response based on the schema."""
        response = {}
        
        # Generate mock data based on schema properties
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                prop_type = prop_schema.get("type", "string")
                
                if prop_type == "string":
                    response[prop_name] = f"mock_{prop_name}_value"
                elif prop_type == "number":
                    response[prop_name] = random.uniform(0, 100)
                elif prop_type == "integer":
                    response[prop_name] = random.randint(0, 100)
                elif prop_type == "boolean":
                    response[prop_name] = random.choice([True, False])
                elif prop_type == "array":
                    response[prop_name] = [f"item_{i}" for i in range(3)]
                elif prop_type == "object":
                    response[prop_name] = {"nested": "value"}
        
        return response
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get local model information."""
        info = super().get_model_info()
        info.update({
            "model_type": "Local Mock Model",
            "response_count": self.response_count,
            "delay": self.delay,
            "predefined_responses": len(self.responses)
        })
        return info 