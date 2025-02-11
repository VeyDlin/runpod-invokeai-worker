#!/bin/bash

set -e

WORKDIR_PATH=$(pwd)
INVOKEAI_PATH=$WORKDIR_PATH/invokeai
APP_PATH=$WORKDIR_PATH/app


# ============ Preparation ============ #
cd $APP_PATH

# Activate venv
source .venv/bin/activate

# Run
python prep.py --invoke $INVOKEAI_PATH &

# Exit venv
deactivate


# ============ InvokeAI ============ #
cd $INVOKEAI_PATH

# Activate venv
source .venv/bin/activate

# Run InvokeAI server in background
invokeai-web --root $INVOKEAI_PATH &

# Exit venv
deactivate


# ============ Worker app ============ #
cd $APP_PATH

# Activate venv
source .venv/bin/activate

# Run Worker server
python handler.py --invoke $INVOKEAI_PATH &

wait -n
exit $?