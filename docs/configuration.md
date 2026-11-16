# Settings reference

## Environment variables

|     Variable      |         Default         |              Purpose              |
| ----------------- | ----------------------- | --------------------------------- |
| APP_NAME          | Python Project Template | Application name                  |
| APP_VERSION       | 0.1.0                   | Application version               |
| APP_ENV           | local                   | Environment identifier            |
| LOG_LEVEL         | INFO                    | Logging verbosity                 |
| API_HOST          | 127.0.0.1               | Listening interface               |
| API_PORT          | 8000                    | Listening port                    |
| API_RELOAD        | False                   | Automatic code reload             |
| API_WORKERS_COUNT | 1                       | Server selection and worker count |

---

## Server-selection behavior

| Workers | Reload |           Server           |
| ------- | ------ | -------------------------- |
|    1    | false  | Uvicorn                    |
|    1    | true   | Uvicorn with reload        |
|    2+   | false  | Gunicorn + Uvicorn workers |
|    2+   | true   | Invalid configuration      |

> `Workers` is defined by `API_WORKERS_COUNT`
> `Reload` is defined by `API_RELOAD`

---

## Recommendations

- `API_HOST`: use the default `127.0.0.1` when running only on a host/VM. Use `0.0.0.0` when running in a container or hybrid host environments like Windows+WSL.
- `API_WORKERS_COUNT`: **The recommended default is one worker per container**, especially when deploying to Kubernetes in the future. Gunicorn remains available for standalone or VM-based deployments.
- `API_RELOAD=true` option is not compatible with multi-worker configuration.

---
