# # Use the full Python image (instead of slim) to reduce potential package missing issues
# FROM python:3.9-buster

# # Install system dependencies required by Playwright
# RUN apt-get update && apt-get install -y \
#     libgtk-3-0 \
#     libgdk-3-0 \
#     libnss3 \
#     libxss1 \
#     libatk-bridge2.0-0 \
#     libatk1.0-0 \
#     libcups2 \
#     libx11-xcb1 \
#     libdbus-1-3 \
#     libgdk-pixbuf2.0-0 \
#     libnspr4 \
#     libxcomposite1 \
#     libxrandr2 \
#     libgbm1 \
#     libasound2 \
#     libpangocairo-1.0-0 \
#     libpango-1.0-0 \
#     libfontconfig1 \
#     libgles2-mesa \
#     && rm -rf /var/lib/apt/lists/*

# # Set the working directory inside the container
# WORKDIR /app

# # Copy the current directory's contents into the container at /app
# COPY . /app

# # Ensure the requirements.txt file is copied correctly
# COPY requirements.txt /app/

# # Install the Python dependencies from requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# # Install Playwright browsers
# RUN python -m playwright install

# # Expose the port that Render expects
# EXPOSE 8000

# # Command to run your application using the deployment command provided by Render
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]





# # Use Playwright's official Docker image, which includes necessary dependencies
# FROM mcr.microsoft.com/playwright:v1.48.0-focal

# # Install Python & pip
# RUN apt-get update && apt-get install -y \
#     python3 \
#     python3-pip \
#     python3-venv \
#     && rm -rf /var/lib/apt/lists/*

# # Set the working directory inside the container
# WORKDIR /app

# # Copy the current directory's contents into the container at /app
# COPY . /app

# # Ensure the requirements.txt file is copied correctly
# COPY requirements.txt /app/

# # Install the Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Expose the port that Render expects
# EXPOSE 8000

# # Command to run the app using the deployment command
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]



# Use Playwright's official Docker image, which includes necessary dependencies
FROM mcr.microsoft.com/playwright:v1.48.0-focal

# Install Python & pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Ensure the requirements.txt file is copied correctly
COPY requirements.txt /app/

# Fix pyee version issue before installing other dependencies
RUN pip install --no-cache-dir pyee==12.0.0

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory's contents into the container at /app
COPY . /app

# Ensure playwright browsers are installed
RUN playwright install --with-deps

# Expose the port that Render expects
EXPOSE 8000

# Command to run the app using the deployment command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]