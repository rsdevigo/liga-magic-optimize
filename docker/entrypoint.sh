#!/bin/bash
set -e

mkdir -p /app/data/db /app/data/cache /app/data/input /app/reports /app/logs

python -c "
from cube_budget.database.migrations import run_migrations
from cube_budget.config.loader import load_config
config = load_config()
run_migrations(config.database.path)
print('Database migrations completed.')
"

# If first arg is not cube-budget/pytest/bash, prepend cube-budget
if [ $# -gt 0 ] && [ "$1" != "cube-budget" ] && [ "$1" != "pytest" ] && [ "$1" != "bash" ] && [ "$1" != "python" ]; then
  set -- cube-budget "$@"
fi

exec "$@"
