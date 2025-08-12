# Decision Records

This document tracks important architectural and technical decisions made during the project development.

## 📋 **Decision Record Format**

Each decision follows this format:
- **Date**: When the decision was made
- **Context**: What problem we were solving
- **Decision**: What we decided
- **Rationale**: Why we made this choice
- **Alternatives**: What we considered but didn't choose
- **Consequences**: What this decision means for the project

---

## 🧰 Environment & Tooling Constraints
**Date**: 2025-08-10
**Context**: CI/dev container restricts system installs; PEP 668 blocks pip writes.
**Decision**: Document venv-first setup; provide restricted-env fallbacks and scriptable test entrypoints; remove unnecessary `asyncio` dependency; add `pyproject.toml` for tooling.
**Consequences**: Reliable local setup; tests/examples runnable without admin; standardized formatting.

---

## 🧪 Continuous Integration Setup
**Date**: 2025-08-10  
**Context**: Need automated quality gates for PRs and main.  
**Decision**: Add GitHub Actions CI with Python 3.11/3.12 matrix: install split requirements, run black/isort/flake8, run pytest, and upload `pip freeze` as lock artifact (`requirements/lock-py311.txt`).  
**Alternatives**: Single-version CI (less coverage), local-only checks (no automation).  
**Consequences**: Early breakage detection; consistent code quality; artifact available for pinning.

---

## 📦 Requirements Extras Split
**Date**: 2025-08-10  
**Context**: Heavy deps (vision/models) not always needed; dev tools separate.  
**Decision**: Split into `requirements/base.txt`, `requirements/models.txt`, `requirements/vision.txt`, `requirements/dev.txt`; aggregate via root `requirements.txt`.  
**Alternatives**: Single monolithic file (slower installs), optional extras via setup.py (out of scope).  
**Consequences**: Faster, targeted installs; simpler CI steps; clearer dependency boundaries.

---

## 🔒 Version Pinning Policy
**Date**: 2025-08-10  
**Context**: Ensure reproducible builds after CI green.  
**Decision**: After CI is green on main, promote the `requirements/lock-py311.txt` artifact to a tracked lock file (e.g., `requirements/locked.txt`) and/or update split files with pinned versions. Trigger via manual step/PR.  
**Alternatives**: Always pin (less flexibility), never pin (non-reproducible).  
**Consequences**: Stable builds; controlled updates; clear workflow for dependency changes.

---
## 🐍 **Language Selection**

**Date**: 2025-08-07 19:50  
**Context**: Need primary language for ONI AI agent system with game parsing, real-time processing, and AI/ML capabilities.  
**Decision**: **Python 3.11+** - Rich AI ecosystem, game automation tools, async/await for multi-agent coordination.  
**Alternatives**: Java (weaker AI ecosystem), C++ (slower dev), Rust (immature AI).  
**Consequences**: ✅ Rapid development, ✅ AI/ML libraries, ✅ Game integration. ⚠️ May need performance optimization.

---

## 🏗️ **Architecture Pattern**

**Date**: 2025-08-07 19:50  
**Context**: Need architectural pattern for multi-agent system code organization.  
**Decision**: **Clean Architecture** - Clear separation of concerns, testability, flexibility for swapping implementations.  
**Alternatives**: Monolithic (harder to test), Microservices (overkill), Event-Driven (adds complexity).  
**Consequences**: ✅ Clear organization, ✅ Easy testing, ✅ Flexible swapping. ⚠️ More setup, ⚠️ Need to maintain boundaries.

---

## 🎯 **Development Approach**

**Date**: 2025-08-07 19:50  
**Context**: Need to define development approach for complex multi-agent system.  
**Decision**: **Incremental Development** with POC-first approach - build and test components incrementally.  
**Alternatives**: Big Bang (high risk), Waterfall (inflexible for experimentation).  
**Consequences**: ✅ Lower risk, ✅ Early validation, ✅ Easy adaptation. ⚠️ May need refactoring, ⚠️ Need to maintain focus.

---

## 📚 **Documentation Strategy**

**Date**: 2025-08-07 19:50  
**Context**: Need to decide how to document the system and track decisions.  
**Decision**: **Decision Records** (ADR format) and comprehensive inline documentation for traceability and knowledge sharing.  
**Alternatives**: No formal tracking (lose context), Wiki approach (less structured).  
**Consequences**: ✅ Clear history, ✅ Better onboarding, ✅ Professional practices. ⚠️ Requires discipline, ⚠️ Documentation overhead.

---

