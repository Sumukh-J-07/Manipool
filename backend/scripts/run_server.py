#!/usr/bin/env python3
import os
import sys

# Ensure repository root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn
from backend.app.config import settings

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} on http://{host}:{port}")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=reload)
