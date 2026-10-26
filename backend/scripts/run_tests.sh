#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

if [ -f ".venv/bin/pytest" ]; then
    PYTHON_EXEC=".venv/bin/python3"
    PYTEST_EXEC=".venv/bin/pytest"
else
    PYTHON_EXEC="python3"
    PYTEST_EXEC="pytest"
fi

echo "=========================================================="
echo " Running ManiPool Backend Verification & Acceptance Tests "
echo "=========================================================="
$PYTEST_EXEC -c pytest.ini tests/ -v "$@"
