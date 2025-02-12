#!/bin/bash

set -e

WORKDIR_PATH=$(pwd)
INVOKEAI_PATH="$WORKDIR_PATH/invokeai"
APP_PATH="$WORKDIR_PATH/app"
VENV_APP="$APP_PATH/.venv/bin/activate"

log() {
    echo "[INFO] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

cleanup() {
    log "Stopping all background processes..."
    pkill -P $$ 
}
trap cleanup EXIT


# ============ Preparation ============ #
log "Starting preparation..."
cd "$APP_PATH" || error "Failed to change directory to $APP_PATH"

# Activate venv
if [ -f "$VENV_APP" ]; then
    source "$VENV_APP"
else
    error "Virtual environment not found in $APP_PATH"
fi

# Run preparation script
log "Running prep.py..."
python prep.py --invoke "$INVOKEAI_PATH" || error "prep.py failed"

# Exit venv
deactivate


# ============ Supervisor ============ #
supervisord > /dev/null 2>&1 &


# ============ App ============ #
log "Starting preparation..."
cd "$APP_PATH" || error "Failed to change directory to $APP_PATH"

# Activate venv
if [ -f "$VENV_APP" ]; then
    source "$VENV_APP"
else
    error "Virtual environment not found in $APP_PATH"
fi

# Run preparation script
log "Running handler.py..."
python handler.py --invoke "$INVOKEAI_PATH" || error "handler.py failed"

# Exit venv
deactivate