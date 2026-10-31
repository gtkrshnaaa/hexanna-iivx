FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies and package
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .[all]

# Copy remaining application files
COPY . .

# Default non-root user
RUN useradd -m -u 10001 hexannauser && \
    chown -R hexannauser:hexannauser /app
USER hexannauser

ENTRYPOINT ["python3", "-m", "hexanna"]
CMD ["--help"]
