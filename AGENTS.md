# AGENTS.md — LinkedIn Post Master

## Project Overview

- **Name**: PostCraft AI — LinkedIn Content Studio
- **Stack**: React SPA (frontend) + FastAPI (backend) + Anthropic Claude API + Redis
- **Purpose**: AI-powered LinkedIn post generation with multi-input synthesis and engagement optimization
- **Repo**: `linkedin-post-master`
- **Branch for overnight work**: `overnight/run-1`

---

## Agent System

This project uses the **BMAD** agent system. Agents are defined in `_bmad/bmm/agents/` and invoked via skill names.

### Available Agents

### Available Agents (14 total)

| Skill | Display Name | Role |
|---|---|---|
| `bmad-team-lead` | Rae | Team Lead Orchestrator — coordinates the full development pipeline, dispatches agents per task |
| `bmad-dev` | Amelia | Senior Software Engineer — story execution, TDD, code implementation |
| `bmad-qa` | Quinn | QA Engineer — API/E2E test generation, coverage analysis |
| `bmad-pr-supervisor` | Alex | PR Supervisor — runs two senior reviewers in parallel, aggregates findings into unified verdict |
| `bmad-pr-review` | Alex | PR Review Agent — adversarial code review across correctness, security, performance, maintainability |
| `bmad-arch-review` | Winston | Architecture Review Agent — technical debt, scalability, API design evaluation |
| `bmad-adversarial` | Skyler | Adversarial Review Agent — critical analysis, assumption surfacing, failure scenarios |
| `bmad-security` | Kira | Security Review Agent — OWASP Top 10, CVE auditing, auth flows, penetration testing |
| `bmad-pm` | — | Product Manager — scoping, prioritization, roadmapping |
| `bmad-analyst` | — | Analyst — requirements breakdown, story creation |
| `bmad-architect` | Winston | Architect — technical design, architecture decisions |
| `bmad-sm` | — | Scrum Master — sprint planning, retrospectives |
| `bmad-tech-writer` | — | Tech Writer — documentation, READMEs, CONTRIBUTING guide |
| `bmad-ux-designer` | — | UX Designer — design specs, UX planning |

### Agent Activation

Each agent is invoked via its skill name:

```
bmad-team-lead    → invoke team lead (Rae) — orchestrator
bmad-dev          → invoke dev agent (Amelia)
bmad-qa           → invoke qa agent (Quinn)
bmad-pr-supervisor → invoke PR supervisor (Alex) — spawns parallel sub-reviewers
bmad-pr-review    → invoke PR review agent (Alex)
bmad-arch-review  → invoke architecture review (Winston)
bmad-adversarial  → invoke adversarial agent (Skyler)
bmad-security     → invoke security agent (Kira)
bmad-pm           → invoke pm agent
bmad-analyst      → invoke analyst agent
bmad-architect    → invoke architect (Winston)
bmad-sm           → invoke sm agent
bmad-tech-writer  → invoke tech-writer agent
bmad-ux-designer  → invoke ux-designer agent
```

Agent menu items include `PM` (party mode — all agents active simultaneously) and `OR` (overnight run — full automated pipeline).

---

## Task Queue

**File**: `docs/tasks/overnight.md`
**Total tasks**: 75 across 7 tracks
**Execution order**: B → A → C+D → E → F → G

| Track | Tasks | Description |
|---|---|---|
| B | 8 | Bug fixes |
| A | 15 | Frontend design consistency (Tailwind app-wide) |
| C | 12 | Backend features |
| D | 10 | Missing feature implementation |
| E | 10 | Test coverage gaps |
| F | 5 | Documentation + DevOps |
| G | 15 | Comprehensive security review |

---

## Pipeline Flow

The full development pipeline runs per task in this order:

```
TASK QUEUE (docs/tasks/overnight.md)
        │
        ▼
   ┌─────────────┐
   │  TEAM LEAD  │  ← picks next unmarked task
   │   (Rae)     │
   └──────┬──────┘
          │ dispatches
          ▼
   ┌─────────────┐
   │  ARCHITECT  │  ← pre-flight: checks existing code + new task
   │  (Winston)  │    for architecture fit; raises concerns before code is written
   └──────┬──────┘
          │ clears
          ▼
   ┌─────────────┐
   │    DEV      │  ← writes code + tests per task
   │  (Amelia)   │
   └──────┬──────┘
          │ passes
          ▼
   ┌──────────────────────┐
   │    PR SUPERVISOR     │  ← spawns TWO parallel subagents:
   │       (Alex)         │    Subagent A (correctness)   ─┐
   │                       │    Subagent B (sec+perf)      ─┤
   └──────┬────────────────┘                               ─┘
          │ aggregates findings
          ▼
   ┌─────────────┐
   │  ADVERSARIAL │  ← edge cases, failure scenarios,
   │  (Skyler)    │    assumption surfacing
   └──────┬──────┘
          │
          ▼ (track G only)
   ┌─────────────┐
   │  SECURITY   │
   │   (Kira)    │  ← OWASP Top 10, CVE audit, secrets scan
   └──────┬──────┘
          │
          ▼
   Mark [x] in overnight.md → Commit → Next task
```

