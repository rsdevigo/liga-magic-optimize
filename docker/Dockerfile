FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy project files needed for install
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --upgrade pip && \
    pip install -e ".[dev]"

# Install Playwright browser
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy remaining files
COPY config/ /app/config/
COPY tests/ /app/tests/
# Copy entrypoint (must use LF line endings)
COPY docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Create data directories with correct permissions
RUN mkdir -p /app/data/db /app/data/cache /app/data/input /app/reports /app/logs && \
    chown -R pwuser:pwuser /app

USER pwuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('/app/data/db/cube_budget.sqlite').cursor().execute('SELECT 1')" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["cube-budget", "--help"]
