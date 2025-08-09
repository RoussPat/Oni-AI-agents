"""
Rate limiter for AI model API calls.

Provides rate limiting functionality to prevent API quota exhaustion
and ensure fair usage across multiple agents.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from enum import Enum


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    
    FIXED_WINDOW = "fixed_window"      # Fixed time window
    SLIDING_WINDOW = "sliding_window"   # Sliding time window
    TOKEN_BUCKET = "token_bucket"       # Token bucket algorithm
    LEAKY_BUCKET = "leaky_bucket"       # Leaky bucket algorithm


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    retry_after_seconds: int = 60
    max_retries: int = 3


class RateLimiter:
    """
    Rate limiter for API calls.
    
    Supports multiple rate limiting strategies and provides
    async/await interface for easy integration.
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize the rate limiter.
        
        Args:
            config: Rate limiting configuration
        """
        self.config = config
        self.request_times: list = []
        self.last_request_time: float = 0
        self.current_burst: int = 0
        self.last_burst_reset: float = time.time()
        
        # Track different time windows
        self.minute_requests: list = []
        self.hour_requests: list = []
        self.day_requests: list = []
    
    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make an API call.
        
        Args:
            timeout: Maximum time to wait for permission (None = wait forever)
            
        Returns:
            True if permission granted, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self._can_make_request():
                self._record_request()
                return True
            
            # Check timeout
            if timeout is not None and (time.time() - start_time) > timeout:
                return False
            
            # Wait before retrying
            await asyncio.sleep(0.1)
    
    def _can_make_request(self) -> bool:
        """Check if a request can be made based on rate limits."""
        current_time = time.time()
        
        # Clean up old requests
        self._cleanup_old_requests(current_time)
        
        # Reset burst counter if enough time has passed (for non-token-bucket strategies)
        # Use a longer reset interval to prevent premature resets
        if (self.config.strategy != RateLimitStrategy.TOKEN_BUCKET and 
            self.config.strategy != RateLimitStrategy.LEAKY_BUCKET and
            current_time - self.last_burst_reset > 5.0):  # Reset burst every 5 seconds
            self.current_burst = 0
            self.last_burst_reset = current_time
        
        # Check burst limit
        if self.current_burst >= self.config.burst_limit:
            return False
        
        # Check rate limits based on strategy
        if self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(current_time)
        elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(current_time)
        elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(current_time)
        elif self.config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return self._check_leaky_bucket(current_time)
        
        return True
    
    def _check_fixed_window(self, current_time: float) -> bool:
        """Check fixed window rate limits."""
        # Check minute limit
        minute_ago = current_time - 60
        minute_count = len([t for t in self.minute_requests if t > minute_ago])
        if minute_count >= self.config.requests_per_minute:
            return False
        
        # Check hour limit
        hour_ago = current_time - 3600
        hour_count = len([t for t in self.hour_requests if t > hour_ago])
        if hour_count >= self.config.requests_per_hour:
            return False
        
        # Check day limit
        day_ago = current_time - 86400
        day_count = len([t for t in self.day_requests if t > day_ago])
        if day_count >= self.config.requests_per_day:
            return False
        
        return True
    
    def _check_sliding_window(self, current_time: float) -> bool:
        """Check sliding window rate limits."""
        # Sliding window: count requests in the last window period
        window_size = 60  # 1 minute window
        
        # Count requests in the sliding window
        window_start = current_time - window_size
        window_requests = [t for t in self.minute_requests if t > window_start]
        
        # Check if we're within the limit
        if len(window_requests) >= self.config.requests_per_minute:
            return False
        
        # Also check burst limit
        if self.current_burst >= self.config.burst_limit:
            return False
        
        return True
    
    def _check_token_bucket(self, current_time: float) -> bool:
        """Check token bucket rate limits."""
        tokens_per_second = self.config.requests_per_minute / 60.0
        
        # Handle initial state
        if self.last_request_time == 0:
            # Start with 1 token for immediate first request
            self.current_burst = 1.0
            return True
        
        time_since_last = current_time - self.last_request_time
        
        # Add tokens based on time passed
        new_tokens = time_since_last * tokens_per_second
        self.current_burst = min(self.config.burst_limit, self.current_burst + new_tokens)
        
        # Check if we have at least one token to consume
        return self.current_burst >= 1.0
    
    def _check_leaky_bucket(self, current_time: float) -> bool:
        """Check leaky bucket rate limits."""
        leak_rate = self.config.requests_per_minute / 60.0
        
        # Handle initial state
        if self.last_request_time == 0:
            self.current_burst = 0
            return True
        
        time_since_last = current_time - self.last_request_time
        
        # Leak tokens based on time passed
        leaked_tokens = time_since_last * leak_rate
        self.current_burst = max(0, self.current_burst - leaked_tokens)
        
        return self.current_burst < self.config.burst_limit
    
    def _cleanup_old_requests(self, current_time: float) -> None:
        """Clean up old request timestamps."""
        # Keep only recent requests for memory efficiency
        self.minute_requests = [t for t in self.minute_requests if t > current_time - 60]
        self.hour_requests = [t for t in self.hour_requests if t > current_time - 3600]
        self.day_requests = [t for t in self.day_requests if t > current_time - 86400]
    
    def _record_request(self) -> None:
        """Record a successful request."""
        current_time = time.time()
        
        # Update burst counter based on strategy
        if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            # Consume a token
            self.current_burst = max(0, self.current_burst - 1.0)
        elif self.config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            # Add to bucket
            self.current_burst = min(self.config.burst_limit, self.current_burst + 1.0)
        else:
            # Fixed/Sliding window - use burst counter
            if current_time - self.last_burst_reset > 1.0:  # Reset burst every second
                self.current_burst = 0
                self.last_burst_reset = current_time
            
            self.current_burst += 1
        
        self.last_request_time = current_time
        
        # Record in different time windows
        self.minute_requests.append(current_time)
        self.hour_requests.append(current_time)
        self.day_requests.append(current_time)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status."""
        current_time = time.time()
        
        return {
            "strategy": self.config.strategy.value,
            "current_burst": self.current_burst,
            "burst_limit": self.config.burst_limit,
            "requests_last_minute": len([t for t in self.minute_requests if t > current_time - 60]),
            "requests_last_hour": len([t for t in self.hour_requests if t > current_time - 3600]),
            "requests_last_day": len([t for t in self.day_requests if t > current_time - 86400]),
            "limits": {
                "per_minute": self.config.requests_per_minute,
                "per_hour": self.config.requests_per_hour,
                "per_day": self.config.requests_per_day
            }
        }


