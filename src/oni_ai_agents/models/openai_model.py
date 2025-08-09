"""
OpenAI model implementation.
"""

import json
import os
from typing import Any, Dict, List, Optional

from .base_model import BaseModel


class OpenAIModel(BaseModel):
    """
    OpenAI model implementation using OpenAI API.
    
    Supports GPT-3.5, GPT-4, and other OpenAI models.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI model.
        
        Args:
            config: Configuration dictionary with:
                - api_key: OpenAI API key
                - model: Model name (e.g., gpt-4, gpt-3.5-turbo)
                - base_url: Optional custom base URL
        """
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.model_name = config.get("model", "gpt-3.5-turbo")
        self.base_url = config.get("base_url")
        self.client = None
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    async def initialize(self) -> bool:
        """Initialize the OpenAI client."""
        try:
            import openai
            
            # Configure the client
            if self.base_url:
                openai.api_base = self.base_url
            
            # Test the connection
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            self.is_initialized = True
            self.logger.info(f"OpenAI model initialized: {self.model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI model: {e}")
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
        Generate a response using OpenAI API.
        
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
            import openai
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content.strip()
            
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
        Generate a structured response using OpenAI's function calling.
        
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
            import openai
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Create function definition from schema
            function_def = {
                "name": "generate_response",
                "description": "Generate a structured response",
                "parameters": schema
            }
            
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=messages,
                functions=[function_def],
                function_call={"name": "generate_response"},
                temperature=temperature,
                **kwargs
            )
            
            # Parse the function call response
            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "generate_response":
                return json.loads(function_call.arguments)
            else:
                raise ValueError("Failed to generate structured response")
                
        except Exception as e:
            self.logger.error(f"Failed to generate structured response: {e}")
            return {"error": str(e)}
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings using OpenAI's embedding API.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            import openai
            
            embeddings = []
            for text in texts:
                response = await openai.Embedding.acreate(
                    model="text-embedding-ada-002",
                    input=text
                )
                embeddings.append(response.data[0].embedding)
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to get embeddings: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information."""
        info = super().get_model_info()
        info.update({
            "model_name": self.model_name,
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key)
        })
        return info 