#!/bin/bash
# =============================================================================
# LELOCK - Development Launch Script
# =============================================================================
# Runs Lelock in development mode with debug output and hot reload support.
#
# Usage:
#   ./scripts/run_dev.sh           # Normal dev mode
#   ./scripts/run_dev.sh --docker  # Run in Docker dev container
#   ./scripts/run_dev.sh --test    # Run tests
#
# Created by Kit & Ada Marie
# =============================================================================

set -e

# Colors for output (because we like pretty things)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root (relative to script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Banner
echo -e "${PURPLE}"
echo "  _          _            _    "
echo " | |        | |          | |   "
echo " | |     ___| | ___   ___| | __"
echo " | |    / _ \ |/ _ \ / __| |/ /"
echo " | |___|  __/ | (_) | (__|   < "
echo " |______\___|_|\___/ \___|_|\_\\"
echo -e "${NC}"
echo -e "${CYAN}Life Emulation & Lucid Observation for Care & Keeping${NC}"
echo -e "${YELLOW}Development Mode${NC}"
echo ""

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_lm_studio() {
    log_info "Checking LM Studio connection..."
    if curl -s --connect-timeout 2 "http://localhost:1234/v1/models" > /dev/null 2>&1; then
        log_success "LM Studio is running"
        return 0
    else
        log_warn "LM Studio not detected at localhost:1234"
        log_warn "NPCs will not have AI responses without LM Studio!"
        log_warn "Start LM Studio and load a model to enable NPC dialogue."
        echo ""
        return 1
    fi
}

check_venv() {
    if [ -d "$PROJECT_ROOT/venv" ]; then
        log_success "Virtual environment found"
        return 0
    else
        log_warn "Virtual environment not found"
        return 1
    fi
}

activate_venv() {
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        source "$PROJECT_ROOT/venv/bin/activate"
        log_success "Virtual environment activated"
    elif [ -f "$PROJECT_ROOT/venv/Scripts/activate" ]; then
        # Windows Git Bash
        source "$PROJECT_ROOT/venv/Scripts/activate"
        log_success "Virtual environment activated (Windows)"
    else
        log_error "Could not find activation script"
        exit 1
    fi
}

setup_venv() {
    log_info "Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
    activate_venv
    log_info "Installing dependencies..."
    pip install --upgrade pip
    pip install -r "$PROJECT_ROOT/requirements.txt"
    log_success "Dependencies installed"
}

# -----------------------------------------------------------------------------
# Main Logic
# -----------------------------------------------------------------------------

cd "$PROJECT_ROOT"

# Parse arguments
USE_DOCKER=false
RUN_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --docker    Run in Docker development container"
            echo "  --test      Run tests instead of game"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Docker mode
if [ "$USE_DOCKER" = true ]; then
    log_info "Starting Docker development environment..."

    # Ensure X11 forwarding is allowed (Linux/macOS)
    if command -v xhost &> /dev/null; then
        xhost +local:docker 2>/dev/null || true
    fi

    docker-compose --profile dev up lelock-dev
    exit 0
fi

# Native mode
log_info "Running in native development mode"
echo ""

# Check/setup virtual environment
if ! check_venv; then
    log_info "Setting up virtual environment..."
    setup_venv
else
    activate_venv
fi

# Check LM Studio (warn but don't fail)
echo ""
check_lm_studio || true
echo ""

# Set development environment variables
export LELOCK_DEBUG=1
export LELOCK_ENV=development
export PYGAME_HIDE_SUPPORT_PROMPT=1

# Platform-specific audio driver
if [[ "$OSTYPE" == "darwin"* ]]; then
    export SDL_AUDIODRIVER=coreaudio
elif [[ "$OSTYPE" == "linux"* ]]; then
    export SDL_AUDIODRIVER=pulse
fi

# Run tests or game
if [ "$RUN_TESTS" = true ]; then
    log_info "Running tests..."
    python -m pytest tests/ -v --tb=short
else
    log_info "Starting Lelock in development mode..."
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  The sanctuary awaits. Welcome home.${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""

    # Run the game with Python
    python -m src.main
fi

# Cleanup message on exit
echo ""
echo -e "${PURPLE}The sanctuary will be here when you return.${NC}"
