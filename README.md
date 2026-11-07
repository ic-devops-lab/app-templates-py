# Python Project Template. Barebones

Barebones for a modern Python projects - a project template with all infrastructure for maintaining and testing configured and installed. Could be helpful if you are:
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

---

## What is included

- **uv**: package and project manager
- **mypy**: tool for static type checking
- **ruff**: tool for linting and code formatting
- **bandit**: tool for static application security testing (SAST)
- **pytest**: framework for tests and a basic test suite
- **centralized app configuration**: all app settings in one place (core/config.py module)
- **basic logging**: basic app logging configuration (core.logging.py module)

---

## config.py and environment variables

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

---

## Quick start

```bash
uv lock
uv sync --locked

make run
# or
uv run py-app-tmpl
```

## Build

To build wheel and source distributions, run:
```bash
uv build

# or
make build
```

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
    uv run pytest                                 # run tests
    # run tests and calculate coverage
    uv run pytest --cov=py_app_tmpl --cov-report=term-missing -v

    # run a specific test
    uv run pytest tests/py_app_tmpl/core/test_config.py::test_env_fixture_overrides_sensitive_vars -xvs

    # using make
    make test                                     # run tests
    make cov                                      # run tests and show the coverage report
    ```
- **SAST check**: a SAST check using the bandit tool
    ```bash
    uv run bandit -r src/py_app_tmpl

    # using make
    make sast
    ```
- **Local CI**: run all checks and tests at once
  ```bash
  make ci
  ```
  > Local CI also includes build command to check whether the package can be built.
---

### Test environment configuration

The project provides two mechanisms for managing application settings during tests, defined in [`tests/conftest.py`](./tests/conftest.py):

- **`pytest_configure()`** — establishes a global test environment before test collection.
- **`override_settings()`** — allows individual tests to override environment variables with automatic cleanup.

---

#### Global test environment: `pytest_configure()`

The `pytest_configure()` hook sets predefined environment variables before pytest collects and imports test modules.

This is particularly useful when application modules initialize settings at import time:

```python
from py_app_tmpl.core.config import get_settings

settings = get_settings()
```

Ordinary pytest fixtures execute after test collection, so they cannot guarantee that test environment variables are available before such imports.

**Keep `pytest_configure()` enabled when:**
- Application modules initialize settings at import time.
- Most tests should use the same predefined test configuration.
- You want a consistent test environment independent of the developer's local settings.

**Consider commenting it out when:**
- Tests should use application defaults or explicitly supplied environment variables.
- Settings are initialized lazily, and individual fixtures provide all necessary configuration.
- You need to test different startup configurations without globally forcing test values.

**Important:** `pytest_configure()` modifies `os.environ` for the entire pytest process. It does not automatically restore those values between tests. Also, it runs before normal test collection, but not necessarily before imports performed by pytest plugins or earlier initialization hooks.

---

#### Per-test overrides: `override_settings()`

Use the `override_settings` fixture when an individual test needs different configuration values.

```python
def test_custom_app_name(override_settings):
    override_settings.setenv("APP_NAME", "custom_app")

    settings = get_settings()

    assert settings.app_name == "custom_app"
```

The fixture uses pytest's `monkeypatch` to restore modified environment variables after the test and clears the `get_settings()` LRU cache before and after execution.

**Use `override_settings()` when:**
- Testing alternative configuration values.
- Testing behavior controlled by environment variables.
- Verifying configuration validation and error handling.
- Preventing cached settings from leaking between tests.

The fixture is **not autouse**: tests must explicitly request it.

**Limitation:** Clearing `get_settings()` cache does not update settings objects already stored in module-level variables. For applications requiring dynamic configuration during tests, prefer lazy settings access or dependency injection.

---

#### Recommended approach

For this template, both mechanisms are available:

- Keep `pytest_configure()` enabled for projects requiring a common test environment before test collection.
- Use `override_settings()` for test-specific configuration changes.
- Disable `pytest_configure()` when tests should rely entirely on application defaults or explicitly managed fixtures.

When testing application defaults, remember that Pydantic Settings may also read values from a local `.env` file. Use `Settings(_env_file=None)` and explicitly control relevant environment variables to avoid unintended overrides.

---

## List of Make commands

Configuration file: [`Makefile`](./Makefile)

Get a list of all make commands available in the project:
```bash
make help
```

---
