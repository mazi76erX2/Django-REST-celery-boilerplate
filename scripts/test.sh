#!/bin/bash
set -e

uv run pytest backend/ --cov=backend -v
