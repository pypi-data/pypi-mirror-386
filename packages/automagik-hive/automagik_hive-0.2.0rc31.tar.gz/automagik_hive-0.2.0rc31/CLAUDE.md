# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working with the Automagik Hive repository.

## Context & Scope

[CONTEXT]
- Master playbook for Automagik Hive; every change starts here before entering sub-domain guides.
- Aggregates global guardrails, orchestration rules, and tooling standards enforced across the repo.
- Always cross-reference the relevant domain `CLAUDE.md` after reviewing this document.

[CONTEXT MAP]
@ai/CLAUDE.md
@ai/agents/CLAUDE.md
@ai/teams/CLAUDE.md
@ai/workflows/CLAUDE.md
@ai/tools/CLAUDE.md
@api/CLAUDE.md
@lib/config/CLAUDE.md
@lib/auth/CLAUDE.md
@lib/logging/CLAUDE.md
@lib/mcp/CLAUDE.md
@lib/knowledge/CLAUDE.md
@tests/CLAUDE.md

[SUCCESS CRITERIA]
✅ Behavioral learnings applied before executing tasks.
✅ Domain guides kept in sync; no drift between root instructions and sub-docs.
✅ Every change follows TDD, uv tooling, claude-mcp orchestration, and version bump policies.
✅ Evidence (tests, logs, command output) captured in wish/Forge artifacts.

[NEVER DO]
❌ Skip this document or sub-guides when planning work.
❌ Re-introduce deprecated workflows (workspace scaffolding, manual orchestration).
❌ Use non-uv tooling, bypass approvals, or edit files outside writable roots.
❌ Declare success without documented verification.

## Task Decomposition

```
<task_breakdown>
1. [Discovery] Understand the request
   - Read the active wish or Forge task plus relevant CLAUDE.md sub-guides.
   - Inspect existing code, configs, and tests tied to the change.
   - Confirm sandbox, approval, and tooling constraints.

2. [Implementation] Apply compliant changes
   - Update code + YAML together, bump versions, and document decisions.
   - Use `apply_patch`, `uv` tooling, and claude-mcp orchestration per domain rules.
   - Coordinate specialists (hive-coder, hive-tests, etc.) through Genie.

3. [Verification] Prove the outcome
   - Run targeted `uv run pytest ...` suites and any required commands.
   - Capture evidence (logs, outputs) and attach to the wish/Forge entry.
   - Summarize results in DEATH TESTAMENT before closing the wish.
</task_breakdown>
```

## Behavioral Learnings

[CONTEXT]
- hive-self-learn maintains corrective entries that override any conflicting rule.
- Read current entries before touching code; highest-priority source of truth.

[SUCCESS CRITERIA]
✅ Latest entry acknowledged and applied.
✅ Violations trigger immediate hive-self-learn escalation.
✅ Corrections validated through observable behavior (tests, logs, approvals).

[ENTRY FIELDS]
- `date` — `YYYY-MM-DD` format.
- `violation_type` — exact category name.
- `severity` — `CRITICAL`, `HIGH`, or `MEDIUM`.
- `trigger` — behavior that caused the violation.
- `correction` — required adjustment.
- `validation` — evidence confirming compliance.

## Global Guardrails

### Fundamental Rules *(CRITICAL)*
- Do precisely what is requested—nothing more, nothing less.
- Prefer editing existing files; create new files only when indispensable.
- Never author documentation (`*.md`, README) unless explicitly asked.
- Treat `.claude/commands/prompt.md` as the canonical prompting framework.

### Code Quality Standards
- Remove unnecessary complexity; prefer clear, minimal solutions (KISS/YAGNI/DRY).
- Deliver complete implementations—no placeholders, pseudocode, or stubs.
- Use industry-standard libraries before writing custom alternatives.
- Compose over inherit; only use inheritance for true "is-a" relationships.

### File Organization Principles
- Break work into small, purpose-specific files (target <350 LOC).
- Separate utilities, constants, types, UI, and business logic cleanly.
- Follow existing directory structure and naming conventions.
- Design with reuse and maintainability in mind (well-defined imports/exports).

## Critical Behavioral Overrides

