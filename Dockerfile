FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin

WORKDIR /app

# Create user with home directory and proper permissions
RUN addgroup --system nonroot && \
    adduser --system --ingroup nonroot --home /home/nonroot nonroot && \
    mkdir -p /home/nonroot/.cache && \
    chown -R nonroot:nonroot /app /home/nonroot

# Copy dependency files with correct ownership
COPY --chown=nonroot:nonroot uv.lock pyproject.toml README.md /app/

# Copy source code (needed for editable install)
COPY --chown=nonroot:nonroot src /app/src

# Switch to nonroot user BEFORE running uv sync
USER nonroot

# Sync dependencies as nonroot user (this will install the package in editable mode)
RUN uv sync --no-cache

# Copy remaining application code
COPY --chown=nonroot:nonroot . /app/

# Add .venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

ENTRYPOINT []
