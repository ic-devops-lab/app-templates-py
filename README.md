# Python Project Template. FastAPI Application with optional Observability support

A project template for a modern Python projects with all infrastructure for maintaining and testing configured and installed. Could be helpful if you are:
- **Starting a new Python project** and want a solid foundation with best practices already configured
- **Learning modern Python development** patterns, including dependency management, testing, and CI/CD
- **A DevOps engineer** looking for a simple Python app to experiment with containerization, deployment pipelines, or monitoring
- **Prototyping or building small tools** that need proper structure without the overhead of larger frameworks
- **Teaching or demonstrating** Python project organization and development workflows

---

## Prerequisites

- Linux OS
- Python 3.13
- make (optional, only if you plan to use make commands)
- docker and docker compose
- trivy (see [official installation documentation](https://trivy.dev/docs/latest/getting-started/installation/))

---

## What is included

- **uv**: package and project manager
- **mypy**: tool for static type checking
- **ruff**: tool for linting and code formatting
- **bandit**: tool for static application security testing (SAST)
- **pytest**: framework for tests and a basic test suite
- **centralized app configuration**: all app settings in one place (core/config.py module)
- **basic logging**: basic app logging configuration (core.logging.py module)
- **Dockerfile**: document for creating a Docker image
- **docker compose**:  tool for defining and running multi-container applications
- **Trivy**: security scanner for container images, code, and configurations
- **FastAPI App**: base for a FastAPI service with several check endpoints
- **Optional PostgreSQL support**:
  - async SQLAlchemy/SQLModel engine,
  - session factory,
  - readiness check,
  - Docker Compose profile,
  - integration tests using Testcontainers
- **Optional Observability**: (*Added*)
  - Prometheus instrumentation for FastAPI
  - `/metrics` endpoint and unit tests for it


> See detailed Python code structure [here](./docs/architecture.md)

---

## Previous Stages

1. [Python Project Template. Barebones](https://github.com/ic-devops-lab/app-templates-py/tree/barebones-v1.0.0)
2. [Python Project Template. Containerized App](https://github.com/ic-devops-lab/app-templates-py/tree/containerized-v1.0.0)
3. [Python Project Template. FastAPI Application](https://github.com/ic-devops-lab/app-templates-py/tree/fastapi-v1.0.0)
4. [Python Project Template. FastAPI Application with optional PostgresQL support](https://github.com/ic-devops-lab/app-templates-py/tree/postgres-v1.0.0)

---

## `config.py` and environment variables

To keep all app settings in one place, the [`config.py`](./src/py_app_tmpl/core/config.py) module is used. All settings are gathered in the `Settings` class using the `pydantic-settings` library. If the `.env` file exists in the project's root directory, variables from it will overwrite the default settings.

To see the complete list of environment variables that can be used in the project, check the [`.env.example` file](./.env.example).
All commented variables are optional and have default values in the `config.py` module.

Create a `.env` file from the example:
```bash
cd /path/to/the/project/root

make env
# or
cp .env.example .env
```

For more details about app configuration, please, check out [`configuration.md` doc](./docs/configuration.md)

---

## Quick start

```bash
# install base dependencies
uv sync --locked
# install all dependencies
uv sync --locked --all-extras
# install optional dependences (for example for postgres)
uv sync --extra postgres
# install dependencies for prod environment
uv sync --no-dev --no-extra postgres

# Test App
make run
# or
uv run py-app-tmpl

# FastAPI app
make run-api
# or
uv run py-app-api
```

---

## FastAPI App

Depending on configuration could be run using Uvicorn (test or single-worker environments) or Gunicorn (multi-worker environments).

**Available endpoints**:
- `/health`: Liveness probe
- `/ready`: Readiness probe
- `/info`: System info
- `/`: Example sync endpoint
- `/async_home`: Example async endpoint
> In non-prod mode also FastAPI's interactive documentation is available at `/docs` and `/redoc`


```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/info
```

---

### Optional PostgreSQL support

PostgreSQL is disabled by default. When enabled, the application creates
an async database engine during startup, provides a session factory,
checks connectivity through `/ready`, and disposes of the engine on shutdown.

For local development, configure `.env`:

```dotenv
COMPOSE_PROFILES=postgres
UV_EXTRAS=--extra postgres
POSTGRES_ENABLED=true
POSTGRES_URL=postgresql+asyncpg://app:devpassword@postgres:5432/appdb
```

Then start the application and database:

```bash
docker compose up --build
curl http://localhost:8000/ready
```

Expected readiness response:

```json
{
  "global_status": "ok",
  "postgres": "ok",
  "cache_placeholder": "ok",
  "mq_placeholder": "ok"
}
```

For tests, PostgreSQL integration tests use Testcontainers and require
a running Docker daemon:

```bash
uv run --extra postgres pytest
```

The test suite provisions its own PostgreSQL container; no manually
configured database is required.

---

### Optional Prometheus Metrics

The application supports optional Prometheus instrumentation using `prometheus-fastapi-instrumentator`.

The extension provides:

- HTTP request counters by route, method, and response status.
- HTTP request duration histograms.
- Python garbage collection and runtime metrics.
- Process-level metrics, including CPU and memory usage.
- A dedicated `/metrics` endpoint.

Each application instance uses an independent Prometheus collector registry.

#### Local development

Install the optional dependencies:

```bash
uv sync --locked --extra metrics
```

Enable metrics in `.env`:

```dotenv
METRICS_ENABLED=true
```

Start the application:

```bash
uv run --extra metrics py-app-api
```

Generate some traffic and retrieve the metrics:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

#### Docker Compose

Configure `.env`:

```dotenv
METRICS_ENABLED=true
UV_EXTRAS=--extra metrics
```

Build and start the application:

```bash
make docker-build
make docker-run-bald
```

To combine metrics with PostgreSQL, install both extras:

```dotenv
UV_EXTRAS=--extra postgres --extra metrics
```

Configure PostgreSQL as described in the PostgreSQL extension section.

#### Testing

Run the metrics tests:

```bash
uv run --extra metrics pytest tests/py_app_tmpl/api/test_metrics_endpoint.py -v
```

Run the complete test suite with all optional extensions:

```bash
uv run --all-extras pytest -v
```

#### Limitations

- Metrics are disabled by default.
- When disabled, `/metrics` returns HTTP 404.
- Requests to `/metrics` are excluded from HTTP instrumentation.
- Metrics currently support single-worker operation (`API_WORKERS_COUNT=1`). Gunicorn multiprocess metrics aggregation is not implemented.
- In production, access to `/metrics` should be restricted to trusted monitoring systems.
- Metrics are stored in memory and reset when the application process restarts.

---

## Build

To build wheel and source distributions, run:
```bash
uv build

# or
make build
```

---

## Testing

All app code can be checked and tested using:

- **Linting** check
    ```bash
    uv run ruff check -v .                      # check the code
    uv run ruff check --show-files .            # list the files for test

    # using make
    make lint
    ```
- **Code style** check
    ```bash
    uv run ruff format                          # auto-format
    uv run ruff format --check                  # only check style

    # using make
    make fmt
    make fmt-check
    ```
- **Types consistency** check
    ```bash
    uv run mypy .                                # check the whole project
    uv run mypy src/py_app_tmpl                  # perform a check only for the app folder

    # using make
    make type
    make type-app
    ```
- **Tests**: a test suite with a coverage report
    ```bash
    uv run --locked --all-extras pytest           # run tests

    # run tests and calculate coverage
    uv run pytest --cov=py_app_tmpl --cov-report=term-missing -v

    # run a specific test
    uv run pytest tests/py_app_tmpl/core/test_config.py::test_env_fixture_overrides_sensitive_vars -xvs

    # using make
    make test                                     # run all tests
    make test-fast                                # run quick tests only (no integration or regression tests)
    make cov                                      # run all tests and show the coverage report
    ```
- **SAST check**: a SAST check using the bandit tool
    ```bash
    uv run bandit -r src/py_app_tmpl

    # using make
    make sast
    ```
- **Local CI**: run all checks and tests at once
  ```bash
  make ci UV_EXTRAS=--all-extras
  ```
  > Local CI also includes build command to check whether the package can be built.
---

---

### Test environment configuration

Test configuration is managed through fixtures in `tests/conftest.py`
and environment profiles in `src/helpers/test/env.py`.

- `TestEnv` provides default test settings.
- `ProdLikeTestEnv` provides production-like settings.
- `PostgresTestEnv` enables PostgreSQL for individual tests.
- `apply_test_env` applies a profile and clears the settings cache.
- `async_client_factory` creates a FastAPI test client with a managed
  application lifespan, after test configuration has been applied.
- `postgres_test_env` starts a PostgreSQL Testcontainer and configures
  its connection URL.

Example:

```python
@pytest.mark.asyncio
async def test_readiness_postgres_ok(
    postgres_test_env: None,
    async_client_factory: AsyncClientFactory,
) -> None:
    async with async_client_factory() as client:
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json()["postgres"] == "ok"
```

Apply test configuration before creating the application. Changing
environment variables after application startup does not reconfigure
an existing database engine.

The default test environment is initialized before test collection.
Individual tests can override settings using `apply_test_env` or
`override_settings`.

---

## List of Make commands

Configuration file: [`Makefile`](./Makefile)

Get a list of all make commands available in the project:
```bash
make help
```

---

## Containerization

### Dockerfile

File: [`Dockerfile`](./Dockerfile)

The builder uses the official uv image, while the runtime uses a minimal Python image without uv or build tools.

The dependency installation is split into two steps so changes to application source code don't force a full dependency reinstall.

A few important choices:
- `--locked` in `uv sync` ensures the lockfile remains unchanged during the build.
- `--no-dev` in `uv sync` excludes Ruff, mypy, pytest, Bandit, and other development dependencies.
- `--no-editable` in `uv sync` installs the application as a regular package into `.venv` next to project's dependencies rather than linking it to source files.
  This is possible because our `pyproject.toml` file has the `build-system` section configured
- The virtual environment is copied into the runtime image, so the application doesn't require `uv` to start.
- The production image intentionally excludes pip to eliminate 5 high vulnerabilities that it brings.
- `CMD`, rather than `ENTRYPOINT`, makes it straightforward to override the process later, for example for API or worker containers.

We're deliberately not copying `.env` into the image. Runtime configuration should be supplied externally.

**Build and Run**:

```bash
# manual build
docker build -t py-app-api:dev .

docker run --rm \
  -p 8000:8000 \
  -e API_HOST=0.0.0.0 \
  py-app-api:dev
# API service expected to be up and serve endpoints

# check the runtime user
docker run --rm --entrypoint id py-app-api:dev
# expected: a non-root UID and GID

# check runtime configuration
docker run --rm -e LOG_LEVEL=DEBUG py-app-api:dev
# debug log expected in the logs

# check the image contents
docker run --rm \
  --entrypoint sh \
  py-app-api:dev \
  -c 'command -v python; command -v py-app-tmpl; command -v py-app-api; command -v uv || true'
# the application commands and Python should be available; uv should not be installed in the runtime image
```

---

### Docker Compose

File: [`compose.yaml`](./compose.yaml)

A few design decisions:
- `build.context: .` keeps the project root as the Docker build context.
- `image` gives the built image a predictable local name.
- `environment` explicitly passes configuration into the container.
- `${VAR:-default}` uses a default when the variable is unset or empty.
- configured port is exposed for communication with the FastAPI application
- No volumes, restart, or healthcheck are needed for our current simplistic FastAPI application.

**Build and Run**:

Commands:
```bash
# build the image
docker compose build api

# run the application
docker compose up api

# run the application in a temporary container
docker compose run --rm --service-ports api

# check runtime environment are taken by the app
LOG_LEVEL=DEBUG docker compose up api
# debug log expected in the logs
# instead explicit variable setting up `LOG_LEVEL=DEBUG` you can modify your local .env file

# inspect the resolved configuration
docker compose config
LOG_LEVEL=DEBUG docker compose config

# check docker compose accepts custom image name and tag correctly
IMAGE_NAME=my-python-app IMAGE_TAG=v1.0.0 docker compose config --images
# expected result
my-python-app:v1.0.0

# remove Docker Compose resources
docker compose down
```

Using `make` commands:
```bash
# build the application image
make docker-build

# run the application in a container
make docker-run
LOG_LEVEL=DEBUG make docker-run

# stop and remove Compose-managed containers
make docker-down
```

---

### Image Security Scan with Trivy

```bash
mkdir -p tmp
# full scan with report
trivy image \
  --scanners vuln \
  --format table \
  --output tmp/trivy-report.txt \
  py-app-api:dev


docker image inspect py-app-api:dev \
  --format '{{.Created}}'
trivy image \
  --scanners vuln \
  --severity HIGH,CRITICAL \
  --format table \
  py-app-api:dev

# using make
# # scan an image (that already built)
make docker-scan
# # build a fresh image and scan it
make docker-ci
```

See [a doc with some techniques of getting rid of vulnerabilities](./docs/trivy-eliminating-risks.md)

---

## Troubleshooting

### `curl: (7) Failed to connect to 127.0.0.1 port 8000 after 0 ms: Connection refused`

If you use WSL on Windows, set `API_HOST` to "0.0.0.0" instead of default "127.0.0.1".

`.env`
```text
...
API_HOST="0.0.0.0"
...
```

---
