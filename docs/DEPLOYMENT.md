# Lelock Deployment Guide

**L.E.L.O.C.K.** - Life Emulation & Lucid Observation for Care & Keeping

A digital sanctuary where the world doesn't need saving. The world is there to save you.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Requirements](#requirements)
3. [Installation Methods](#installation-methods)
4. [LM Studio Setup](#lm-studio-setup)
5. [Save Data & Persistence](#save-data--persistence)
6. [Configuration](#configuration)
7. [Platform-Specific Notes](#platform-specific-notes)
8. [Troubleshooting](#troubleshooting)
9. [For Developers](#for-developers)

---

## Quick Start

### The Fastest Way to Play

```bash
# 1. Clone the repository
git clone https://github.com/kit-ada/lelock.git
cd lelock

# 2. Run the development script (handles everything)
./scripts/run_dev.sh
```

That's it! The script will:
- Create a virtual environment
- Install dependencies
- Check for LM Studio
- Launch the game

**Important:** You need [LM Studio](#lm-studio-setup) running for NPC dialogue. Without it, NPCs cannot speak.

---

## Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10+, macOS 12+, Linux (Ubuntu 22.04+) |
| **Python** | 3.11 or higher |
| **RAM** | 4GB minimum, 8GB recommended |
| **Storage** | 500MB for game + 2-8GB for LLM models |
| **Display** | 1280x720 minimum |

### Required Software

1. **Python 3.11+** - [python.org](https://www.python.org/downloads/)
2. **LM Studio** - [lmstudio.ai](https://lmstudio.ai/) (REQUIRED for NPC dialogue)

### Optional Software

- **Docker Desktop** - For containerized deployment
- **Git** - For cloning the repository

---

## Installation Methods

### Method 1: Native Python (Recommended)

Best for most users. Simple and direct.

```bash
# Clone the repository
git clone https://github.com/kit-ada/lelock.git
cd lelock

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate        # macOS/Linux
# or
.\venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Run the game
python -m src.main
```

Or just use the scripts:

```bash
./scripts/run_dev.sh   # Development mode (debug output)
./scripts/run_prod.sh  # Production mode (optimized)
```

### Method 2: Docker

Best for isolation and reproducibility.

```bash
# Clone the repository
git clone https://github.com/kit-ada/lelock.git
cd lelock

# Build and run with Docker Compose
docker-compose up

# Or build manually
docker build -t lelock:latest .
docker run --rm -it \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v lelock-saves:/home/lelock/game/saves \
  lelock:latest
```

**Note:** Docker requires X11 forwarding for GUI. See [Platform-Specific Notes](#platform-specific-notes).

### Method 3: pip install (Coming Soon)

```bash
# Future release
pip install lelock
lelock
```

---

## LM Studio Setup

**LM Studio is REQUIRED for Lelock.** Without it, NPCs cannot generate dialogue and the game loses its core therapeutic feature.

### Step 1: Download LM Studio

1. Go to [lmstudio.ai](https://lmstudio.ai/)
2. Download for your platform
3. Install and launch

### Step 2: Download a Model

Recommended models for Lelock (tested and balanced for therapy/cozy content):

| Model | Size | VRAM | Notes |
|-------|------|------|-------|
| **Llama 3.2 3B Instruct** | ~2GB | 4GB | Best balance of quality and speed |
| **Phi-3 Mini** | ~2.3GB | 4GB | Very fast, good for older hardware |
| **Mistral 7B Instruct** | ~4GB | 8GB | Higher quality, needs more VRAM |
| **Llama 3.1 8B Instruct** | ~5GB | 10GB | Best quality, needs good GPU |

In LM Studio:
1. Click "Search" in the left sidebar
2. Search for your chosen model
3. Click "Download"

### Step 3: Start the Local Server

1. Go to the "Local Server" tab (left sidebar)
2. Select your downloaded model
3. Click "Start Server"
4. Verify it says "Server running on http://localhost:1234"

### Step 4: Verify Connection

```bash
# Test the connection
curl http://localhost:1234/v1/models
```

You should see JSON with your model name.

### Recommended LM Studio Settings

For the coziest NPC dialogue:

```
Temperature: 0.7      (Creative but coherent)
Max Tokens: 150       (Short, digestible responses)
Top P: 0.9            (Good variety)
Context Length: 4096  (Enough for conversation history)
```

---

## Save Data & Persistence

Lelock treasures your save data. Here's where everything lives:

### Save Locations

| Data Type | Default Location | Environment Variable |
|-----------|------------------|---------------------|
| **Save Files** | `./saves/` | `LELOCK_SAVES_DIR` |
| **NPC Memories** | `./memories/` | `LELOCK_MEMORY_DIR` |
| **Logs** | `./logs/` | `LELOCK_LOG_DIR` |
| **Config** | `./config/` | `LELOCK_CONFIG_DIR` |

### Docker Volumes

When running with Docker, data persists in named volumes:

```bash
# List volumes
docker volume ls | grep lelock

# Backup save data
docker run --rm -v lelock-saves:/data -v $(pwd):/backup alpine \
  tar czf /backup/lelock-saves-backup.tar.gz /data

# Restore save data
docker run --rm -v lelock-saves:/data -v $(pwd):/backup alpine \
  tar xzf /backup/lelock-saves-backup.tar.gz -C /
```

### Backup Recommendations

1. **Save Files**: Back up regularly. These are PRECIOUS.
2. **NPC Memories**: Back up if you want to preserve NPC relationships.
3. **Logs**: Optional, useful for debugging.

```bash
# Simple backup script
tar czf lelock-backup-$(date +%Y%m%d).tar.gz saves/ memories/
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LELOCK_DEBUG` | `0` | Enable debug mode (`1` for verbose output) |
| `LELOCK_ENV` | `production` | Environment (`development` or `production`) |
| `LELOCK_LLM_BASE_URL` | `http://localhost:1234/v1` | LM Studio API endpoint |
| `LELOCK_LLM_MODEL` | Auto-detect | Override model name |
| `LELOCK_SAVES_DIR` | `./saves` | Save file directory |
| `LELOCK_MEMORY_DIR` | `./memories` | NPC memory database directory |
| `LELOCK_LOG_DIR` | `./logs` | Log file directory |

### Settings File (Coming Soon)

```yaml
# config/settings.yaml
display:
  width: 1280
  height: 720
  fullscreen: false
  vsync: true

audio:
  master_volume: 0.7
  music_volume: 0.5
  sfx_volume: 0.8

llm:
  base_url: http://localhost:1234/v1
  temperature: 0.7
  max_tokens: 150
```

---

## Platform-Specific Notes

### macOS

```bash
# Homebrew dependencies (if needed)
brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf

# If using Docker, install XQuartz for X11
brew install --cask xquartz
# Logout and login, then:
xhost +localhost
```

### Linux (Ubuntu/Debian)

```bash
# Install SDL2 dependencies
sudo apt-get install libsdl2-2.0-0 libsdl2-image-2.0-0 \
  libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0

# For Docker GUI support
xhost +local:docker

# For audio in Docker
# Ensure PulseAudio is running
pulseaudio --check || pulseaudio --start
```

### Windows

```bash
# Most dependencies are bundled with pygame-ce on Windows
# Just run:
pip install -r requirements.txt

# For Docker, use WSL2 with Docker Desktop
# Enable WSLg for GUI support
```

### Steam Deck / Handheld Linux

```bash
# Flatpak deployment (coming soon)
flatpak install lelock

# Manual installation works in Desktop Mode
# Controller support is built-in via SDL2
```

---

## Troubleshooting

### Common Issues

#### "LM Studio not detected"

**Problem:** Lelock can't connect to LM Studio.

**Solutions:**
1. Make sure LM Studio is running
2. Check the Local Server tab shows "Server running"
3. Verify the URL: `curl http://localhost:1234/v1/models`
4. Check firewall isn't blocking port 1234

#### "Could not import Game class"

**Problem:** Python can't find the game modules.

**Solutions:**
1. Make sure you're in the `lelock/` directory
2. Run with `python -m src.main` not `python src/main.py`
3. Check virtual environment is activated

#### "No module named 'pygame'"

**Problem:** Dependencies not installed.

**Solutions:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### Black screen / No display (Docker)

**Problem:** X11 forwarding not working.

**Solutions:**
```bash
# Linux
xhost +local:docker
export DISPLAY=:0

# macOS (requires XQuartz)
xhost +localhost
export DISPLAY=host.docker.internal:0
```

#### Audio not working

**Problem:** No sound in game.

**Solutions:**
```bash
# Check audio driver
echo $SDL_AUDIODRIVER

# macOS
export SDL_AUDIODRIVER=coreaudio

# Linux
export SDL_AUDIODRIVER=pulse
# or
export SDL_AUDIODRIVER=alsa
```

### Debug Mode

Enable debug mode for verbose output:

```bash
LELOCK_DEBUG=1 python -m src.main
```

Or use the development script:

```bash
./scripts/run_dev.sh
```

### Log Files

Check logs for detailed error information:

```bash
cat logs/lelock.log
tail -f logs/lelock.log  # Live monitoring
```

---

## For Developers

### Development Setup

```bash
# Clone with submodules
git clone --recursive https://github.com/kit-ada/lelock.git
cd lelock

# Setup development environment
./scripts/run_dev.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install dev dependencies
pip install pytest black ruff mypy ipython
```

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html

# Specific test file
python -m pytest tests/test_llm.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Building Docker Images

```bash
# Production image
docker build -t lelock:latest .

# Development image
docker build -t lelock:dev --target dev .

# Headless/CI image
docker build -t lelock:headless --target headless .
```

### CI/CD Pipeline

The headless Docker target is designed for CI:

```bash
# Run tests in CI
docker run --rm lelock:headless

# Or with custom test command
docker run --rm lelock:headless python -m pytest tests/ -v --tb=short
```

---

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/kit-ada/lelock/issues)
- **Discussions:** [GitHub Discussions](https://github.com/kit-ada/lelock/discussions)
- **Wiki:** [Project Wiki](https://github.com/kit-ada/lelock/wiki)

---

*Built with love by Kit & Ada Marie*

*The sanctuary awaits. Welcome home.*
