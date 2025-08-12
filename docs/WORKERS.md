### Workers guide (concise)

This repo uses manager-issued briefs to coordinate up to 4 workers in parallel. Keep replies short, high-signal, and CI-safe.

#### Roles
- Manager: splits work, defines acceptance criteria, merges, keeps CI green.
- Workers: implement only what’s in scope; keep edits minimal and lint/CI clean.

#### Workflow
1) Initial assignment (from manager)
   - Title, branch or trunk note, objective, deliverables, acceptance, commands.
2) Delivery reply (from worker)
   - Status, changes, how to run, acceptance met, branch/commit ref.

#### Git policy
- The manager owns branches, commits, merges, and release tagging.
- Workers should NOT perform git/branch operations unless explicitly assigned.
- Deliver work as minimal file edits or diffs; keep scope tight.
- If you already opened a PR, share the link and branch name, then pause further commits until review.
- Default is trunk-based flow; use feature branches only when specified in the brief.

#### Prompt templates

Initial assignment:
```
Title: <short>
Branch/Trunk: <branch-name or trunk>
Objective: <what and why>
Deliverables: <files/edits>
Acceptance: <tests/criteria>
Commands: <how to run & lint>
```

Delivery reply:
```
Status: <done/notes>
Changes: <key edits + files>
How to run: <commands>
Acceptance: <how criteria are met>
Branch/Commit: <ref>
```

#### CI and quality gates
- Tests: `python -m pytest -q`
- Lint/format: `python -m black . && python -m isort . && python -m flake8`
- Keep edits scoped; avoid reformatting unrelated code.

#### Local model runtime (quick)
- Preferred for dev: Ollama OpenAI endpoint in WSL on 11435.
- Env for examples/agents:
```
OPENAI_BASE_URL=http://127.0.0.1:11435/v1
OPENAI_MODEL=gpt-oss:20b
OPENAI_FORCE_CHAT=1
PYTHONPATH=.
```
- Scripts (when available): `scripts/wsl_ollama_start.sh`, `scripts/wsl_ollama_pull.sh`.

#### Decision records
- Record roadmap-impacting choices in `DECISIONS.md`, ≤5 lines per entry [[memory:5491893]] [[memory:5491888]].

#### Notes
- Prefer trunk-based flow when asked; otherwise use small feature branches.
- Keep examples CI-safe (exit 0 when external services are missing).

---

All future manager prompts to workers follow this guide. Workers should reference `docs/WORKERS.md` in their replies for scope, acceptance, and commands.