### Time Estimation Prohibition *(CRITICAL)*
- We operate in agent time (seconds/minutes), not human weeks/days.
- Forbidden expressions: "Week 1", "6-week plan", "3 days", "8 hours", any timeline estimates.
- Acceptable alternatives: "Phase 1", "Phase 2", "Core Implementation", "Polish".
- Any time estimate triggers hive-self-learn and counts as a CRITICAL violation.

### UV Compliance Requirement *(CRITICAL)*
- ALL Python commands run through `uv`:
  - `uv run pytest ...`, `uv run python ...`, `uv run coverage ...`.
  - Never call `python`, `pytest`, or `coverage` directly.
- Testing agents must honor uv usage; violations escalate immediately.

### pyproject.toml Protection *(CRITICAL)*
- `pyproject.toml` is read-only: no manual edits, rewrites, or dependency swaps.
- Use `uv add`, `uv add --dev`, `uv lock`, etc. for dependency updates.
- Any direct edit counts as a system integrity breach requiring termination.

## Workspace & Wish System

[CONTEXT]
- `/genie/` is the autonomous planning space, centered on wishes.
- One wish equals one evolving document; DEATH TESTAMENT closes the lifecycle.

[SUCCESS CRITERIA]
✅ Active work lives under `genie/wishes/` with orchestration strategy + final report.
✅ `/wish` command drives planning; updates happen in-place (no v2/v3 files).
✅ DEATH TESTAMENT entries capture evidence, outcomes, and remaining risks.

[NEVER DO]
❌ Recreate the old `reports/` folder or duplicate wish documents.
❌ Start implementation without an orchestration strategy and assigned agents.
❌ Skip DEATH TESTAMENT when declaring a wish complete.

### Directory Layout
- `wishes/` — active planning, orchestration strategy, DEATH TESTAMENT.
- `ideas/` — exploratory thoughts and sketches.
- `experiments/` — throwaway prototypes and spikes.
- `knowledge/` — durable learnings, patterns, and references.

## Strategic Orchestration

### Genie → Domain → Execution
- Master Genie coordinates specialized agents; never performs implementation directly.
- Domain orchestrators (e.g., `genie-dev`, `genie-testing`) spawn `.claude/agents` via claude-mcp.
- Execution layer (`.claude/agents/`) inherits CLAUDE context automatically and follows TDD.

### TDD Pipeline *(Always)*
1. RED – `hive-tests` writes failing tests.
2. GREEN – `hive-coder` implements minimal code to pass.
3. REFACTOR – Improve quality with tests green.

### Forge Workflow *(Delegated Execution)*
- Break wishes into Forge tasks with complete context (`@` references) and agent assignments.
- Escalate zen tools based on complexity (>=7 requires consensus/deep analysis).
- Commit format: `Wish [wish-name]: [specific-change]` with `Co-Authored-By: Automagik Genie <genie@namastex.ai>`.

## Configuration Management

[CONTEXT]
- `--install` command orchestrates `.env` lifecycle; runtime code only reads env vars.
- Maintain strict separation between application configuration and infrastructure overrides.

[SUCCESS CRITERIA]
✅ Install flow reuses valid credentials, regenerates placeholders, and seeds new `.env` files when needed.
✅ `.env` contains runtime settings only; infrastructure values live in compose files.
✅ Documentation and code stay aligned when configuration behavior changes.

[NEVER DO]
❌ Hardcode secrets or environment-specific paths in code/YAML.
❌ Store Docker UID/GID or port mappings inside `.env`.
❌ Diverge from YAML-first approach for static configuration.

### Install Command Design
- If `.env` already has credentials → reuse them.
- If `.env` exists with placeholders → generate and update in place.
- If `.env` is missing → seed from `.env.example` with real credentials.
- Installation commands own environment setup; runtime code consumes the result.

### Configuration Architecture
- `.env` → runtime settings: database URLs, API keys, application configuration.
- `docker-compose.yml` → infrastructure settings: permissions, port mappings, volume mounts.
- Use `${VAR:-default}` in compose; apply overrides via shell or `docker-compose.override.yml`.

## Project Architecture

[CONTEXT]
- Provides navigation and orientation for the repository structure.
- Use before large changes to confirm component locations and dependencies.

[SUCCESS CRITERIA]
✅ Navigational commands (`tree`, etc.) reflect current project layout.
✅ Architecture map stays synchronized with actual directories/files.
✅ New components documented via the relevant domain guide.

