"""
Tests for rate limiting functionality.
"""

import pytest
import asyncio
import time
from src.oni_ai_agents.models.rate_limiter import (
    RateLimiter, 
    RateLimitConfig, 
    RateLimitStrategy,
    RateLimitedModel
)
from src.oni_ai_agents.models.local_model import LocalModel


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    def test_rate_limit_config(self):
        """Test rate limit configuration."""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000,
            burst_limit=5,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        
        assert config.requests_per_minute == 10
        assert config.requests_per_hour == 100
        assert config.requests_per_day == 1000
        assert config.burst_limit == 5
        assert config.strategy == RateLimitStrategy.SLIDING_WINDOW
    
    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality."""
        config = RateLimitConfig(
            requests_per_minute=5,
            burst_limit=3
        )
        
        rate_limiter = RateLimiter(config)
        
        # Should allow first 3 requests (burst limit)
        for i in range(3):
            assert await rate_limiter.acquire(timeout=0.1)
        
        # Should block the 4th request
        assert not await rate_limiter.acquire(timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_sliding_window_rate_limiting(self):
        """Test sliding window rate limiting."""
        config = RateLimitConfig(
            requests_per_minute=3,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        
        rate_limiter = RateLimiter(config)
        
        # Make 3 requests quickly
        for i in range(3):
            assert await rate_limiter.acquire(timeout=0.1)
        
        # 4th request should be blocked
        assert not await rate_limiter.acquire(timeout=0.1)
        
        # Wait for some time and try again
        await asyncio.sleep(0.1)
        # Should still be blocked due to sliding window
        assert not await rate_limiter.acquire(timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_token_bucket_rate_limiting(self):
        """Test token bucket rate limiting."""
        config = RateLimitConfig(
            requests_per_minute=60,  # 1 request per second
            strategy=RateLimitStrategy.TOKEN_BUCKET
        )
        
        rate_limiter = RateLimiter(config)
        
        # Should allow first request
        assert await rate_limiter.acquire(timeout=0.1)
        
        # Second request should be blocked immediately
        assert not await rate_limiter.acquire(timeout=0.1)
        
        # Wait for token to refill
        await asyncio.sleep(1.1)
        
        # Should allow another request
        assert await rate_limiter.acquire(timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_status(self):
        """Test rate limiter status reporting."""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000
        )
        
        rate_limiter = RateLimiter(config)
        
        # Make a request
        await rate_limiter.acquire()
        
        # Check status
        status = rate_limiter.get_status()
        
        assert "strategy" in status
        assert "current_burst" in status
        assert "burst_limit" in status
        assert "requests_last_minute" in status
        assert "requests_last_hour" in status
        assert "requests_last_day" in status
        assert "limits" in status
        
        assert status["requests_last_minute"] == 1
        assert status["current_burst"] == 1


class TestRateLimitedModel:
    """Test rate-limited model wrapper."""
    
    @pytest.mark.asyncio
    async def test_rate_limited_model(self):
        """Test rate-limited model functionality."""
        # Create a local model
        local_model = LocalModel({"delay": 0.01})
        
        # Create rate limiter
        rate_limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=5,
            burst_limit=3
        ))
        
        # Create rate-limited model
        rate_limited_model = RateLimitedModel(local_model, rate_limiter)
        
        # Initialize the model
        await local_model.initialize()
        
        # Should allow first 3 requests
        for i in range(3):
            response = await rate_limited_model.generate_response("Test prompt")
            assert response is not None
        
        # 4th request should fail due to rate limiting
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await rate_limited_model.generate_response("Test prompt")
    
    @pytest.mark.asyncio
    async def test_rate_limited_model_info(self):
        """Test rate-limited model info includes rate limiter status."""
        local_model = LocalModel({"delay": 0.01})
        rate_limiter = RateLimiter(RateLimitConfig(requests_per_minute=10))
        rate_limited_model = RateLimitedModel(local_model, rate_limiter)
        
        info = rate_limited_model.get_model_info()
        
        assert "rate_limiter_status" in info
        assert "strategy" in info["rate_limiter_status"]
        assert "current_burst" in info["rate_limiter_status"]


@pytest.mark.asyncio
async def test_model_factory_with_rate_limiting():
    """Test model factory with rate limiting configuration."""
    from src.oni_ai_agents.models.model_factory import ModelFactory
    
    # Create model with rate limiting
    config = {
        "delay": 0.01,
        "rate_limit": {
            "requests_per_minute": 5,
            "burst_limit": 3,
            "strategy": "sliding_window"
        }
    }
    
    model = ModelFactory.create_model("local", config)
    
    # Initialize the model
    await model.initialize()
    
    # Should allow first 3 requests
    for i in range(3):
        response = await model.generate_response("Test prompt")
        assert response is not None
    
    # 4th request should fail due to rate limiting
    with pytest.raises(Exception, match="Rate limit exceeded"):
        await model.generate_response("Test prompt")


@pytest.mark.asyncio
async def test_concurrent_rate_limiting():
    """Test rate limiting with concurrent requests."""
    config = RateLimitConfig(
        requests_per_minute=10,
        burst_limit=5
    )
    
    rate_limiter = RateLimiter(config)
    
    # Create multiple concurrent requests
    async def make_request():
        return await rate_limiter.acquire(timeout=1.0)
    
    # Make 10 concurrent requests
    tasks = [make_request() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # Should allow 5 requests (burst limit)
    allowed_requests = sum(results)
    assert allowed_requests == 5
    assert results[:5] == [True] * 5
    assert results[5:] == [False] * 5


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 