"""
Example demonstrating rate limiting with AI agents.

This example shows how to configure rate limiting for different
AI model providers and how it affects agent behavior.
"""

import asyncio
import logging
from src.oni_ai_agents.core.agent import Agent, AgentMessage
from src.oni_ai_agents.core.agent_types import AgentType
from src.oni_ai_agents.models.rate_limiter import RateLimitConfig, RateLimitStrategy


class RateLimitedObservingAgent(Agent):
    """Observing agent with rate limiting."""
    
    async def process_input(self, input_data):
        """Process input with rate-limited AI model."""
        if not hasattr(self, 'model') or not self.model:
            return {"error": "No model available"}
        
        prompt = f"Analyze this data: {input_data}"
        response = await self.model.generate_response(prompt)
        return {"analysis": response, "input": input_data}
    
    async def _on_start(self):
        self.logger.info("Rate-limited observing agent started")
    
    async def _on_stop(self):
        self.logger.info("Rate-limited observing agent stopped")
    
    async def _process_message(self, message: AgentMessage):
        """Process incoming messages."""
        if message.message_type == "request_analysis":
            result = await self.process_input(message.content)
            await self.send_message(
                message.sender_id,
                "analysis_result",
                result
            )


async def demonstrate_rate_limiting():
    """Demonstrate rate limiting with different configurations."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Rate Limiting Demo")
    print("=" * 40)
    
    # Configuration 1: Strict rate limiting
    print("\n📊 Configuration 1: Strict Rate Limiting")
    strict_config = {
        "delay": 0.01,
        "rate_limit": {
            "requests_per_minute": 3,
            "burst_limit": 2,
            "strategy": "sliding_window"
        }
    }
    
    agent1 = RateLimitedObservingAgent(
        agent_id="strict_agent",
        agent_type=AgentType.OBSERVING,
        model_provider="local",
        model_config=strict_config
    )
    
    await agent1.start()
    
    # Try to make 5 requests quickly
    print("Making 5 rapid requests...")
    results = []
    for i in range(5):
        try:
            result = await agent1.process_input({"test": f"data_{i}"})
            results.append(f"Request {i+1}: SUCCESS")
        except Exception as e:
            results.append(f"Request {i+1}: FAILED - {str(e)}")
    
    for result in results:
        print(f"  {result}")
    
    await agent1.stop()
    
    # Configuration 2: Token bucket rate limiting
    print("\n📊 Configuration 2: Token Bucket Rate Limiting")
    token_config = {
        "delay": 0.01,
        "rate_limit": {
            "requests_per_minute": 60,  # 1 request per second
            "burst_limit": 5,
            "strategy": "token_bucket"
        }
    }
    
    agent2 = RateLimitedObservingAgent(
        agent_id="token_agent",
        agent_type=AgentType.OBSERVING,
        model_provider="local",
        model_config=token_config
    )
    
    await agent2.start()
    
    # Make requests with delays
    print("Making requests with token bucket rate limiting...")
    for i in range(3):
        try:
            result = await agent2.process_input({"test": f"data_{i}"})
            print(f"  Request {i+1}: SUCCESS")
            await asyncio.sleep(0.5)  # Wait between requests
        except Exception as e:
            print(f"  Request {i+1}: FAILED - {str(e)}")
    
    await agent2.stop()
    
    # Configuration 3: No rate limiting (for comparison)
    print("\n📊 Configuration 3: No Rate Limiting")
    no_limit_config = {
        "delay": 0.01
    }
    
    agent3 = RateLimitedObservingAgent(
        agent_id="no_limit_agent",
        agent_type=AgentType.OBSERVING,
        model_provider="local",
        model_config=no_limit_config
    )
    
    await agent3.start()
    
    # Make 5 requests quickly
    print("Making 5 rapid requests without rate limiting...")
    for i in range(5):
        try:
            result = await agent3.process_input({"test": f"data_{i}"})
            print(f"  Request {i+1}: SUCCESS")
        except Exception as e:
            print(f"  Request {i+1}: FAILED - {str(e)}")
    
    await agent3.stop()
    
    print("\n✅ Rate limiting demo completed!")


async def demonstrate_concurrent_rate_limiting():
    """Demonstrate rate limiting with concurrent requests."""
    
    print("\n🔄 Concurrent Rate Limiting Demo")
    print("=" * 40)
    
    # Create agent with rate limiting
    config = {
        "delay": 0.01,
        "rate_limit": {
            "requests_per_minute": 10,
            "burst_limit": 3,
            "strategy": "sliding_window"
        }
    }
    
    agent = RateLimitedObservingAgent(
        agent_id="concurrent_agent",
        agent_type=AgentType.OBSERVING,
        model_provider="local",
        model_config=config
    )
    
    await agent.start()
    
    # Create concurrent requests
    async def make_request(request_id):
        try:
            result = await agent.process_input({"test": f"concurrent_{request_id}"})
            return f"Request {request_id}: SUCCESS"
        except Exception as e:
            return f"Request {request_id}: FAILED - {str(e)}"
    
    # Make 8 concurrent requests
    print("Making 8 concurrent requests...")
    tasks = [make_request(i) for i in range(8)]
    results = await asyncio.gather(*tasks)
    
    for result in results:
        print(f"  {result}")
    
    # Count successes and failures
    successes = len([r for r in results if "SUCCESS" in r])
    failures = len([r for r in results if "FAILED" in r])
    
    print(f"\n📈 Results: {successes} successes, {failures} failures")
    print(f"Expected: 3 successes (burst limit), 5 failures")
    
    await agent.stop()


async def demonstrate_rate_limiter_status():
    """Demonstrate rate limiter status monitoring."""
    
    print("\n📊 Rate Limiter Status Demo")
    print("=" * 40)
    
    from src.oni_ai_agents.models.model_factory import ModelFactory
    
    # Create model with rate limiting
    config = {
        "delay": 0.01,
        "rate_limit": {
            "requests_per_minute": 5,
            "burst_limit": 2,
            "strategy": "sliding_window"
        }
    }
    
    model = ModelFactory.create_model("local", config)
    await model.model.initialize()
    
    # Check initial status
    print("Initial status:")
    info = model.get_model_info()
    status = info["rate_limiter_status"]
    print(f"  Strategy: {status['strategy']}")
    print(f"  Current burst: {status['current_burst']}")
    print(f"  Burst limit: {status['burst_limit']}")
    print(f"  Requests last minute: {status['requests_last_minute']}")
    
    # Make some requests
    print("\nMaking requests...")
    for i in range(3):
        try:
            await model.generate_response(f"Test prompt {i}")
            print(f"  Request {i+1}: SUCCESS")
        except Exception as e:
            print(f"  Request {i+1}: FAILED - {str(e)}")
    
    # Check status after requests
    print("\nStatus after requests:")
    info = model.get_model_info()
    status = info["rate_limiter_status"]
    print(f"  Current burst: {status['current_burst']}")
    print(f"  Requests last minute: {status['requests_last_minute']}")
    print(f"  Requests last hour: {status['requests_last_hour']}")
    print(f"  Requests last day: {status['requests_last_day']}")


async def main():
    """Run all rate limiting demonstrations."""
    print("🤖 ONI AI Agents - Rate Limiting Examples")
    print("=" * 50)
    
    await demonstrate_rate_limiting()
    await demonstrate_concurrent_rate_limiting()
    await demonstrate_rate_limiter_status()
    
    print("\n🎉 All rate limiting demonstrations completed!")


if __name__ == "__main__":
    asyncio.run(main()) 