### Per-Task Pipeline Details

1. **Architecture Pre-flight** — Winston reviews existing code + new task description before any code is written. Raises concerns if the new task conflicts with established patterns, introduces unnecessary complexity, or violates architectural decisions.

2. **Code Implementation** — Amelia executes the task: writes code, writes tests, ensures all tests pass before marking done.

3. **Parallel PR Review** — Alex (PR Supervisor) spawns two subagents simultaneously:
   - **Subagent A (Correctness)**: logic errors, null checks, state management, edge cases, business logic correctness, AC coverage
   - **Subagent B (Security + Performance)**: auth flows, injection vectors, query efficiency, resource bounds, race conditions
   Both report back to Alex → unified verdict (APPROVE / REQUEST_CHANGES / BLOCK)

4. **Adversarial Review** — Skyler stress-tests the implementation: constructs failure scenarios, surfaces unstated assumptions, identifies the weakest link.

5. **Security Review** (Track G only) — Kira performs full security audit: OWASP Top 10, dependency CVE audit, secrets scan, auth flow review.

6. **Track G (Security) runs last** — after all other tracks complete, Kira runs the full security review on the final state of the application.

---

## PR Merge Rules

Every PR must pass these gates before merging. These rules are enforced by the PR Supervisor and checked by the Team Lead before committing.

### 1. PR Size — Maximum 150 Lines Changed

- A PR must not exceed **150 lines changed** (additions + deletions, excluding generated files like `package-lock.json`, `requirements.txt`, `_bmad/` config)
- If a task produces more than 150 lines, **split it into multiple PRs** — one per logical concern
- The PR review agent must **BLOCK** any PR exceeding 150 lines
- Rationale: Small PRs are faster to review, less likely to introduce bugs, and easier to revert

### 2. PR Title — Clear and Descriptive

Format: `[TASK-ID] <type>: <what changed>`

- `[TASK-ID]` — the overnight.md task identifier (e.g., `B1`, `A3`, `C7`)
- `<type>` — one of: `fix:`, `feat:`, `refactor:`, `docs:`, `test:`, `chore:`, `security:`
- `<what changed>` — specific, not vague. Good: `fix: remove stale TODO comment in PostResult.js`. Bad: `fix: fixes`

### 3. PR Description — Must Include

Every PR must have a description with these four sections:

```
## What
One sentence describing what this PR does.

## Why
One sentence on the reason for the change (link to task if applicable).

## How
Brief summary of the approach taken — specific enough that a reviewer knows what to look at.

## Testing
How was this tested? What should reviewers verify?
```

### PR Review Verdict

| Verdict | Meaning |
|---|---|
| **APPROVE** | Merge. PR meets all gates. |
| **REQUEST_CHANGES** | Specific changes required. Fix and re-review. |
| **BLOCK** | PR exceeds 150 lines, or fundamental issue found. Must split or redesign. |

---

## Overnight Run Instructions

### Pre-Flight (once)

```bash
cd ~/Documents/linkedin-post-master
git checkout -b overnight/run-1
npm install
cd backend && pip install -r requirements.txt
```

### Running the Loop

1. Invoke `bmad-team-lead` via the skill tool
2. Select `OR` (Start Overnight Run) — the team lead loads `docs/tasks/overnight.md`
3. Each loop iteration, the team lead:
   - Finds the first unmarked `[ ]` task
   - Dispatches **Architect (Winston)** for architecture pre-flight on the task
   - Once cleared, dispatches **Dev (Amelia)** to implement the task
   - Once complete, dispatches **PR Supervisor (Alex)** who runs two parallel sub-reviewers
   - Once PR review passes, dispatches **Adversarial (Skyler)** for edge case analysis
   - Marks task `[x]` in `docs/tasks/overnight.md`
   - Commits with `[TASK-ID]` prefix
   - Moves to the next task
4. After completing each track, the team lead runs the full test suite before moving on
5. Track G (Security with Kira) runs last — after all other tracks complete

### Manual Override

You can invoke any agent directly at any time:

