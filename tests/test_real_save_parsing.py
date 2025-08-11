#!/usr/bin/env python3
"""
Real ONI Save File Analysis

Analyzes a real ONI save file to understand the binary format
and test our parser implementation.
"""

import json
import logging
import struct
import zlib
from datetime import datetime
from pathlib import Path

from src.oni_ai_agents.services.oni_save_parser import BinaryReader, OniSaveParser


def analyze_save_file_structure(file_path: Path):
    """Analyze the binary structure of a real ONI save file."""
    print(f"🔍 Analyzing save file structure: {file_path}")
    print(f"📁 File size: {file_path.stat().st_size:,} bytes ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"\n📊 Binary Analysis:")
    
    # Check for common patterns
    reader = BinaryReader(data)
    
    try:
        # Try to read what might be version info
        print(f"   First 32 bytes (hex): {data[:32].hex()}")
        print(f"   First 32 bytes (ascii): {repr(data[:32])}")
        
        # Look for potential integer values at the beginning
        reader.seek(0)
        first_int = reader.read_int32()
        second_int = reader.read_int32()
        third_int = reader.read_int32()
        fourth_int = reader.read_int32()
        
        print(f"   First 4 int32s: {first_int}, {second_int}, {third_int}, {fourth_int}")
        
        # Check if this could be version info (likely small positive numbers)
        if 0 < first_int < 100 and 0 < second_int < 100:
            print(f"   💡 Potential version: {first_int}.{second_int}")
        
        # Look for string patterns (length-prefixed strings)
        reader.seek(8)  # Skip potential version
        try:
            string_length = reader.read_int32()
            if 0 < string_length < 1000:  # Reasonable string length
                string_data = reader.read_bytes(string_length)
                try:
                    decoded_string = string_data.decode('utf-8')
                    print(f"   📝 Potential string at offset 8: '{decoded_string}'")
                except:
                    print(f"   📝 Non-UTF8 data at offset 8")
        except:
            pass
        
        # Look for compressed data signatures
        for offset in [0, 100, 200, 500, 1000]:
            if offset < len(data) - 10:
                chunk = data[offset:offset+10]
                if chunk.startswith(b'\x78\x9c') or chunk.startswith(b'\x78\xda'):
                    print(f"   🗜️  Potential zlib data at offset {offset}")
                    try:
                        # Try to decompress
                        decompressed = zlib.decompress(data[offset:offset+1000])
                        print(f"      ✅ Successfully decompressed {len(decompressed)} bytes")
                    except:
                        print(f"      ❌ Failed to decompress")
        
    except Exception as e:
        print(f"   ⚠️  Analysis error: {e}")


def test_parser_with_real_file():
    """Test our parser with the real save file."""
    print(f"\n🤖 Testing parser with real save file...")
    file_path = Path("test_data/clone_laboratory.sav")
    output_dir = Path("test_data/analysis_results")
    
    parser = OniSaveParser()
    result = parser.parse_save_file(file_path)
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Save parsing results
    results_file = output_dir / "parse_results.json"
    
    parse_info = {
        "timestamp": datetime.now().isoformat(),
        "file_path": str(file_path),
        "file_size_bytes": file_path.stat().st_size,
        "success": result.success,
        "error_message": result.error_message,
        "warnings": result.warnings,
        "parse_time_seconds": result.parse_time_seconds
    }
    
    if result.success and result.save_game:
        summary = result.save_game.get_summary()
        parse_info["save_summary"] = summary
        
        print(f"✅ Parser succeeded!")
        print(f"   Version: {summary.get('version', 'unknown')}")
        print(f"   Cycles: {summary.get('cycles', 'unknown')}")
        print(f"   Duplicants: {summary.get('duplicants', 'unknown')}")
        print(f"   Parse time: {result.parse_time_seconds:.3f}s")
        
        if summary.get('object_counts'):
            print(f"   Object counts:")
            for obj_type, count in summary['object_counts'].items():
                print(f"     - {obj_type}: {count}")
    else:
        print(f"❌ Parser failed: {result.error_message}")
    
    if result.warnings:
        print(f"⚠️  Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    # Include extracted entities (e.g., duplicants)
    try:
        parse_info["entities"] = result.entities
    except Exception:
        pass

    # Save results to file
    with open(results_file, 'w') as f:
        json.dump(parse_info, f, indent=2)
    
    print(f"💾 Results saved to: {results_file}")
    
    return result


def enhanced_binary_analysis(file_path: Path, output_dir: Path):
    """Enhanced binary analysis to understand the save format better."""
    print(f"\n🔬 Enhanced Binary Analysis...")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    analysis = {
        "file_size": len(data),
        "analysis_timestamp": datetime.now().isoformat(),
        "byte_distribution": {},
        "potential_structures": [],
        "compression_analysis": []
    }
    
    # Byte frequency analysis
    byte_counts = [0] * 256
    for byte in data:
        byte_counts[byte] += 1
    
    # Find most common bytes
    common_bytes = sorted(enumerate(byte_counts), key=lambda x: x[1], reverse=True)[:10]
    analysis["byte_distribution"] = {
        f"0x{byte:02x}": count for byte, count in common_bytes
    }
    
    # Look for repeating patterns
    reader = BinaryReader(data)
    
    # Scan for potential string tables or repeated structures
    for offset in range(0, min(len(data), 10000), 4):
        try:
            reader.seek(offset)
            potential_length = reader.read_int32()
            
            if 4 <= potential_length <= 1000:  # Reasonable string/data length
                try:
                    chunk = reader.read_bytes(potential_length)
                    if all(32 <= b <= 126 for b in chunk):  # Printable ASCII
                        try:
                            decoded = chunk.decode('utf-8')
                            analysis["potential_structures"].append({
                                "offset": offset,
                                "type": "string",
                                "length": potential_length,
                                "content": decoded[:100]  # First 100 chars
                            })
                        except:
                            pass
                except:
                    pass
        except:
            pass
    
    # Look for compressed sections
    for offset in range(0, len(data) - 100, 100):
        chunk = data[offset:offset+100]
        
        # Check for zlib headers
        for i in range(len(chunk) - 2):
            if chunk[i:i+2] in [b'\x78\x9c', b'\x78\xda', b'\x78\x01']:
                try:
                    remaining_data = data[offset+i:]
                    decompressed = zlib.decompress(remaining_data[:min(len(remaining_data), 50000)])
                    
                    analysis["compression_analysis"].append({
                        "offset": offset + i,
                        "compressed_size": "unknown",
                        "decompressed_size": len(decompressed),
                        "compression_ratio": "unknown",
                        "header": chunk[i:i+10].hex()
                    })
                    
                    print(f"   🗜️  Found compressed section at offset {offset + i}")
                    print(f"      Decompressed size: {len(decompressed):,} bytes")
                    
                    # Analyze decompressed data
                    if len(decompressed) > 100:
                        print(f"      First 100 bytes: {decompressed[:100]}")
                    
                    break  # Only find first compression in this chunk
                except:
                    pass
    
    # Save detailed analysis
    analysis_file = output_dir / "binary_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"💾 Binary analysis saved to: {analysis_file}")
    
    return analysis


def main():
    """Main analysis function."""
    logging.basicConfig(level=logging.INFO)
    
    print("🔬 Real ONI Save File Analysis")
    print("=" * 50)
    
    # File paths
    save_file = Path("test_data/clone_laboratory.sav")
    output_dir = Path("test_data/analysis_results")
    
    if not save_file.exists():
        print(f"❌ Save file not found: {save_file}")
        print("Make sure the save file was copied correctly.")
        return
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Basic structure analysis
        analyze_save_file_structure(save_file)
        
        # Step 2: Test our parser
        parser_result = test_parser_with_real_file(save_file, output_dir)
        
        # Step 3: Enhanced binary analysis
        binary_analysis = enhanced_binary_analysis(save_file, output_dir)
        
        # Step 4: Summary
        print(f"\n📋 Analysis Summary:")
        print(f"   File analyzed: {save_file}")
        print(f"   File size: {save_file.stat().st_size:,} bytes")
        print(f"   Parser success: {parser_result.success}")
        print(f"   Warnings: {len(parser_result.warnings)}")
        print(f"   Output directory: {output_dir}")
        print(f"   Potential strings found: {len(binary_analysis.get('potential_structures', []))}")
        print(f"   Compressed sections: {len(binary_analysis.get('compression_analysis', []))}")
        
        print(f"\n🎯 Next Steps:")
        if not parser_result.success:
            print(f"   1. Review binary structure analysis")
            print(f"   2. Compare with RoboPhred's parser format")
            print(f"   3. Implement proper header parsing")
            print(f"   4. Handle compression sections")
        else:
            print(f"   1. Implement detailed section parsing")
            print(f"   2. Test with observer agents")
            print(f"   3. Validate data accuracy")
        
        print(f"\n💾 All results saved to: {output_dir}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
