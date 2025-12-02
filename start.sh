#!/bin/bash
# Start script for Render deployment
# Uses uvicorn directly for FastAPI (ASGI)
# Single worker for stability on Render (workers can cause issues with limited resources)

exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}

