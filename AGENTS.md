# zoomcamp-ai-flowboard

Commands

Python / uv

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file

Frontend / Backend (pnpm workspace)

- `pnpm install` - install dependencies
- `pnpm run typecheck` - typecheck all packages
- `pnpm run build` - typecheck + build all packages
- `PORT=5000 pnpm --filter @workspace/api-server run dev` - run the API server
- `PORT=22152 BASE_PATH=/ pnpm --filter @workspace/kanban-board run dev` - run the frontend app
- `pnpm --filter @workspace/api-spec run codegen` - regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` - push DB schema changes (dev only)
- Required env for api-server/db: `DATABASE_URL` - Postgres connection string

Rules

- Python dependencies are added in `pyproject.toml`. Do not add one without
  asking
- JS/TS dependencies use the `catalog:` in `pnpm-workspace.yaml`