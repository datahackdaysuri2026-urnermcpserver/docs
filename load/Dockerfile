FROM python:3.12-slim

LABEL maintainer="Data Loading System"
LABEL description="Container for running scheduled web scrapers"

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Create output directory
RUN mkdir -p /output

# Set environment variables
ENV OUTPUT_PATH=/output
ENV RUN_MODE=schedule
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Define output volume
VOLUME ["/output"]

# Run the scheduler
CMD ["python", "src/main.py"]