```
bmad-team-lead    → Start/resume the overnight run pipeline
bmad-arch-review  → Architecture review on specific code or task
bmad-pr-supervisor → Run parallel PR review on current changes
bmad-adversarial  → Adversarial edge case review
bmad-security     → Security audit (G-track tasks)
```

### Commit Format

```
[B1] fix: remove stale TODO in PostResult.js
[A1] feat: enable Tailwind preflight and extend design tokens
[C3] feat: add logout endpoint with Redis JWT blacklist
...
```

### Verification Per Track

- **A (design)**: Start dev server, screenshot key pages, check for visual regressions
- **B (bugs)**: All bug-related tests pass, no regressions
- **C (backend)**: `pytest backend/tests/` — 100% pass
- **D (features)**: Feature works end-to-end in browser
- **E (tests)**: `pytest + npm test` — 100% pass
- **F (docs)**: `docs/` renders correctly, `docker-compose up` works
- **G (security)**: Run `pip-audit`, `npm audit`, verify all G tasks pass

---

## Codebase Structure

```
linkedin-post-master/
├── frontend/                    # React SPA (Create React App)
│   ├── src/
│   │   ├── App.js              # Routing, auth shell
│   │   ├── components/
│   │   │   ├── PostGenerator   # Input form
│   │   │   ├── PostResult      # Results + variants
│   │   │   ├── VariantCard     # Per-variant card
│   │   │   ├── IntelligenceSidebar  # Engagement intel
│   │   │   └── auth/           # Login, ProtectedRoute, AccessDenied
│   │   ├── context/AuthProvider.js
│   │   └── services/apiService.js
│   └── tailwind.config.js      # Tailwind config (preflight disabled)
├── backend/                    # FastAPI
│   ├── main.py                 # All API routes
│   ├── agents/content_agent.py # Claude content generation
│   ├── services/
│   │   ├── claude_service.py   # Anthropic API wrapper
│   │   ├── image_service.py    # fal.ai / HuggingFace
│   │   ├── input_processor.py # PDF/Image/URL processing
│   │   └── quota_service.py    # Redis quota tracking
│   ├── auth/                   # Google OAuth, JWT
│   └── middleware/             # Auth middleware
├── docs/
│   └── tasks/overnight.md      # Task queue (75 tasks)
├── _bmad/                     # BMAD agent system
│   ├── bmm/agents/            # Agent definitions
│   └── bmb/skills/            # Agent-builder, workflow-builder
└── _bmad-output/              # Generated artifacts
```

---

## Key Conventions

### Frontend (React)
- **Styling**: CSS custom properties in `index.css` + Tailwind (A1–A6 will migrate to full Tailwind)
- **State**: React hooks, `AuthProvider` context
- **API calls**: `apiService.js` with Axios interceptors for auth + quota
- **Tests**: React Testing Library (per-component `.test.js` files)

### Backend (FastAPI)
- **Auth**: JWT (HS256), Google OAuth2
- **Quota**: Redis with daily TTL
- **Tests**: `pytest` with fixtures in `conftest.py`

### Design System
- **Colors**: LinkedIn blue primary (`#0A66C2`), gray neutral scale
- **Fonts**: DM Sans (body), Bricolage Grotesque (display)
- **Shadows**: `shadow-sm / md / lg / xl` scale
- **Radius**: `radius-sm / md / lg / xl` scale

---

## Environment Variables

```env
# Backend
ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-sonnet-4-6
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET=...
JWT_EXPIRY_HOURS=24
REDIS_URL=redis://localhost:6379
DAILY_QUOTA_LIMIT=10
IMAGE_GEN_API_KEY=...
IMAGE_GEN_PROVIDER=fal
ALLOWED_EMAILS=you@gmail.com

# Frontend
REACT_APP_API_URL=http://localhost:8001
REACT_APP_GOOGLE_CLIENT_ID=...
```

---

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Frontend
cd frontend
npm install
npm start

# Both together (with Docker)
docker-compose -f docker-compose.yml up
```

---

## Skills Reference

Skills are loaded via the `skill` tool. Available skills relevant to this project:

| Skill | Use When |
|---|---|
| `bmad-dev-story` | Implementing a story from a spec file |
| `bmad-code-review` | Reviewing code changes before PR |
| `bmad-qa-generate-e2e-tests` | Generating end-to-end tests |
| `ce-work` | General development execution |
| `ce-debug` | Debugging errors or test failures |
| `ce-test-browser` | Running browser tests |
| `ce-test-xcode` | iOS build verification |
| `ce-simplify-code` | Simplifying recently-written code |