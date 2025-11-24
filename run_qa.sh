#!/bin/bash

# Run ruff and pyrefly on the specified directory
set -e

directory=${1:-.}

echo "🔍 Running ruff linter..."
# formatting
ruff format $directory
# isort
ruff check --select I --fix $directory
# style checks
ruff check $directory --fix


echo

echo "🤖 Running pyrefly code analysis..."
pyrefly check $directory
