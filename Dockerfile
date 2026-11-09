ARG PYTHON_VERSION=3.13

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-alpine AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY README.md ./
COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable

FROM python:${PYTHON_VERSION}-alpine AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

# Remove pip and its bundled dependencies from runtime.
RUN python -m pip uninstall -y pip \
    && addgroup -S app \
    && adduser -S -G app app

COPY --from=builder /app/.venv /app/.venv

USER app

CMD ["py-app-tmpl"]