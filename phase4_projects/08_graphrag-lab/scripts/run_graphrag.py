"""
GraphRAG CLI 抑制警告的包装器
================================

在导入 graphrag 之前抑制 LiteLLM AWS 相关的无害警告日志。

用法：
  python scripts/run_graphrag.py index --root .
  python scripts/run_graphrag.py query --root . --method local "What is LoRA?"
"""

import logging
logging.basicConfig(level=logging.WARNING)

import sys
from graphrag.cli.main import app

if __name__ == "__main__":
    sys.exit(app())
