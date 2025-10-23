#!/usr/bin/env python
"""
Convenience script to run the Product Knowledge Graph Manager.

Usage:
    python run.py
"""
import uvicorn
from backend.config import config

if __name__ == "__main__":
    print("=" * 60)
    print("Product Knowledge Graph Manager")
    print("=" * 60)
    print(f"Starting server at http://{config.app_host}:{config.app_port}")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    uvicorn.run(
        "backend.app:app",
        host=config.app_host,
        port=config.app_port,
        reload=config.app_debug
    )
