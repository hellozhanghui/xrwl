# Repository Guidelines

## Project Structure & Module Organization

This repository is a lightweight logistics management system for Xingrui Logistics. The backend is a Python standard-library HTTP service in `backend/server.py`, with application modules under `backend/app/`. API routing lives in `backend/app/api/`, business services in `backend/app/services/`, repositories in `backend/app/repositories/`, and map provider integrations in `backend/app/map_providers/`. The SQLite database is stored at `backend/data/logistics.sqlite`; uploaded files are kept under `backend/uploads/`.

The frontend is a static single-page app in `frontend/src/`, mainly `index.html`, `app.js`, and `styles.css`. Project documentation and architecture notes are in `README.md`, `物流车辆管理系统架构.md`, and `docs/`.

## Build, Test, and Development Commands

- `python3 scripts/init_db.py`: initialize or update the local SQLite schema and seed data.
- `python3 backend/server.py`: start the local backend and static web server, usually at `http://127.0.0.1:8000`.
- `PYTHONPYCACHEPREFIX=/private/tmp/xrwl-pycache python3 -m compileall backend`: syntax-check backend Python without writing cache files into restricted locations.
- `node --check frontend/src/app.js`: syntax-check the main frontend JavaScript file.

## Coding Style & Naming Conventions

Use 4-space indentation for Python and keep service functions small, explicit, and grouped by domain. Prefer repository/service helpers over direct SQL in route handlers. Use snake_case for Python functions, variables, and database columns.

Frontend code uses plain JavaScript, HTML, and CSS. Keep user-facing labels in Chinese, especially workflow states, vehicle types, order fields, and logistics terminology. Use camelCase for JavaScript variables and functions, and keep CSS class names descriptive and hyphenated.

## Testing Guidelines

There is no formal automated test suite yet. Before handing off changes, run the Python compile check and the JavaScript syntax check above. For behavior changes, also perform a manual smoke test in the browser: login, create a transport order, calculate a route, open order detail, and verify map/path/freight output.

## Commit & Pull Request Guidelines

No Git history is available in this workspace. Use concise imperative commit messages such as `Add address route planner` or `Fix order detail map loading`. Pull requests should include a short description, affected modules, verification commands, screenshots for UI changes, and any database migration notes.

## Security & Configuration Tips

Do not hard-code new secrets in frontend files. Map provider tokens and operational defaults should be managed through backend configuration or system management data. Treat `backend/data/` and `backend/uploads/` as local runtime data, not source artifacts.
