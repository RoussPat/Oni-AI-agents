"""
Demo script for the complete agent flow test.

This script runs the end-to-end agent flow test and shows
the communication between all three agent types.
"""

import asyncio
import logging

# This demo depends on a separate test module that might not exist in every environment.
# Guard the import so test collection doesn't fail when the module is absent.
try:
    from tests.test_agent_flow import (
        ResourceObservingAgent,
        ColonyCoreAgent,
        GameCommandsAgent,
    )
except Exception:  # pragma: no cover - demo-only fallback
    ResourceObservingAgent = None
    ColonyCoreAgent = None
    GameCommandsAgent = None


async def run_agent_flow_demo():
    """Run a demonstration of the complete agent flow."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🤖 ONI AI Agents - Complete Flow Demo")
    print("=" * 50)
    
    # Ensure optional dependencies are available
    if not all([ResourceObservingAgent, ColonyCoreAgent, GameCommandsAgent]):
        print("❌ Skipping demo: optional 'tests.test_agent_flow' not available.")
        return

    # Create the three agents
    print("\n📋 Creating agents...")
    resource_agent = ResourceObservingAgent(
        agent_id="resource_observer",
        model_provider="local",
        model_config={"delay": 0.1}
    )
    
    core_agent = ColonyCoreAgent(
        agent_id="colony_core",
        model_provider="local", 
        model_config={"delay": 0.1}
    )
    
    commands_agent = GameCommandsAgent(
        agent_id="commands_agent",
        model_provider="local",
        model_config={"delay": 0.1}
    )
    
    # Connect the agents
    print("🔗 Connecting agents...")
    resource_agent.connect_to_agent(core_agent)
    core_agent.connect_to_agent(commands_agent)
    commands_agent.connect_to_agent(core_agent)
    
    # Start all agents
    print("🚀 Starting agents...")
    await resource_agent.start()
    await core_agent.start()
    await commands_agent.start()
    
    # Simulate a critical game state
    print("\n🎮 Simulating game state...")
    game_state = {
        "resources": {
            "food": 25,      # Critical - below 50% threshold
            "oxygen": 35,    # Warning - below 1.5x threshold  
            "power": 80,     # OK
            "water": 10      # Critical - below 25% threshold
        },
        "duplicants": {
            "count": 8,
            "health": "good"
        },
        "threats": ["heat", "disease"]
    }
    
    print(f"Game State: {game_state}")
    
    # Step 1: Resource Analysis
    print("\n🔄 Step 1: Resource Analysis")
    print("Requesting resource analysis from observing agent...")
    
    await resource_agent.send_message(
        "colony_core",
        "request_resource_analysis", 
        {"game_state": game_state}
    )
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    # Check results
    print(f"\n📊 Resource Agent Results:")
    print(f"- Observations: {len(resource_agent.observations)}")
    if resource_agent.observations:
        latest = resource_agent.observations[-1]
        print(f"- Latest observation: {latest.get('alerts', [])}")
    
    # Step 2: Strategic Decision
    print("\n🔄 Step 2: Strategic Decision")
    print("Core agent processing observations...")
    
    await asyncio.sleep(0.5)
    
    print(f"\n🧠 Core Agent Results:")
    print(f"- Decisions made: {len(core_agent.decisions)}")
    if core_agent.decisions:
        latest = core_agent.decisions[-1]
        print(f"- Strategy: {latest.get('strategy', '')[:100]}...")
    
    # Step 3: Command Execution
    print("\n🔄 Step 3: Command Execution")
    print("Commands agent executing decisions...")
    
    await asyncio.sleep(0.5)
    
    print(f"\n⚡ Commands Agent Results:")
    print(f"- Commands executed: {len(commands_agent.executed_commands)}")
    if commands_agent.executed_commands:
        latest = commands_agent.executed_commands[-1]
        print(f"- Execution status: {latest.get('execution_status', 'unknown')}")
        print(f"- Commands: {latest.get('commands', '')[:100]}...")
    
    # Final Status Report
    print("\n📈 Final Status Report")
    print("-" * 30)
    
    resource_status = resource_agent.get_status()
    core_status = core_agent.get_status()
    commands_status = commands_agent.get_status()
    
    print(f"Resource Agent:")
    print(f"  - Active: {resource_status['is_active']}")
    print(f"  - Connected to: {resource_status['connected_agents']}")
    print(f"  - Messages in queue: {resource_status['message_queue_size']}")
    
    print(f"\nCore Agent:")
    print(f"  - Active: {core_status['is_active']}")
    print(f"  - Connected to: {core_status['connected_agents']}")
    print(f"  - Messages in queue: {core_status['message_queue_size']}")
    
    print(f"\nCommands Agent:")
    print(f"  - Active: {commands_status['is_active']}")
    print(f"  - Connected to: {commands_status['connected_agents']}")
    print(f"  - Messages in queue: {commands_status['message_queue_size']}")
    
    # Stop all agents
    print("\n🛑 Stopping agents...")
    await resource_agent.stop()
    await core_agent.stop()
    await commands_agent.stop()
    
    print("\n✅ Agent flow demo completed successfully!")
    
    # Summary
    print("\n📋 Summary:")
    print(f"- Resource observations: {len(resource_agent.observations)}")
    print(f"- Strategic decisions: {len(core_agent.decisions)}")
    print(f"- Commands executed: {len(commands_agent.executed_commands)}")
    print(f"- Total messages processed: {sum([
        resource_status['message_queue_size'],
        core_status['message_queue_size'], 
        commands_status['message_queue_size']
    ])}")


if __name__ == "__main__":
    asyncio.run(run_agent_flow_demo()) 