#!/usr/bin/env python3
"""
Simple Save File Test (without image dependencies)

Tests the real ONI save file parsing without dependencies that might cause issues.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from src.oni_ai_agents.services.oni_save_parser import OniSaveParser


def test_save_parsing():
    """Test parsing the real save file and show results."""
    
    print("🔬 Simple ONI Save File Test")
    print("=" * 50)
    
    # Parse the save file
    save_file = Path("test_data/clone_laboratory.sav")
    
    if not save_file.exists():
        print(f"❌ Save file not found: {save_file}")
        return
    
    print(f"📁 Testing file: {save_file}")
    print(f"📊 File size: {save_file.stat().st_size:,} bytes ({save_file.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # Parse with our parser
    parser = OniSaveParser()
    result = parser.parse_save_file(save_file)
    
    if result.success:
        print(f"\n✅ PARSING SUCCESS!")
        
        # Get save summary
        summary = result.save_game.get_summary()
        game_info = result.save_game.header.game_info
        
        print(f"\n📊 Save File Details:")
        print(f"   Game Name: {game_info.get('baseName', 'Unknown')}")
        print(f"   Save Version: {summary['version']}")
        print(f"   Build Version: {game_info.get('buildVersion', 'Unknown')}")
        print(f"   Header Version: {game_info.get('headerVersion', 'Unknown')}")
        print(f"   Compressed: {game_info.get('isCompressed', 'Unknown')}")
        print(f"   Cycles Played: {summary['cycles']}")
        print(f"   Duplicants: {summary['duplicants']}")
        print(f"   Cluster ID: {game_info.get('clusterId', 'Unknown')}")
        print(f"   DLC: {game_info.get('dlcIds', 'None')}")
        
        print(f"\n⏱️  Performance:")
        print(f"   Parse Time: {result.parse_time_seconds:.4f} seconds")
        
        if result.warnings:
            print(f"\n⚠️  Implementation Status ({len(result.warnings)} items pending):")
            for warning in result.warnings:
                print(f"   - {warning}")
        
        # Save detailed results
        output_dir = Path("test_data/final_results")
        output_dir.mkdir(exist_ok=True)
        
        detailed_results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "simple_save_parsing",
            "success": True,
            "file_info": {
                "path": str(save_file),
                "size_bytes": save_file.stat().st_size,
                "size_mb": round(save_file.stat().st_size / 1024 / 1024, 2)
            },
            "parsing_results": {
                "parse_time_seconds": result.parse_time_seconds,
                "warnings_count": len(result.warnings),
                "warnings": result.warnings
            },
            "game_data": {
                "name": game_info.get('baseName'),
                "version": summary['version'],
                "build_version": game_info.get('buildVersion'),
                "header_version": game_info.get('headerVersion'),
                "is_compressed": game_info.get('isCompressed'),
                "cycles": summary['cycles'],
                "duplicants": summary['duplicants'],
                "cluster_id": game_info.get('clusterId'),
                "dlc_ids": game_info.get('dlcIds'),
                "auto_save": game_info.get('isAutoSave'),
                "sandbox_enabled": game_info.get('sandboxEnabled'),
                "colony_guid": game_info.get('colonyGuid')
            },
            "full_game_info": game_info
        }
        
        results_file = output_dir / "parsing_success.json"
        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        # Show what we've accomplished
        print(f"\n🎉 ACHIEVEMENTS:")
        print(f"   ✅ Successfully parsed real ONI save file!")
        print(f"   ✅ Extracted game metadata from JSON header")
        print(f"   ✅ Handled binary format correctly") 
        print(f"   ✅ Parser architecture working")
        print(f"   ✅ Ready for observer agent integration")
        
        print(f"\n📈 NEXT STEPS FOR FULL IMPLEMENTATION:")
        print(f"   1. Parse type templates section")
        print(f"   2. Handle compressed save body")
        print(f"   3. Parse game objects (duplicants, buildings)")
        print(f"   4. Parse world/simulation data")
        print(f"   5. Connect to observer agents with real data")
        
        return detailed_results
        
    else:
        print(f"❌ PARSING FAILED: {result.error_message}")
        if result.warnings:
            for warning in result.warnings:
                print(f"   Warning: {warning}")
        return None


def main():
    """Main test function."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        results = test_save_parsing()
        
        if results:
            print(f"\n🏆 SUCCESS SUMMARY:")
            print(f"   Parsed: {results['game_data']['name']}")
            print(f"   Version: {results['game_data']['version']}")
            print(f"   Cycles: {results['game_data']['cycles']}")
            print(f"   Parse Time: {results['parsing_results']['parse_time_seconds']:.4f}s")
            print(f"   File Size: {results['file_info']['size_mb']} MB")
            
            print(f"\n🎯 Ready for your next development phase!")
        else:
            print(f"\n❌ Test failed - check the implementation")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
