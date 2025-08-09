# ONI AI Agent System - Project Purpose

## 🎯 **Project Overview**

We are building a comprehensive system of AI agents to play **Oxygen Not Included (ONI)**. The system will use multiple specialized AI agents working together to observe, analyze, and control the game.

## 🏗️ **System Architecture**

### **Multi-Agent Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Observing      │    │     Core        │    │   Commands      │
│   Agents        │───▶│    Agent        │───▶│     AI          │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Game State     │    │  Strategy &     │    │   Game          │
│  Information    │    │  Decision       │    │  Interaction    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🤖 **Agent Types & Responsibilities**

### **1. Observing Agents**
- **Purpose**: Monitor different aspects of the game state
- **Responsibilities**:
  - Resource monitoring (food, oxygen, power, etc.)
  - Colony status tracking (duplicant health, morale, skills)
  - Base layout analysis
  - Threat detection (disease, heat, etc.)
  - Production efficiency monitoring

### **2. Core Agent**
- **Purpose**: Central decision-making and strategy coordination
- **Responsibilities**:
  - Analyze data from observing agents
  - Formulate overall strategy
  - Prioritize actions and goals
  - Coordinate between different game systems
  - Make high-level decisions

### **3. Commands AI**
- **Purpose**: Execute specific game actions
- **Responsibilities**:
  - Translate strategy into specific commands
  - Handle game interaction mechanics
  - Execute building, digging, and management tasks
  - Manage duplicant assignments
  - Handle emergency responses

## 🔄 **Information Flow**

1. **Observation Phase**: Multiple observing agents gather game state data
2. **Analysis Phase**: Core agent processes and analyzes the information
3. **Strategy Phase**: Core agent formulates strategy and priorities
4. **Execution Phase**: Commands AI translates strategy into game actions
5. **Feedback Loop**: Results feed back to observing agents

## 🧪 **Experimental Approach**

### **Strategy Testing**
- We will experiment with different strategies for:
  - What information to feed to observing agents
  - How to structure the data for the core agent
  - Decision-making algorithms and priorities
  - Command execution patterns

### **Gradual Development**
- Build functionalities incrementally
- Start with basic observation capabilities
- Add decision-making logic progressively
- Test and refine each component before moving to the next
- Focus on POC functionality first, then expand

## 🎮 **Game Integration**

### **Data Sources**
- Game save files (ONI save format)
- Real-time game state monitoring
- Historical game data analysis
- Performance metrics tracking

### **Command Execution**
- Game automation tools
- API integration (if available)
- Macro and script execution
- Direct game interaction

## 📈 **Success Metrics**

- **Colony Survival**: How long can the AI maintain a stable colony?
- **Efficiency**: Resource optimization and production rates
- **Adaptability**: Response to unexpected events and challenges
- **Learning**: Improvement over multiple game sessions
- **Strategy Effectiveness**: Different approaches and their outcomes

## 🚀 **Development Phases**

### **Phase 1: Foundation**
- Basic game state parsing
- Simple observing agent
- Core agent framework
- Basic command execution

### **Phase 2: Intelligence**
- Multiple observing agents
- Advanced decision-making
- Strategy implementation
- Performance optimization

### **Phase 3: Advanced Features**
- Machine learning integration
- Adaptive strategies
- Complex scenario handling
- Long-term planning

---

*This document serves as our north star - keeping us focused on the ultimate goal while we build incrementally.* 