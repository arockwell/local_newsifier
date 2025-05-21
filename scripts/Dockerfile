FROM python:3.13

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and build scripts
COPY requirements.txt /app/
COPY scripts/build_wheels.sh /app/scripts/

# Build wheels for Python 3.13 on Linux
CMD ["./scripts/build_wheels.sh", "python3.13"]