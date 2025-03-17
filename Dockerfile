# Use a base image with Python installed
FROM python:3.9-slim

# Install system dependencies required by playwright
RUN apt-get update && apt-get install -y \
    libgtk-4-dev \
    libgraphene-1.0-0 \
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    libenchant-2-2 \
    libsecret-1-0 \
    libmanette-0.2-0 \
    libgles2-mesa \
    libnss3 \
    libxss1 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libx11-xcb1 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libatk1.0-0 \
    libgles2-mesa \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory's contents into the container at /app
COPY . /app

# Ensure the requirements.txt file is copied correctly
COPY requirements.txt /app/

# Copy the current dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install

# Expose the port that render expects
EXPOSE 8000

# Command to run app using the deployment command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]