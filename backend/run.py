#!/usr/bin/env python3
"""
Simple startup script for the unified API.
Run with: python run.py
Or use: uvicorn main:app --reload
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
