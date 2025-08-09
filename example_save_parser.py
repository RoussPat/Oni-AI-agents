#!/usr/bin/env python3
"""
Example ONI Save Parser Usage

Demonstrates how to use the Python ONI save parser implementation.
"""

import asyncio
import logging
from pathlib import Path

from src.oni_ai_agents.services.oni_save_parser import OniSaveParser
from src.oni_ai_agents.agents.resource_observer_agent import ResourceObserverAgent


async def main():
    """Demonstrate ONI save parser functionality."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("🔧 ONI Save Parser Demo")
    print("=" * 40)
    
    # Create parser
    parser = OniSaveParser()
    
    # Show supported versions
    versions = parser.get_supported_versions()
    print(f"\n📋 Supported Save Versions:")
    print(f"   Major: {versions['major_version']}")
    print(f"   Minor: {versions['minor_version_range']['min']}-{versions['minor_version_range']['max']}")
    print(f"   Based on: {versions['based_on']}")
    
    # Look for save files to parse
    save_file_locations = [
        Path("test_save.sav"),
        Path("research/test_data/example.sav"),
        Path.home() / "Documents/Klei/OxygenNotIncluded/save_files",
    ]
    
    save_file = None
    for location in save_file_locations:
        if location.is_file():
            save_file = location
            break
        elif location.is_dir():
            # Look for any .sav files in directory
            sav_files = list(location.glob("*.sav"))
            if sav_files:
                save_file = sav_files[0]
                break
    
    if save_file:
        print(f"\n💾 Found save file: {save_file}")
        
        # Parse the save file
        print("🔄 Parsing save file...")
        result = parser.parse_save_file(save_file)
        
        if result.success:
            print("✅ Parse successful!")
            
            # Show summary
            summary = result.save_game.get_summary()
            print(f"\n📊 Save File Summary:")
            print(f"   Version: {summary['version']}")
            print(f"   Cycles: {summary['cycles']}")
            print(f"   Duplicants: {summary['duplicants']}")
            print(f"   Object Groups: {summary['object_groups']}")
            print(f"   Total Objects: {summary['total_objects']}")
            
            if summary['object_counts']:
                print(f"   Object Types:")
                for obj_type, count in summary['object_counts'].items():
                    print(f"     - {obj_type}: {count}")
            
            # Show warnings if any
            if result.warnings:
                print(f"\n⚠️  Warnings ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"   - {warning}")
            
            print(f"\n⏱️  Parse time: {result.parse_time_seconds:.2f} seconds")
            
            # Demonstrate integration with observer agent
            print(f"\n🤖 Testing integration with Resource Observer Agent...")
            
            resource_agent = ResourceObserverAgent(
                agent_id="demo_resource_observer",
                model_provider="local",
                model_config={"delay": 0.1}
            )
            
            await resource_agent.start()
            
            try:
                # Test with parsed save data
                # Note: This will use placeholder data until full parsing is implemented
                analysis_result = await resource_agent.process_input({
                    "save_file_path": str(save_file)
                })
                
                print(f"   ✅ Agent analysis completed")
                print(f"   Agent: {analysis_result.get('agent_id', 'unknown')}")
                print(f"   Section: {analysis_result.get('section', 'unknown')}")
                
                if 'error' in analysis_result:
                    print(f"   ⚠️  Agent error: {analysis_result['error']}")
                
            finally:
                await resource_agent.stop()
        
        else:
            print(f"❌ Parse failed: {result.error_message}")
            if result.warnings:
                print(f"Warnings:")
                for warning in result.warnings:
                    print(f"   - {warning}")
    
    else:
        print(f"\n💡 No save files found. To test the parser:")
        print(f"   1. Play ONI and create a save file")
        print(f"   2. Copy a .sav file to this directory")
        print(f"   3. Or update the save_file_locations in this script")
        
        print(f"\n🔧 Parser Implementation Status:")
        print(f"   ✅ Binary reader for low-level operations")
        print(f"   ✅ Data structures matching ONI save format")
        print(f"   ✅ Basic parser framework")
        print(f"   ⚠️  Section parsing needs completion (based on RoboPhred's work)")
        print(f"   ⚠️  Type templates parsing")
        print(f"   ⚠️  Game objects parsing")
        print(f"   ⚠️  Compression handling")
        
        print(f"\n📚 Next Implementation Steps:")
        print(f"   1. Study RoboPhred's TypeScript types in detail")
        print(f"   2. Implement header parsing based on actual save format")
        print(f"   3. Add zlib decompression for compressed sections")
        print(f"   4. Parse type templates and game objects")
        print(f"   5. Test with real save files")
    
    print(f"\n🎯 Ready for:")
    print(f"   ✅ Observer agent integration (placeholder data)")
    print(f"   ✅ Extensible parser architecture")
    print(f"   ✅ Error handling and validation")
    print(f"   📈 Full implementation with real save parsing")


if __name__ == "__main__":
    asyncio.run(main())
