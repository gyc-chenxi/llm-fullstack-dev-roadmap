#!/usr/bin/env python3
"""Wrapper to suppress harmless LiteLLM AWS warnings before running graphrag commands.

Usage:
  python scripts/run_graphrag.py index --root .
  python scripts/run_graphrag.py query --root . --method local "What is LoRA?"
"""

# MUST be before any litellm/graphrag import
import logging
logging.basicConfig(level=logging.WARNING)

import sys
from graphrag.cli.main import app

if __name__ == "__main__":
    sys.exit(app())
