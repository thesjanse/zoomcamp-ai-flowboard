# zoomcamp-ai-flowboard

A responsive Kanban project-management web app for individuals and small teams. Built as a
learning project for the AI development zoomcamp.

The app is a FastAPI REST backend plus a React + TypeScript (Vite) frontend. The backend uses an
in-memory data store seeded with demo data, so you can run and explore the full stack without a
database.

## Features

- Email + password authentication with JWT sessions
- Projects, invites, and admin/member roles
- Up to 7 Kanban columns with drag-and-drop card ordering
- Cards with priority, due date, assignee, and rich-text descriptions
- Flat comments with `@mention` autocomplete
- Blocking relationships between cards
- Search across projects and cards (including archived projects)
- Project archive / restore and permanent deletion
- Light/dark theme, responsive desktop & mobile

See `_docs/specs.md` for the full MVP specification.

## Repository layout

| Path | What it is |
| --- | --- |
| `backend/api-server/` | FastAPI backend (uv / Python) |
| `frontend/kanban-board/` | Main React app (pnpm / Vite) |
| `frontend/mockup-sandbox/` | Separate mockup/preview sandbox app |
| `frontend/lib/api-client-react/` | Generated React Query API hooks + custom fetch |
| `lib/api-spec/` | OpenAPI spec and Orval codegen config |
| `lib/api-zod/` | Zod schemas generated from the API spec |
| `lib/db/` | Drizzle schema / DB migrations |
| `openapi.yaml` | OpenAPI specification of the API |
| `_docs/specs.md` | MVP feature specification |

## Prerequisites

- Python >= 3.11 with [uv](https://docs.astral.sh/uv/)
- Node.js with [pnpm](https://pnpm.io/)

## Running the project

The API client talks to the same-origin relative `/api` path, so run both servers and access the
app through the frontend URL.

### 1. Start the backend

From `backend/api-server/`:

```bash
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 5000
```

- The store runs in-memory and is seeded with demo data (no database required).
- `SECRET_KEY` is optional for local dev and defaults to a dev value.

### 2. Start the frontend

From the repository root:

```bash
pnpm install
PORT=22152 BASE_PATH=/ pnpm --filter @workspace/kanban-board run dev
```

Open http://localhost:22152.

### Demo accounts

All seeded users share the password `password123`:

| Email | Name |
| --- | --- |
| `demo@demo.dev` | Demo User |
| `mara@demo.dev` | Mara Chen |
| `theo@demo.dev` | Theo Alvarez |
| `inez@demo.dev` | Inez Okafor |
| `rowan@demo.dev` | Rowan Bell |

## Testing and checks

From `backend/api-server/`:

```bash
uv run pytest                 # run all backend tests
uv run pytest tests/test_health.py  # run a single test file
```

From the repository root:

```bash
pnpm run typecheck                              # typecheck all packages
PORT=22153 BASE_PATH=/ pnpm run build           # typecheck + build all packages
pnpm --filter @workspace/kanban-board run test  # frontend tests (vitest)
```

Utility commands:

```bash
pnpm --filter @workspace/api-spec run codegen   # regenerate API clients/Zod schemas
pnpm --filter @workspace/db run push            # push DB schema changes (dev only)
```

`api-spec` and `db` tooling require a `DATABASE_URL` (Postgres connection string). The build and
dev commands require `PORT`/`BASE_PATH` environment variables (see the frontend `vite.config.ts`).