#!/bin/bash
# Start script for Render deployment
# Uses uvicorn directly for FastAPI (ASGI)

exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000} --workers 2

