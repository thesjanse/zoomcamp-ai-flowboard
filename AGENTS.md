# zoomcamp-ai-flowboard

Commands

Python / uv (backend/api-server)

- `uv sync` - install dependencies (run from `backend/api-server/`)
- `uv run pytest` - run all backend tests
- `uv run pytest tests/test_health.py` - run one test file
- `uv run uvicorn app.main:app --host 0.0.0.0 --port 5000` - run the API server (from `backend/api-server/`)
- Required env for api-server: `SECRET_KEY` (JWT secret, defaults to dev value)

Frontend / Backend (pnpm workspace)

- `pnpm install` - install dependencies
- `pnpm run typecheck` - typecheck all packages
- `PORT=22153 BASE_PATH=/ pnpm run build` - typecheck + build all packages (PORT/BASE_PATH are required by the frontend vite configs)
- `pnpm --filter @workspace/kanban-board run test` - run frontend tests (vitest)
- `PORT=22152 BASE_PATH=/ pnpm --filter @workspace/kanban-board run dev` - run the frontend app
- `pnpm --filter @workspace/api-spec run codegen` - regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` - push DB schema changes (dev only)
- Required env for api-spec/db: `DATABASE_URL` - Postgres connection string

Rules

- Python dependencies are added in `pyproject.toml`. Do not add one without
  asking
- JS/TS dependencies use the `catalog:` in `pnpm-workspace.yaml`