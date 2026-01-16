#!/bin/bash
# =============================================================================
# LELOCK - Production Launch Script
# =============================================================================
# Runs Lelock in production mode with optimizations and no debug output.
#
# Usage:
#   ./scripts/run_prod.sh              # Native production mode
#   ./scripts/run_prod.sh --docker     # Docker production mode
#   ./scripts/run_prod.sh --check      # Pre-flight check only
#
# Created by Kit & Ada Marie
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Banner (simpler for production)
echo -e "${PURPLE}LELOCK${NC} - Life Emulation & Lucid Observation for Care & Keeping"
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

preflight_check() {
    local all_ok=true

    log_info "Running pre-flight checks..."
    echo ""

    # Check Python version
    if command -v python3 &> /dev/null; then
        PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ $(echo "$PY_VERSION >= 3.11" | bc -l 2>/dev/null || python3 -c "print(1 if $PY_VERSION >= 3.11 else 0)") == 1 ]]; then
            log_success "Python $PY_VERSION"
        else
            log_error "Python 3.11+ required (found $PY_VERSION)"
            all_ok=false
        fi
    else
        log_error "Python 3 not found"
        all_ok=false
    fi

    # Check virtual environment
    if [ -d "$PROJECT_ROOT/venv" ]; then
        log_success "Virtual environment exists"
    else
        log_warn "Virtual environment not found - will need to install dependencies"
    fi

    # Check LM Studio (REQUIRED for production)
    if curl -s --connect-timeout 3 "http://localhost:1234/v1/models" > /dev/null 2>&1; then
        log_success "LM Studio is running"
    else
        log_error "LM Studio not detected at localhost:1234"
        log_error "LM Studio is REQUIRED for NPC dialogue!"
        log_error "Please start LM Studio and load a model before running Lelock."
        all_ok=false
    fi

    # Check save directory
    SAVES_DIR="${LELOCK_SAVES_DIR:-$PROJECT_ROOT/saves}"
    if [ -d "$SAVES_DIR" ]; then
        log_success "Save directory exists: $SAVES_DIR"
    else
        log_info "Save directory will be created: $SAVES_DIR"
        mkdir -p "$SAVES_DIR"
        log_success "Save directory created"
    fi

    # Check memory directory
    MEMORY_DIR="${LELOCK_MEMORY_DIR:-$PROJECT_ROOT/memories}"
    if [ -d "$MEMORY_DIR" ]; then
        log_success "Memory directory exists: $MEMORY_DIR"
    else
        log_info "Memory directory will be created: $MEMORY_DIR"
        mkdir -p "$MEMORY_DIR"
        log_success "Memory directory created"
    fi

    echo ""

    if [ "$all_ok" = true ]; then
        log_success "All pre-flight checks passed!"
        return 0
    else
        log_error "Pre-flight checks failed. Please resolve issues above."
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Main Logic
# -----------------------------------------------------------------------------

cd "$PROJECT_ROOT"

# Parse arguments
USE_DOCKER=false
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --docker    Run in Docker production container"
            echo "  --check     Run pre-flight check only"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check-only mode
if [ "$CHECK_ONLY" = true ]; then
    preflight_check
    exit $?
fi

# Docker mode
if [ "$USE_DOCKER" = true ]; then
    log_info "Starting Docker production environment..."

    # Ensure X11 forwarding is allowed (Linux)
    if command -v xhost &> /dev/null; then
        xhost +local:docker 2>/dev/null || true
    fi

    # Build and run
    docker-compose build lelock
    docker-compose up lelock
    exit 0
fi

# Native production mode
log_info "Running in native production mode"

# Pre-flight check (fail if LM Studio not running)
if ! preflight_check; then
    exit 1
fi

echo ""

# Activate virtual environment
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
elif [ -f "$PROJECT_ROOT/venv/Scripts/activate" ]; then
    source "$PROJECT_ROOT/venv/Scripts/activate"
else
    log_error "Virtual environment activation script not found"
    log_info "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Set production environment variables
export LELOCK_DEBUG=0
export LELOCK_ENV=production
export PYGAME_HIDE_SUPPORT_PROMPT=1
export PYTHONOPTIMIZE=1

# Platform-specific audio driver
if [[ "$OSTYPE" == "darwin"* ]]; then
    export SDL_AUDIODRIVER=coreaudio
elif [[ "$OSTYPE" == "linux"* ]]; then
    export SDL_AUDIODRIVER=pulse
fi

# Save/memory directories
export LELOCK_SAVES_DIR="${LELOCK_SAVES_DIR:-$PROJECT_ROOT/saves}"
export LELOCK_MEMORY_DIR="${LELOCK_MEMORY_DIR:-$PROJECT_ROOT/memories}"

log_info "Starting Lelock..."
echo ""
echo -e "${GREEN}The sanctuary awaits.${NC}"
echo ""

# Run the game with optimizations
python -O -m src.main

# Goodbye message
echo ""
echo -e "${PURPLE}Until next time. The sanctuary remembers you.${NC}"
