#!/bin/bash

# Install playwright browsers
python -m playwright install

# Start application
uvicorn app.main:app --host 0.0.0.0 --port $PORT