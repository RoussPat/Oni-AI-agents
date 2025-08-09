"""
Anthropic model implementation.
"""

import json
import os
from typing import Any, Dict, List, Optional

from .base_model import BaseModel


class AnthropicModel(BaseModel):
    """
    Anthropic model implementation using Claude API.
    
    Supports Claude-3 and other Anthropic models.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Anthropic model.
        
        Args:
            config: Configuration dictionary with:
                - api_key: Anthropic API key
                - model: Model name (e.g., claude-3-sonnet-20240229)
        """
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = config.get("model", "claude-3-sonnet-20240229")
        self.client = None
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
    
    async def initialize(self) -> bool:
        """Initialize the Anthropic client."""
        try:
            import anthropic
            
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # Test the connection
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=5,
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            self.is_initialized = True
            self.logger.info(f"Anthropic model initialized: {self.model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Anthropic model: {e}")
            return False
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a response using Anthropic API.
        
        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "user", "content": f"System: {system_prompt}\n\nUser: {prompt}"})
            else:
                messages.append({"role": "user", "content": prompt})
            
            response = await self.client.messages.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return f"Error generating response: {e}"
    
    async def generate_structured_response(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a structured response using Anthropic's tools.
        
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
        
        try:
            # Create tool definition from schema
            tool = {
                "name": "generate_response",
                "description": "Generate a structured response",
                "input_schema": schema
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "user", "content": f"System: {system_prompt}\n\nUser: {prompt}"})
            else:
                messages.append({"role": "user", "content": prompt})
            
            response = await self.client.messages.create(
                model=self.model_name,
                messages=messages,
                tools=[tool],
                temperature=temperature,
                **kwargs
            )
            
            # Parse the tool use response
            if response.content[0].type == "tool_use":
                tool_use = response.content[0]
                if tool_use.name == "generate_response":
                    return json.loads(tool_use.input)
            
            raise ValueError("Failed to generate structured response")
                
        except Exception as e:
            self.logger.error(f"Failed to generate structured response: {e}")
            return {"error": str(e)}
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings using Anthropic's embedding API.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            embeddings = []
            for text in texts:
                response = await self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                embeddings.append(response.embedding)
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to get embeddings: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Anthropic model information."""
        info = super().get_model_info()
        info.update({
            "model_name": self.model_name,
            "has_api_key": bool(self.api_key)
        })
        return info 