[NEVER DO]
❌ Introduce undocumented top-level directories.
❌ Leave architecture map outdated after structural changes.

### Exploration Command
```bash
# Explore codebase without noise
tree -I '__pycache__|.git|*.pyc|.venv|data|logs|.pytest_cache|*.egg-info|node_modules|.github|genie|scripts|common|docs|alembic'      -P '*.py|*.yaml|*.yml|*.toml|*.md|Makefile|Dockerfile|*.ini|*.sh|*.csv|*.json' --prune -L 4
```

### Architecture Map
```
🧭 NAVIGATION ESSENTIALS
├── pyproject.toml              # Project dependencies (managed via UV)

🤖 MULTI-AGENT CORE (Start Here for Agent Development)
├── ai/
│   ├── agents/registry.py      # 🏭 Agent factory - loads all agents
│   │   └── template-agent/     # 📋 Copy this to create new agents
│   ├── teams/registry.py       # 🏭 Team factory - routing logic
│   │   └── template-team/      # 📋 Copy this to create new teams
│   └── workflows/registry.py   # 🏭 Workflow factory - orchestration
│       └── template-workflow/  # 📋 Copy this to create new workflows

🌐 API LAYER (Where HTTP Meets Agents)
├── api/
│   ├── serve.py                # 🚀 Production server (Agno FastAPIApp)
│   ├── main.py                 # 🛝 Dev playground (Agno Playground)
│   └── routes/v1_router.py     # 🛣️ Main API endpoints

📚 SHARED SERVICES (The Foundation)
├── lib/
│   ├── config/settings.py      # 🎛️ Global configuration hub
│   ├── knowledge/              # 🧠 CSV-based RAG system
│   │   ├── knowledge_rag.csv   # 📊 Data goes here
│   │   └── csv_hot_reload.py   # 🔄 Hot reload magic
│   ├── auth/service.py         # 🔐 API authentication
│   ├── utils/agno_proxy.py     # 🔌 Agno framework integration
│   └── versioning/             # 📦 Component version management

🧪 TESTING (tests/ directory – expand scenarios alongside every new feature)
```

## Development Methodology

[CONTEXT]
- Red-green-refactor is mandatory for all feature work.
- Testing precedes implementation; refactors happen with green tests.

[SUCCESS CRITERIA]
✅ Each cycle starts with failing tests from `hive-tests`.
✅ Implementation limited to satisfy tests before refactoring.
✅ Refactor stage retains green status and updates documentation.

[NEVER DO]
❌ Spawn `hive-coder` before failing tests exist.
❌ Skip refactor stage when design smells persist.
❌ Leave orchestration strategy undocumented in the wish.

### TDD Cycle
1. **RED** – `Task(subagent_type="hive-tests", prompt="Create failing test suite for [feature]")`
2. **GREEN** – `Task(subagent_type="hive-coder", prompt="Implement [feature] to make tests pass")`
3. **REFACTOR** – Improve structure while tests stay green.

**Strict Rule** — never dispatch `hive-coder` without prior failing tests from `hive-tests`.

## Development Workflow & Tooling

[CONTEXT]
- All development/testing occurs through `apply_patch`, uv tooling, and controlled shell access.

### Server Management
- `Bash(command="make dev", run_in_background=True)` — start dev server.
- `tail -f logs/server.log` / `curl http://localhost:8886/api/v1/health` — monitor.
- `make stop` → graceful shutdown; `pkill -f "uvicorn"` if forced.

### UV Commands
```bash
uv sync                     # Install/sync dependencies
uv add <package>            # Add runtime dependency (never pip install)
uv add --dev <package>      # Add dev dependency
uv run ruff check --fix     # Lint & auto-fix
uv run mypy .               # Type checking
uv run pytest               # Full suite entry point
uv run pytest tests/ai/agents/      # Agent coverage
uv run pytest tests/ai/workflows/   # Workflow coverage
uv run pytest tests/api/            # API coverage
uv run pytest --cov=ai --cov=api --cov=lib  # Coverage report
```

### Evidence Requirements
- Attach command output or summaries in wish/Forge records.
- Ensure git status clean aside from intentional changes.
- Never claim success without recorded verification steps.

## Development Standards

