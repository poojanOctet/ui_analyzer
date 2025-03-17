#!/bin/bash

# Install missing system dependencies
apt-get update && apt-get install -y \
    libgtk-4-dev \
    libgraphene-1.0-0 \
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    libenchant-2-2 \
    libsecret-1-0 \
    libmanette-0.2-0 \
    libgles2-mesa

# Install playwright browsers
python -m playwright install --with-deps

# Start application
uvicorn app.main:app --host 0.0.0.0 --port $PORT