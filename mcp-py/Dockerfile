FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt update && apt install -y curl

# Install pixi for fast dependency management
RUN curl -fsSL https://pixi.sh/install.sh | sh

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies
RUN /root/.pixi/bin/pixi workspace platform add linux-64
RUN /root/.pixi/bin/pixi install

# Define the data folder
ENV DATA_PATH=/data
RUN mkdir -p /data
VOLUME ["/data"]

# Run the program
CMD ["/root/.pixi/bin/pixi", "run", "python", "-m", "testmcp.main"]