### Core Principles
- Write simple, focused code that solves current needs (KISS/YAGNI/DRY).
- Apply SOLID principles where relevant; favor composition over inheritance.
- Use industry-standard libraries before inventing custom ones.
- Break backward compatibility when cleaner modern implementations exist.
- Remove legacy shims immediately; keep implementations clean.
- Make side effects explicit and minimal.
- Evaluate ideas honestly; discard weak approaches quickly.

### Quality Requirements
- Every new agent ships with unit and integration tests.
- Use the CSV-based RAG system with hot reload for context-aware responses.
- Never hardcode values—pull configuration from `.env` files and YAML configs.

## Domain Playbooks

Use these guides alongside the root playbook:
- `ai/CLAUDE.md` — Multi-agent orchestration overview.
- `ai/agents/CLAUDE.md` — Domain orchestrator agents.
- `ai/teams/CLAUDE.md` — Routing and coordination teams.
- `ai/workflows/CLAUDE.md` — Step-based workflows.
- `ai/tools/CLAUDE.md` — Reusable tool architecture.
- `api/CLAUDE.md` — FastAPI exposure and deployment.
- `lib/config/CLAUDE.md` — Global configuration hierarchy.
- `lib/auth/CLAUDE.md` — Authentication and message validation.
- `lib/logging/CLAUDE.md` — Structured logging and emoji system.
- `lib/mcp/CLAUDE.md` — Model Context Protocol integrations.
- `lib/knowledge/CLAUDE.md` — CSV-based RAG system.
- `tests/CLAUDE.md` — Testing strategy and coverage expectations.

## MCP Tooling

[CONTEXT]
- Model Context Protocol connects external services (WhatsApp, Postgres, etc.) to Automagik Hive.
- `.mcp.json` is the single source of truth for server definitions.

### Available Tools
- **postgres** *(Working)* — Direct SQL queries on the main DB (port 5532). Example: `SELECT * FROM hive.component_versions`.
- **automagik-hive** *(Auth Required)* — API interactions for agents, teams, workflows (`HIVE_API_KEY`).
- **automagik-forge** *(Working)* — Project/task management; list or update Forge tasks.
- **search-repo-docs** *(Working)* — External docs such as Agno (`/context7/agno`).
- **ask-repo-agent** *(Requires Indexing)* — GitHub repo Q&A for Agno/external sources.
- **wait** *(Working)* — Workflow delays (e.g., `wait_minutes(0.1)`).
- **send_whatsapp_message** *(Working)* — External notifications; double-check recipients/content.

### Database Schema Reference
```sql
-- Main system database (postgresql://localhost:5532/automagik_hive)

-- agno schema
agno.knowledge_base         -- Vector embeddings for RAG system
  ├── id, name, content    -- Core fields
  ├── embedding (vector)   -- pgvector embeddings
  └── meta_data, filters   -- JSONB for filtering

-- hive schema
hive.component_versions     -- Agent/team/workflow versioning
  ├── component_type       -- 'agent', 'team', 'workflow'
  ├── name, version        -- Component identification
  └── modified_at          -- Version tracking

-- Example queries:
SELECT * FROM hive.component_versions WHERE component_type = 'agent';
SELECT * FROM agno.knowledge_base WHERE meta_data->>'domain' = 'development';
```

### Usage Workflow
1. Query current state via `postgres` before making changes.
2. Document strategy in Automagik Forge tasks prior to execution.
3. Take actions only with explicit user approval.
4. Ensure the development server is running (`Bash(.., run_in_background=True)`).
5. Bump YAML version numbers whenever configuration changes occur.

### Best Practices
- Inspect current state first; never modify blind.
- Secure user approval for planned work and features.
- Report critical issues, bugs, and blockers automatically.
- Wrap DB changes in `BEGIN; ... COMMIT/ROLLBACK;` transactions.
- Record significant actions in Automagik Forge for auditing.
- Pace bulk operations with waits to respect rate limits.
- Maintain fallback strategies (API → DB → in-memory).

### Safety Rules
- `postgres`: Read-only queries unless explicitly authorized.
- `automagik_forge`: Track decisions and progress inside tasks.
- `send_whatsapp_message`: Confirm recipients and message content before sending.
- Version bumps are mandatory for any config change performed via tools.

### Troubleshooting
- **Auth issues**
  ```bash
  cat .env | grep HIVE_API_KEY  # Verify API key exists
  # If missing, check with user or use postgres as fallback
  ```
