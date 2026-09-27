# TaskFlow Pro — Dependency-Aware Workflow and DAG Scheduling Engine

**Author:** Harsh Giri
**Repository:** https://github.com/harshgiri3531/taskflow-pro-dag-scheduler
**Built for:** Contata Hackathon 2026

A Kanban tool where tasks can depend on each other. The engine models tasks as a
directed acyclic graph (DAG), rejects cycles before they are saved, computes each
task's earliest start/finish and critical path, and derives Blocked/Ready status
from prerequisite completion. An optional AI feature suggests dependencies for a
new task, but every suggestion is validated against the same cycle check before
it can ever be accepted.

## Tech stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Scheduling engine:** pure Python (`app/engine/`), no web framework imports,
  fully unit-testable on its own
- **Frontend:** React (loaded via CDN + Babel standalone — no Node.js/npm build
  step) with native HTML5 Drag and Drop instead of dnd-kit
- **AI:** Groq-hosted LLM (`openai/gpt-oss-20b`) for dependency suggestions

## How to run

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
copy .env.example .env       # Windows: copy | Mac/Linux: cp
# then put your real GROQ_API_KEY inside .env
python -m uvicorn app.main:app --reload
```
Backend runs at `http://127.0.0.1:8000`. Interactive API docs at `/docs`.

### Frontend
Open `frontend/index.html` with the VS Code "Live Server" extension
(right-click → "Open with Live Server"), or double-click the file to open it
directly in a browser. No build step, no Node.js required.

### Tests
```bash
cd backend
pytest tests/ -v
```
All 7 engine tests pass, covering direct/indirect/self cycles, diamond-dependency
delay counting, critical path identification, and blocked status.

## Architecture

Three layers, kept deliberately separate:

1. **Engine (`app/engine/`)** — `graph.py` holds a plain adjacency-list `Graph`
   with cycle detection (`would_create_cycle`, using BFS from the successor to
   check if the predecessor is already reachable) and topological sort (Kahn's
   algorithm). `scheduler.py` runs a forward pass (earliest start = max of all
   predecessors' earliest finish — this is what prevents double-counting delay
   in a diamond-shaped dependency) and a backward pass (slack, critical path).
   This module has zero FastAPI/SQLAlchemy imports so it can be tested alone.

2. **API (`app/api/`)** — FastAPI routers for tasks, dependencies, the combined
   workflow view, and AI suggestions. `dependencies.py` rebuilds the graph from
   the database on every write and dry-runs the new edge through
   `would_create_cycle` before saving — an edge that would create a cycle is
   rejected with the offending path returned to the caller.

3. **Frontend** — a single React app (`frontend/app.js`) that only renders what
   `/workflow` returns. It never computes schedules itself, so there is one
   source of truth for dates, slack, and blocked/critical status.

### API endpoints
- `GET/POST /tasks`, `PATCH/DELETE /tasks/{id}`
- `POST /dependencies` (cycle-checked), `DELETE /dependencies/{id}`
- `GET /workflow` — full computed state (dates, slack, critical flag, blocked flag)
- `POST /suggestions/generate/{task_id}` — asks the LLM, validates, stores as pending
- `POST /suggestions/{id}/accept` / `/dismiss`

## Data model

- **tasks** — id, title, description, duration, column (Backlog/In Progress/
  Review/Done), created_at
- **dependencies** — predecessor_id, successor_id, source (manual/ai),
  unique constraint on the pair, check constraint blocking self-links
- **suggestions** — predecessor_id, successor_id, reason, confidence, status
  (pending/accepted/dismissed)
- **audit_log** — records column changes for traceability

## AI usage (trust-but-verify)

When a new task is created, its title/description plus a short list of existing
tasks are sent to a Groq-hosted LLM with a JSON-only prompt. Task text is treated
as untrusted data in the prompt, not instructions. Every returned suggestion is
then:
1. checked for a valid, existing predecessor id,
2. dry-run through the exact same `would_create_cycle` function the manual flow
   uses — a suggestion that would create a cycle is silently dropped,
3. shown to the user with a reason and confidence, and only written to the
   graph if the user clicks Accept (re-validated again at accept time).

If the LLM call fails, times out, or returns malformed JSON, the function
returns an empty list and the manual flow is completely unaffected.

## Verified test scenario

The following 5-task chain was used to manually verify the engine end-to-end
(also covered by the automated tests in `backend/tests/test_engine.py`):

Design database schema (1d)
│
├──> Build authentication API (2d) ───┐
│ ├──> Integrate frontend with API (1d) ──> Write end-to-end tests (1d)
└──> Build product listing API (2d) ───┘


- **Diamond dependency:** "Integrate frontend with API" starts at day 3
  (`max(3, 3)`), not day 6 (`3 + 3`) — confirming delay is counted once, not
  summed across both incoming paths.
- **Cycle rejection:** attempting to link "Write end-to-end tests" back to
  "Design database schema" is rejected with the exact offending path returned
  in the error message.
- **Blocked/Ready propagation:** moving "Design database schema" to Done makes
  both dependent tasks Ready; moving it back out of Done (regression) makes
  them Blocked again, with no stale state, since `/workflow` recomputes the
  full schedule from the database on every request.

## Known limitations / assumptions

- Durations are whole/fractional working days; no calendars or holidays
- Single workspace, no login/auth (out of scope for this sprint)
- SQLite is used for simplicity; the code can move to PostgreSQL by changing
  `SQLALCHEMY_DATABASE_URL` in `app/db.py`
- No resource leveling (unlimited parallel capacity assumed)
- AI suggestion quality depends on how descriptive task titles/descriptions are
- Frontend uses CDN-loaded React with in-browser Babel (chosen after local
  Node.js/npm setup issues during the sprint) instead of a Vite build with
  dnd-kit/React Flow; drag-and-drop uses the native HTML5 Drag API and there is
  no dedicated graph visualization view — the Kanban board with Blocked/Ready/
  Critical Path badges is the primary UI
- The Groq model used (`openai/gpt-oss-20b`) was selected based on what was
  available on the developer's account at build time; swap the model string in
  `app/services/llm_client.py` if needed

## AI Tool Declaration

An AI coding assistant (Claude) was used during development for boilerplate,
debugging build/environment errors, and drafting this README. The DAG engine
logic (`app/engine/graph.py`, `app/engine/scheduler.py`) and its test suite were
written and verified by hand, including the diamond-dependency and cycle-
detection test cases, since correctness there matters most.