## 🤖 **Agent Flow Implementation**

**Date**: 2025-08-07 20:10  
**Context**: Need to implement end-to-end agent communication flow with three agent types (Observing, Core, Commands).  
**Decision**: **Implemented complete agent flow** with message passing, AI model integration, and comprehensive testing.  
**Alternatives**: Synchronous processing (no async), direct function calls (no message passing), single agent (no separation).  
**Consequences**: ✅ Full agent communication working, ✅ AI model integration successful, ✅ All tests passing. ✅ Ready for game integration.

---

## 🖼️ **Image Observer Agent Implementation**

**Date**: 2025-08-07 21:30  
**Context**: Need observer agent that takes PNG images and returns text summaries for core agent analysis.  
**Decision**: **Implemented ImageObserverAgent** with vision model factory, comprehensive testing, and multiple input formats (base64, bytes, file path).  
**Alternatives**: Complex computer vision pipeline (overkill), direct API calls (no abstraction), single model provider (less flexible).  
**Consequences**: ✅ Simple image-to-text conversion, ✅ Multiple AI providers supported, ✅ 17/17 tests passing, ✅ Ready for integration.

---

## 💾 **Save File Integration Strategy**

**Date**: 2025-01-15  
**Context**: Need to decide how to integrate ONI save file data and manage real-time vs batch processing.  
**Decision**: **Hybrid pause-save-analyze approach** with specialized observer agents for different save file sections.  
**Alternatives**: Real-time integration (too complex), pure automation (less control), manual analysis (not scalable).  
**Consequences**: ✅ Manageable complexity, ✅ Human oversight, ✅ Incremental automation. ⚠️ Requires save file parsers, ⚠️ Manual intervention needed.

---

## 🔍 **Observer Agent Specialization**

**Date**: 2025-01-15  
**Context**: Need to define how observer agents will analyze different aspects of ONI save files and images.  
**Decision**: **Dedicated specialized observers** - each agent covers specific save file sections plus image-based base analysis.  
**Alternatives**: Single observer (too complex), manual analysis (not scalable), generic observers (less detailed).  
**Consequences**: ✅ Focused expertise, ✅ Detailed analysis, ✅ Modular system. ⚠️ More agents to manage, ⚠️ Need coordination.

---

## 💰 **AI Model Cost Strategy**

**Date**: 2025-01-15  
**Context**: Need to balance AI model capabilities with cost considerations for different system components.  
**Decision**: **Tiered model approach** - GPT-4 for specialized summaries, GPT-5 for image-to-text, cost-effective models for core decisions.  
**Alternatives**: Single premium model (expensive), all cheap models (less capable), no AI (defeats purpose).  
**Consequences**: ✅ Optimized costs, ✅ Right tool for job, ✅ Scalable approach. ⚠️ Multiple API management, ⚠️ Cost monitoring needed.

---

*Last Updated: 2025-01-15* 

---

## 🧩 Save Parser Roadmap (Phase 1)
**Date**: 2025-08-09  
**Context**: Gaps vs research parsers (JS 7.17, .NET 7.11).  
**Decision**: Implement compression/section framing, type templates, game object/component parsing; keep world/sim preserved; add writer.  
**Consequences**: Real section data for agents; round-trip tests; enables accurate analyses.

## 🔢 Version Support Policy
**Date**: 2025-08-09  
**Context**: Real saves report minor 36; previous range capped at 17 causing warnings.  
**Decision**: Update supported minor range to 36; continue warning only when outside 11–36.  
**Consequences**: No false warnings on current game; expectations aligned with latest version.

## 📦 Data Extraction Contract
**Date**: 2025-08-09  
**Context**: Sections return placeholders (resources/duplicants/threats).  
**Decision**: Define exact keys and fill from parsed components (food, oxygen, power, skills, stress, diseases).  
**Consequences**: Stable API for agents; facilitates incremental parsing.

## 🧵 Parsing Architecture Choice
**Date**: 2025-08-09  
**Context**: JS uses instruction-based trampoline with progress.  
**Decision**: Adopt incremental parsing with progress hooks; optional coroutine-style iterator later.  
**Consequences**: Better UX, cancellation, and testability; non-breaking to start.

## 🌍 World/Sim Handling Strategy
**Date**: 2025-08-09  
**Context**: World/sim complex; both repos largely preserve.  
**Decision**: Preserve as-is; parse framing/metadata and sizes; expose sizes/checksums.  
**Consequences**: Safe handling now; room to deepen later without blocking.

---