- **Connection issues**
  - Run `make stop`, then restart with `Bash("make dev", run_in_background=True)`.
  - Main API served at `http://localhost:8886`.

## Forge Integration Patterns

[CONTEXT]
- Forge coordinates cross-instance execution; use it for handoffs, task creation, and orchestration workflows.

### Workflow Integration
- **Phases**
  1. **Brainstorm:** Apply zen tools for complex analysis and architecture.
  2. **Document:** Produce PRDs and wish planning documents.
  3. **Plan:** Break wishes into implementable components.
  4. **Execute:** Create Forge tasks for autonomous work.
- **Task Creation Standards**
  - Create tasks directly in Forge—skip intermediate task files.
  - Provide complete context using `@` references to wish documents.
  - Assign agents and enable zen auto-escalation for complexity ≥7.
  - Choose branch strategy based on complexity assessment.
- **Forge Task Template**
  ```
  AUTOMAGIK FORGE EXECUTION TASK
  =============================

  WISH: [wish-name]
  TASK: [task-name]
  COMPLEXITY: [1-10]
  BRANCH: [dev|feature/wish-name]

  COMPLETE CONTEXT:
  - PRD: @/genie/wishes/[wish-name]/prd.md
  - Wish Plan: @/genie/wishes/[wish-name]/wish.md
  - Architecture: @/genie/wishes/[wish-name]/context/architecture.md
  - Project Patterns: @/CLAUDE.md

  PRIMARY AGENT: @[hive-coder|hive-tests|hive-dev-fixer]
  SUPPORT AGENTS: @[additional-agents] (if parallel streams needed)

  ZEN TOOLS AVAILABLE (auto-escalate complexity 7+):
  - /mcp__zen__debug - Systematic debugging
  - /mcp__zen__codereview - Quality assurance
  - /mcp__zen__testgen - Test strategy
  - /mcp__zen__refactor - Code optimization

  EXECUTION REQUIREMENTS:
  [Detailed task description from wish breakdown]

  SUCCESS CRITERIA:
  [Acceptance criteria from task spec]

  QUALITY GATES:
  - [ ] All tests passing
  - [ ] Code review completed (zen tools if complex)
  - [ ] Documentation updated
  - [ ] No merge conflicts
  - [ ] Progress updated
  ```

### Complexity Assessment
- **Scoring Algorithm**
  - *1–3:* Single-file changes, bug fixes, documentation tweaks.
  - *4–5:* Multi-file features, moderate refactoring, new components.
  - *6–7:* New subsystems, significant architecture, complex features.
  - *8–10:* Full system redesigns, platform changes, major rewrites.
- **Zen Tool Integration**
  - Complexity 1–3: execute directly with minimal zen usage.
  - Complexity 4–6: leverage zen tools strategically for validation.
  - Complexity 7–10: require multi-model consensus and deep analysis.
- **Branch Strategy**
  - Simple work → stay on `dev`.
  - Complex work → create `feature/wish-[kebab-case-name]`.

### Commit Standards
- Format commits as `Wish [wish-name]: [specific-change]`.
- Always add `Co-Authored-By: Automagik Genie <genie@namastex.ai>`.
- Ensure changes are committed before creating the Forge task.

### Security Integration
- Auto-trigger security review for complexity ≥6 or sensitive areas (auth, payments, data handling).
- Run comprehensive audits: OWASP Top 10, relevant compliance (SOC2, PCI DSS, HIPAA, GDPR), threat modeling, infrastructure review.
- Use `/mcp__zen__secaudit` for systematic security assessments.

## Verification & Reporting

[SUCCESS CRITERIA]
✅ Every change linked to a wish/Forge task with documented plan and validation.
✅ Tests + commands executed through uv tooling and recorded in DEATH TESTAMENT.
✅ Behavioral learnings incorporated; no out-of-date instructions linger.
✅ Domain guides remain synchronized—update sub-doc when root policy changes.

[NEVER DO]
❌ Merge or hand off work without recorded evidence.
❌ Modify domain guides without updating root references.
❌ Ignore failure output or flaky tests; resolve before completion.

Stay aligned with this playbook and the domain-specific CLAUDE guides to keep Automagik Hive predictable, test-driven, and safely orchestrated.
