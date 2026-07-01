#!/bin/bash
set -e
pip install -e ".[dev]"
playwright install chromium