## 👥 Duplicant Data Parsing Roadmap (Phase 1.1)
**Date**: 2025-08-09  
**Context**: Positions and basic identity extracted; need richer info.  
**Decision**: Implement minimal template reads for MinionIdentity/MinionResume/MinionModifiers to get name, job/role, skills, vitals.  
**Consequences**: Accurate names, jobs, skills, and vitals; removes heuristics.

---

## ❤️ Vitals Extraction Strategy
**Date**: 2025-08-09  
**Context**: Current vitals are heuristic scans.  
**Decision**: Parse AmountInstance values (calories/health/stress/stamina) via template subset; fall back omitted.  
**Consequences**: Reliable vitals; consistent units; ready for observer agents.

---

## 🧠 Skills and Roles Plan
**Date**: 2025-08-09  
**Context**: Need skills/aptitudes and current role for agents/UI.  
**Decision**: Read MinionResume (MasteryByRoleID, AptitudeBySkillGroup, currentRole); expose in entities.  
**Consequences**: Actionable crew insights; supports recommendations.

---

## 🏷️ Name Resolution Policy
**Date**: 2025-08-09  
**Context**: Name heuristics can mislabel.  
**Decision**: Prefer concrete `name` in MinionIdentity; avoid `nameStringKey`; drop heuristics once templates land.  
**Consequences**: Stable, correct duplicant names.

---

## 📜 Observer Sections Roadmap Adopted
**Date**: 2025-08-09  
**Decision**: Adopt per-section observer roadmap and stable v0.1 data contracts.  
**Rationale**: Enables parallel parsing and agent workstreams.  
**Consequences**: Teams can implement independently; core agent receives richer, consistent inputs.  

## 👔 AI PM + Worker Model (Save Parser Focus)
**Date**: 2025-08-10  
**Decision**: Use concise worker briefs (prompts) to run parallel tasks confined to save-file parsing; track outcomes here.  
**Consequences**: Faster parallel progress, clear acceptance criteria, and consistent adherence to repo guidelines.

## 🧪 OpenAI Local Runtime Testability
**Date**: 2025-08-11  
**Decision**: Add offline tests with a fake `AsyncOpenAI` to cover `responses` and `chat.completions` paths; allow local `base_url` without API key and return stub when unavailable.  
**Consequences**: Tests run with no network; local OpenAI-compatible servers supported via config; wiring verified.

## 🧪 Local OpenAI-Compatible GPT-OSS Runtime
**Date**: 2025-08-11  
**Decision**: Add example and docs for running a local OpenAI-compatible GPT-OSS server; adopt `OPENAI_BASE_URL`/`OPENAI_MODEL` envs.  
**Consequences**: Enables offline/dev testing with OSS models; CI-safe example that exits cleanly when server is absent.

## 🧩 Local GPT-OSS via Ollama
**Date**: 2025-08-11  
**Decision**: Document WSL-based Ollama setup; recommend chat-completions fallback via `OPENAI_FORCE_CHAT=1`.  
**Consequences**: Works with Ollama’s OpenAI-compatible endpoint; predictable behavior across compat servers.

## 🔌 OpenAI Local Runtime Support
**Date**: 2025-08-11  
**Decision**: `OpenAIModel` reads `base_url` from config or env; if set, instantiate real `AsyncOpenAI` with `api_key` or `"EMPTY"`. Add `openai_local` alias in `ModelFactory`.  
**Consequences**: Agents can use local OpenAI-compatible servers without API keys; Responses and Chat Completions work.

## 🧪 GPT-OSS Local Runtime (Docker)
**Date**: 2025-08-11  
**Decision**: Add vLLM-based compose `runtime/docker-compose.gpt-oss.yml`, Windows scripts to download models and run locally; `.env` vars `OPENAI_BASE_URL`/`OPENAI_MODEL`.  
**Consequences**: Reproducible local GPT-OSS via OpenAI API at `http://localhost:8000/v1`; no Python code changes needed to start/stop.

## ♻️ Save Parser Modularization Facade v0.1
**Date**: 2025-08-10
**Decision**: Extract cohesive responsibilities from `save_parser.py` into small modules: `header_reader.py`, `compressed_blocks.py`, `ksav_index.py`, `duplicant_decoder.py`, `metadata_builder.py`; keep `OniSaveParser` as a thin orchestrator.
**Rationale**: Reduce edit contention, enable parallel workstreams (header/metadata, KSAV counts, duplicants, CLI) without touching `save_parser.py`.
**Consequences**: No functional changes; tests remain green; downstream workers can implement features in dedicated files.

