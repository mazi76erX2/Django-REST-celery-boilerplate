#!/bin/bash
set -e

uv run ruff check backend/
uv run mypy backend/