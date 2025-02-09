#!/bin/sh

WORKDIR_PATH=$(pwd)
INVOKEAI_PATH=$WORKDIR_PATH/invokeai
APP_PATH=$WORKDIR_PATH/app


# ============ InvokeAI ============ #
cd $INVOKEAI_PATH

# Activate venv
source .venv/bin/activate

# Run InvokeAI server in background
invokeai-web --root $INVOKEAI_PATH > /dev/null 2>&1 &

# Exit venv
deactivate


# ============ Worker app ============ #
cd $APP_PATH

# Activate venv
source .venv/bin/activate

# Run Worker server
python handler.py &

wait -n
exit $?