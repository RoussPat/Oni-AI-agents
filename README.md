# ONI AI Agents System

A multi-agent AI system for playing Oxygen Not Included (ONI) using intelligent agents.

## 🎯 **Project Overview**

This system uses multiple specialized AI agents working together to observe, analyze, and control the Oxygen Not Included game:

- **Observing Agents**: Monitor game state (resources, colony status, threats)
- **Core Agent**: Central decision-making and strategy coordination
- **Commands AI**: Execute specific game actions and interactions

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Observing      │    │     Core        │    │   Commands      │
│   Agents        │───▶│    Agent        │───▶│     AI          │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 **Quick Start**

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd oni_save_parser

# Option A: Use virtualenv (preferred)
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Or install subsets
# Core only
pip install -r requirements/base.txt
# + models (OpenAI/Anthropic adapters)
pip install -r requirements/models.txt
# + vision (Pillow/OpenCV)
pip install -r requirements/vision.txt
# + dev tools (pytest, black, isort, flake8, mypy)
pip install -r requirements/dev.txt

# Option B: Restricted environments (no venv)
# You can run examples/tests that don't require external packages
# or install with: python3 -m pip install --break-system-packages -r requirements.txt
# (not recommended unless you understand the risks)

# Run the basic example
python examples/example_usage.py

# Run the complete hybrid workflow demo
python examples/example_hybrid_workflow.py
```

### Hybrid Workflow Usage

The system uses a **pause-save-analyze-act** approach:

1. **Pause** your ONI game at any point
2. **Save** the game to generate a save file
3. **Analyze** using the AI agents system
4. **Act** on the recommendations (manual or automated)

```python
from src.oni_ai_agents.services.hybrid_workflow import HybridWorkflowManager
from src.oni_ai_agents.agents.resource_observer_agent import ResourceObserverAgent

# Create workflow manager
workflow = HybridWorkflowManager()

# Register specialized agents
resource_agent = ResourceObserverAgent("resource_obs", model_provider="openai")
workflow.register_observer_agent("resources", resource_agent)

# Start analysis session
session_id = await workflow.start_analysis_session(Path("your_save.sav"))

# Get recommendations
recommendations = workflow.get_session_recommendations(session_id)
```

### Basic Usage

```python
import asyncio
from src.oni_ai_agents.core.agent import Agent
from src.oni_ai_agents.core.agent_types import AgentType

# Create an agent with AI model
agent = YourAgent(
    agent_id="my_agent",
    agent_type=AgentType.OBSERVING,
    model_provider="openai",  # or "anthropic", "local"
    model_config={"api_key": "your-api-key"}
)

# Start the agent
await agent.start()

# Process input
result = await agent.process_input({"game_state": {...}})

# Stop the agent
await agent.stop()
```

## 🤖 **Specialized Agent Types**

### Observer Agents
Each observer agent specializes in a specific aspect of colony management:

**Resource Observer**: Monitors food, oxygen, power, materials, and storage
**Duplicant Observer**: Tracks health, skills, morale, assignments, and stress
**Threat Observer**: Detects diseases, temperature issues, pressure problems, and contamination
**Image Observer**: Analyzes base screenshots for visual insights
**Base Layout Observer**: Evaluates building placement and infrastructure (planned)
**Production Observer**: Monitors machines, efficiency, and bottlenecks (planned)

### Core Agent
Central decision-making and strategy:
- Synthesizes data from all observer agents
- Formulates comprehensive strategy
- Prioritizes actions based on colony needs
- Provides strategic recommendations

### Commands AI
Executes game actions (planned):
- Translates strategy into commands
- Handles game interaction mechanics
- Manages building, digging, assignments
- Handles emergency responses

## 🔌 **Model Connectivity**

The system supports multiple AI model providers:

### OpenAI
```python
model_config = {
    "api_key": "your-openai-key",
    "model": "gpt-4",
    "base_url": "https://api.openai.com/v1"  # Optional
}
```

### Anthropic (Claude)
```python
model_config = {
    "api_key": "your-anthropic-key",
    "model": "claude-3-sonnet-20240229"
}
```

### Local (Testing)
```python
model_config = {
    "delay": 0.1,  # Artificial delay
    "responses": {"custom": "response"}  # Predefined responses
}
```

## 📁 **Project Structure**

```
src/oni_ai_agents/
├── core/                     # Core agent classes
│   ├── agent.py             # Base Agent class
│   └── agent_types.py       # Agent type definitions
├── agents/                   # Specialized agent implementations
│   ├── image_observer_agent.py      # Image analysis agent
│   ├── resource_observer_agent.py   # Resource monitoring agent
│   ├── duplicant_observer_agent.py  # Duplicant management agent
│   └── threat_observer_agent.py     # Threat detection agent
├── models/                   # AI model connectivity
│   ├── base_model.py        # Base model interface
│   ├── model_factory.py     # Model factory
│   ├── vision_model_factory.py # Vision model factory
│   ├── openai_model.py      # OpenAI implementation
│   ├── anthropic_model.py   # Anthropic implementation
│   └── local_model.py       # Local testing model
├── services/                 # Business logic services
│   ├── save_file_parser.py  # ONI save file parsing
│   └── hybrid_workflow.py   # Workflow management
├── utils/                    # Utility functions
└── __init__.py

tests/                        # Test files
docs/                         # Documentation
examples/example_hybrid_workflow.py    # Complete workflow demo
```

## 🧪 **Testing**

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with coverage
pytest --cov=src/oni_ai_agents

# If pytest is not available in restricted envs, run selected tests as scripts:
python tests/test_save_simple.py
python tests/test_save_with_agents.py
python tests/test_real_save_parsing.py
```

## 🔧 **Development**

### Code Quality
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Adding New Agents

1. Create a new agent class inheriting from `Agent`
2. Implement the required abstract methods
3. Add tests for your agent
4. Update documentation

```python
class MyCustomAgent(Agent):
    async def process_input(self, input_data):
        # Your custom logic here
        return {"result": "processed"}
    
    async def _on_start(self):
        # Custom startup logic
        pass
    
    async def _on_stop(self):
        # Custom shutdown logic
        pass
    
    async def _process_message(self, message):
        # Custom message processing
        pass
```

## 📚 **Documentation**

- [Project Purpose](PROJECT_PURPOSE.md) - Detailed project goals and architecture
- [Decision Records](DECISIONS.md) - Technical decisions and rationale
- [Cursor Rules](.cursorrules) - Development guidelines
- [Observer Agents & Sections Roadmap](docs/Observer_Agent_Section_Roadmap.md) - Per-section tasks and agent goals

## 🤝 **Contributing**

1. Follow the established code style (see `.cursorrules`)
2. Write tests for new functionality
3. Update documentation
4. Use conventional commits
5. Create feature branches

## 📄 **License**

[Add your license here]

## 🆘 **Support**

For questions or issues, please [create an issue](link-to-issues) or contact the development team. 