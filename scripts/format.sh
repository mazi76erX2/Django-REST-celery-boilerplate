#!/bin/bash
set -e

uv run isort backend/ --check-only
uv run black backend/ --check