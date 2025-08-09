#!/usr/bin/env python3
"""
Example usage of the Image Observer Agent.

This script demonstrates how to use the ImageObserverAgent to analyze
ONI base screenshots and get text summaries.
"""

import asyncio
import base64
import logging
from pathlib import Path

from src.oni_ai_agents.agents.image_observer_agent import ImageObserverAgent


async def main():
    """Demonstrate image observer agent functionality."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create image observer agent
    agent = ImageObserverAgent(
        agent_id="example_image_observer",
        model_provider="openai",  # Will use mock in this example
        model_config={"model": "gpt-4-vision-preview"}
    )
    
    # Start the agent
    await agent.start()
    
    try:
        # Example 1: Analyze image from file path
        image_path = "The Clone Laboratory.png"
        if Path(image_path).exists():
            print(f"\n📸 Analyzing image from file: {image_path}")
            
            input_data = {
                "image_path": image_path,
                "analysis_type": "base_overview"
            }
            
            result = await agent.process_input(input_data)
            
            print("✅ Analysis Result:")
            print(f"   Summary: {result['summary']}")
            print(f"   Image Hash: {result['image_hash'][:16]}...")
            print(f"   Timestamp: {result['timestamp']}")
        
        # Example 2: Analyze image from base64
        print(f"\n📸 Analyzing image from base64 data...")
        
        # Load image as base64 (using a small sample)
        sample_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        input_data = {
            "image": sample_base64,
            "analysis_type": "resource_analysis"
        }
        
        result = await agent.process_input(input_data)
        
        print("✅ Analysis Result:")
        print(f"   Summary: {result['summary']}")
        print(f"   Analysis Type: {result['analysis_type']}")
        print(f"   Image Hash: {result['image_hash'][:16]}...")
        
        # Example 3: Different analysis types
        analysis_types = ["base_overview", "threat_assessment", "efficiency_analysis"]
        
        for analysis_type in analysis_types:
            print(f"\n📸 Testing {analysis_type} analysis...")
            
            input_data = {
                "image": sample_base64,
                "analysis_type": analysis_type
            }
            
            result = await agent.process_input(input_data)
            
            print(f"   Summary: {result['summary']}")
            print(f"   Type: {result['analysis_type']}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Stop the agent
        await agent.stop()
        print("\n🛑 Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())