class RateLimitedModel:
    """
    Wrapper for models that adds rate limiting.
    
    This class wraps any model implementation and adds
    rate limiting capabilities.
    """
    
    def __init__(self, model: Any, rate_limiter: RateLimiter):
        """
        Initialize the rate-limited model.
        
        Args:
            model: The underlying model to wrap
            rate_limiter: Rate limiter instance
        """
        self.model = model
        self.rate_limiter = rate_limiter
    
    async def initialize(self) -> bool:
        """Initialize the underlying model."""
        return await self.model.initialize()
    
    async def generate_response(self, *args, **kwargs):
        """Generate response with rate limiting."""
        if not await self.rate_limiter.acquire(timeout=1.0):
            raise Exception("Rate limit exceeded")
        
        return await self.model.generate_response(*args, **kwargs)
    
    async def generate_structured_response(self, *args, **kwargs):
        """Generate structured response with rate limiting."""
        if not await self.rate_limiter.acquire(timeout=1.0):
            raise Exception("Rate limit exceeded")
        
        return await self.model.generate_structured_response(*args, **kwargs)
    
    async def get_embeddings(self, *args, **kwargs):
        """Get embeddings with rate limiting."""
        if not await self.rate_limiter.acquire(timeout=1.0):
            raise Exception("Rate limit exceeded")
        
        return await self.model.get_embeddings(*args, **kwargs)
    
    def get_model_info(self):
        """Get model information."""
        info = self.model.get_model_info()
        info["rate_limiter_status"] = self.rate_limiter.get_status()
        return info 