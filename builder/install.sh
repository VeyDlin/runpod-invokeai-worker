#!/bin/bash
set -e

WORKDIR_PATH=$(pwd)
INVOKEAI_PATH=$WORKDIR_PATH/invokeai
APP_PATH=$WORKDIR_PATH/app
BUILDER_PATH=$WORKDIR_PATH/builder


# ============ InvokeAI ============ #
mkdir -p $INVOKEAI_PATH
cd $INVOKEAI_PATH 

# Install and activate venv
uv venv --relocatable --prompt invoke --python 3.11 --python-preference only-managed .venv
source .venv/bin/activate 

# Install InvokeAI
uv pip install invokeai==$INVOKEAI_VERSION --python 3.11 --python-preference only-managed --force-reinstall --extra-index-url https://download.pytorch.org/whl/cu124

# Exit venv
deactivate


# ============ Worker app ============ #
cd $APP_PATH 

# Install and activate venv
uv venv --relocatable --python 3.11 --python-preference only-managed .venv
source .venv/bin/activate

# Install requirements
uv pip install --python 3.11 --python-preference only-managed --force-reinstall -r $BUILDER_PATH/requirements.txt

# Exit venv
deactivate