# ONI Save Parser Analysis

Based on analysis of existing ONI save parser projects, this document outlines the key findings and recommendations for implementing a Python-based parser.

## 📊 **Analyzed Projects**

### 1. **RoboPhred's oni-save-parser (JavaScript)** ⭐ **Primary Reference**
- **Repository**: https://github.com/RoboPhred/oni-save-parser
- **Language**: TypeScript/JavaScript
- **Status**: Active, well-maintained
- **Save Version**: 7.17 (Automation Innovation Update)
- **Key Features**:
  - Idempotent load-save cycle (preserves exact binary data)
  - Instruction-based "trampoline" parser for progressive parsing
  - Full TypeScript type definitions
  - Supports both Node.js and web environments

### 2. **SheepReaper's OniSaveParser (.NET)**
- **Repository**: https://github.com/SheepReaper/OniSaveParser  
- **Language**: C# (.NET Standard)
- **Status**: Read-only parser (no serialization yet)
- **Save Version**: 7.11
- **Key Features**:
  - Based on RoboPhred's work
  - .NET serialization approach
  - JSON export capability

## 🏗️ **Save File Structure Analysis**

Based on RoboPhred's implementation, ONI save files have this structure:

```
ONI Save File (.sav)
├── Header
│   ├── Game Version Info
│   ├── Save File Version
│   └── Metadata
├── Type Templates
│   ├── Component Templates
│   └── Behavior Templates  
├── World Data (Binary/Compressed)
├── Settings
│   ├── Game Settings
│   └── World Settings
├── Simulation Data (Binary blob)
├── Game Objects
│   ├── Duplicants (Minions)
│   ├── Buildings  
│   ├── Items
│   └── Other Entities
└── Game Data
    ├── Research Progress
    ├── Statistics
    └── Achievement Data
```

## 🔧 **Technical Implementation Details**

### **Binary Format**
- **Compression**: Uses DEFLATE/zlib compression
- **Encoding**: Mixed binary and string data
- **Byte Order**: Little-endian
- **Data Types**: 
  - Integers (int32, uint32, int64)
  - Floats (single, double)
  - Strings (length-prefixed UTF-8)
  - Arrays (count-prefixed)
  - Nested objects

### **Key Dependencies (JS Version)**
- `pako`: For zlib compression/decompression
- `long`: For 64-bit integer handling
- `text-encoding`: For string encoding/decoding

### **Parser Architecture (RoboPhred)**
- **Trampoline Pattern**: Generator-based parsing for pausable operations
- **Binary Serializer**: Low-level binary read/write operations  
- **Type System**: Strongly typed data structures
- **Validation**: Save version compatibility checks

## 🐍 **Python Implementation Strategy**

### **Recommended Libraries**
```python
# Core binary parsing
import struct          # Binary data unpacking
import zlib           # Compression handling  
import io             # Stream operations

# Enhanced parsing
import dataclasses    # Type-safe data structures
from typing import *  # Type hints
import asyncio        # For progressive parsing (optional)
```

### **Architecture Design**

Based on analysis, our Python parser should follow this structure:

```python
src/oni_ai_agents/services/oni_save_parser/
├── __init__.py
├── binary_reader.py     # Low-level binary operations
├── save_parser.py       # Main parser class  
├── data_structures.py   # SaveGame, GameObject, etc.
├── type_templates.py    # Component/behavior templates
├── compression.py       # Zlib handling
└── version_validator.py # Save compatibility
```

### **Key Implementation Points**

1. **Binary Reader Class**
   ```python
   class BinaryReader:
       def read_int32(self) -> int
       def read_uint32(self) -> int  
       def read_string(self) -> str
       def read_array(self, element_reader) -> List[Any]
   ```

2. **Save Game Structure**
   ```python
   @dataclass
   class SaveGame:
       header: SaveGameHeader
       templates: TypeTemplates
       world: SaveGameWorld
       settings: SaveGameSettings
       sim_data: bytes
       game_objects: GameObjectGroups
       game_data: SaveGameData
   ```

3. **Progressive Parsing** (Optional)
   ```python
   async def parse_save_file(file_path: Path) -> SaveGame:
       # Allow for cancellation and progress reporting
   ```

## 🎯 **Recommended Approach**

### **Phase 1: Core Parser** 
1. **Start Simple**: Focus on basic save file reading and header parsing
2. **Binary Reader**: Implement low-level binary operations based on RoboPhred's approach
3. **Data Structures**: Create Python equivalents of key TypeScript interfaces
4. **Basic Sections**: Parse header, settings, and basic game object data

### **Phase 2: Full Implementation**
1. **Complete Parsing**: All save file sections
2. **Type Templates**: Component and behavior parsing
3. **Validation**: Save version compatibility
4. **Error Handling**: Robust error reporting

### **Phase 3: Integration**
1. **Observer Agents**: Connect to our existing agent system
2. **Caching**: Optimize for repeated parsing
3. **Testing**: Comprehensive test suite with real save files

## 📝 **Next Steps**

1. **Clone RoboPhred's parser locally** ✅
2. **Create basic Python binary reader** 
3. **Implement save file header parsing**
4. **Test with real ONI save files**
5. **Gradually expand to full save parsing**

### Related Roadmap
- For per-section, parallelizable tasks and observer-agent goals, see `docs/Observer_Agent_Section_Roadmap.md`.

## 🔗 **References**

- [RoboPhred's oni-save-parser](https://github.com/RoboPhred/oni-save-parser)
- [SheepReaper's .NET parser](https://github.com/SheepReaper/OniSaveParser)
- [Duplicity - Save Editor](https://github.com/RoboPhred/oni-duplicity)
- [ONI Official Game](https://www.klei.com/games/oxygen-not-included)

---
*Analysis completed: 2025-01-15*
