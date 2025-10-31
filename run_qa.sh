#!/bin/bash

# Run ruff and pyrefly on the specified directory
set -e

directory=${1:-.}

echo "🔍 Running ruff linter..."
ruff check $directory

echo

echo "🤖 Running pyrefly code analysis..."
pyrefly check $directory
