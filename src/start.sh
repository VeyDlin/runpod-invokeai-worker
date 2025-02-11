#!/bin/bash

set -e

WORKDIR_PATH=$(pwd)
INVOKEAI_PATH="$WORKDIR_PATH/invokeai"
APP_PATH="$WORKDIR_PATH/app"
VENV_APP="$APP_PATH/.venv/bin/activate"
VENV_INVOKE="$INVOKEAI_PATH/.venv/bin/activate"

log() {
    echo "[INFO] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# Функция для завершения всех запущенных процессов
cleanup() {
    log "Stopping all background processes..."
    pkill -P $$  # Завершает все дочерние процессы текущего скрипта
}
trap cleanup EXIT  # Вызывает cleanup при выходе

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


# ============ InvokeAI ============ #
log "Starting InvokeAI..."
cd "$INVOKEAI_PATH" || error "Failed to change directory to $INVOKEAI_PATH"

# Activate venv
if [ -f "$VENV_INVOKE" ]; then
    source "$VENV_INVOKE"
else
    error "Virtual environment not found in $INVOKEAI_PATH"
fi

# Run InvokeAI
invokeai-web --root "$INVOKEAI_PATH" > "$INVOKEAI_PATH/invokeai.log" 2>&1 &
INVOKEAI_PID=$!

# Exit venv
deactivate


# ============ Worker app ============ #
log "Starting Worker App..."
cd "$APP_PATH" || error "Failed to change directory to $APP_PATH"

# Activate venv
if [ -f "$VENV_APP" ]; then
    source "$VENV_APP"
else
    error "Virtual environment not found in $APP_PATH"
fi

# Run Worker server
log "Running handler.py..."
exec python handler.py --invoke "$INVOKEAI_PATH"