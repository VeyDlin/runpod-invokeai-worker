#!/bin/bash

set -e

WORKDIR_PATH=$(pwd)
INVOKEAI_PATH=$WORKDIR_PATH/invokeai
APP_PATH=$WORKDIR_PATH/app
BUILDER_PATH=$WORKDIR_PATH/builder


# ============ Dependencies ============ #

# Install required dependencies, Python 3.11, and associated tools
apt-get update -y 
apt-get install -y libglib2.0-0 libgl1-mesa-glx git python3.11 python3-pip python3.11-venv nano tini

# Set Python 3.11 as the default for python3 and python
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
update-alternatives --set python3 /usr/bin/python3.11
update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
update-alternatives --set python /usr/bin/python3.11

# Upgrade pip and essential Python tools
python3 -m pip install --upgrade pip setuptools wheel

# Update CUDA compatibility
ldconfig /usr/local/cuda-12.4/compat/

# Install Python 3.11 for UV
uv python install 3.11


# ============ InvokeAI ============ #
mkdir -p $INVOKEAI_PATH
cd $INVOKEAI_PATH 

# Install and activate venv
uv venv --relocatable --prompt invoke --python 3.11 --python-preference only-managed .venv
source .venv/bin/activate 

# Install InvokeAI
uv pip install invokeai==$INVOKEAI_VERSION --python 3.11 --python-preference only-managed --force-reinstall --extra-index-url https://download.pytorch.org/whl/cu124

# Run InvokeAI server in background
invokeai-web --root "$INVOKEAI_PATH" > /dev/null 2>&1 &

# Exit venv
deactivate


# ============ Build ============ #
cd $BUILDER_PATH 

# Install and activate venv
uv venv --relocatable --python 3.11 --python-preference only-managed .venv
source .venv/bin/activate

# Install requirements
uv pip install --python 3.11 --python-preference only-managed --force-reinstall -r $BUILDER_PATH/requirements-builder.txt

# Run builder
python installer.py --invoke "$INVOKEAI_PATH" --builder "$BUILDER_PATH" --config "$CONFIG_FILE"

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

chmod +x start.sh