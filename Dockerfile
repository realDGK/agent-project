# Use a base Python image that is secure and slim
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Install system dependencies for database connectors and build tools
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    # Clean up to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code into the container
# This is the fix for the path issue.
# The `.` copies everything from the build context (your project root)
COPY . .

# Create a non-root user for security best practice
RUN useradd -m -u 1000 agentuser && chown -R agentuser:agentuser /app
USER agentuser

# Expose the port the app runs on
EXPOSE 8000

# Health check to verify the application is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
# This is also part of the fix. The entry point for the app is now correctly
# set to the main.py file in the /app directory.
CMD ["python", "main.py"]
