# =============================================================================
# LELOCK - Life Emulation & Lucid Observation for Care & Keeping
# =============================================================================
# Multi-stage Dockerfile for the Lelock RPG
# Supports both GUI mode (development) and headless mode (CI/testing)
#
# Build:
#   docker build -t lelock:latest .
#
# Run (with X11 forwarding):
#   docker run --rm -it -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix lelock:latest
#
# Created by Kit & Ada Marie
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# Install build dependencies for pygame-ce and llama-cpp
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# -----------------------------------------------------------------------------
# STAGE 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Labels for the container
LABEL maintainer="Kit & Ada Marie"
LABEL description="Lelock - A cozy therapeutic RPG where the world saves YOU"
LABEL version="1.0.0"

# Install runtime dependencies for pygame-ce
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    libfreetype6 \
    libportmidi0 \
    # X11 support for GUI mode
    libx11-6 \
    libxext6 \
    libxrender1 \
    # Fonts for better text rendering
    fonts-dejavu-core \
    # Audio support
    libasound2 \
    libpulse0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security (but with game-friendly UID)
RUN useradd --create-home --uid 1000 --shell /bin/bash lelock
WORKDIR /home/lelock/game

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy game source and assets
COPY --chown=lelock:lelock src/ ./src/
COPY --chown=lelock:lelock assets/ ./assets/
COPY --chown=lelock:lelock data/ ./data/

# Create directories for persistent data
RUN mkdir -p saves memories logs && \
    chown -R lelock:lelock saves memories logs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYGAME_HIDE_SUPPORT_PROMPT=1
ENV SDL_VIDEODRIVER=x11
ENV SDL_AUDIODRIVER=pulse

# Lelock-specific environment
ENV LELOCK_SAVES_DIR=/home/lelock/game/saves
ENV LELOCK_MEMORY_DIR=/home/lelock/game/memories
ENV LELOCK_LOG_DIR=/home/lelock/game/logs

# LM Studio connection (default to localhost, override in docker-compose)
ENV LELOCK_LLM_BASE_URL=http://host.docker.internal:1234/v1
ENV LELOCK_LLM_MODEL=local-model

# Volume mount points for persistence
VOLUME ["/home/lelock/game/saves", "/home/lelock/game/memories"]

# Switch to non-root user
USER lelock

# Health check - verify pygame can import
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pygame; print('OK')" || exit 1

# Default command runs the game
CMD ["python", "-m", "src.main"]

# -----------------------------------------------------------------------------
# STAGE 3: Development (optional, build with --target dev)
# -----------------------------------------------------------------------------
FROM runtime AS dev

# Switch to root for dev tool installation
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    less \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dev Python packages
RUN pip install --no-cache-dir \
    pytest \
    black \
    ruff \
    mypy \
    ipython

# Enable debug mode by default in dev
ENV LELOCK_DEBUG=1

# Switch back to lelock user
USER lelock

# Override command for development (allows shell access)
CMD ["/bin/bash"]

# -----------------------------------------------------------------------------
# STAGE 4: Headless/CI (for testing without display)
# -----------------------------------------------------------------------------
FROM runtime AS headless

# Use dummy video driver for headless operation
ENV SDL_VIDEODRIVER=dummy
ENV SDL_AUDIODRIVER=dummy

# Run tests by default in headless mode
CMD ["python", "-m", "pytest", "tests/", "-v"]
