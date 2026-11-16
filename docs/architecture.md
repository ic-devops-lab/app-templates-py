# Application structure

| Component | Responsibility |
| --- | ---|
| src/py_app_tmpl/core/config.py | Validated application settings |
| src/py_app_tmpl/core/logging.py | Shared logging configuration |
| src/py_app_tmpl/api/main.py | FastAPI factory and lifespan |
| src/py_app_tmpl/api/main.py |	Server startup and selection |
| src/py_app_tmpl/api/routers/ | API endpoins |
| src/py_app_tmpl/main.py | Original CLI entry point |
| src/helpers/test/ | Helpers for Pytest tests |
| tests/ | Unit and integration tests |

## Architectural Conventions

- avoid side effects at import time
- keep server selection independent of application logic
- use dependency injection or explicit settings overrides for testability
- avoid singleton background jobs in FastAPI lifespan because that code executes in each worker
- use `configure_logging()` only in the entry-point module

---
