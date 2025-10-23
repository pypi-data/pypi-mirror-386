# src/coda_mcp/logging.py
from __future__ import annotations

import json
import logging
import os
import sys
import time

LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO").upper()

class _StderrJSON(logging.StreamHandler):
    def __init__(self): super().__init__(stream=sys.stderr)
    def emit(self, r: logging.LogRecord) -> None:
        try:
            msg = {
                "ts": int(time.time()*1000),
                "level": r.levelname,
                "msg": r.getMessage(),
                "logger": r.name,
            }
            self.stream.write(json.dumps(msg) + "\n")
        except Exception:
            try:
                self.stream.write('{"level":"ERROR","msg":"log_emit_failed"}\n')
            except Exception:
                pass

def get_logger(name: str = "mcp") -> logging.Logger:
    lg = logging.getLogger(name)
    if not lg.handlers:
        lg.setLevel(LEVEL)
        lg.addHandler(_StderrJSON())
        lg.propagate = False
    return lg
