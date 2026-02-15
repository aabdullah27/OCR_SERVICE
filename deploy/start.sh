#!/bin/bash

echo "Waiting for vLLM to be ready..."

until curl -s http://localhost:8000/v1/models > /dev/null 2>&1; do
    sleep 2
done

echo "vLLM is ready. Starting FastAPI..."

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
