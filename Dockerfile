# Base image with CUDA 12.4.1 and Ubuntu 22.04
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Builder config
ARG CONFIG_FILE=config.user.yml
ARG INVOKEAI_VERSION=5.6.0

# Environment variables
ENV STORAGE_PATH=/runpod-volume

# Set the working directory in the container
WORKDIR /worker-app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache \
    apt-get update -y && apt-get install -y \
    libglib2.0-0 libgl1-mesa-glx git python3.11 python3-pip python3.11-venv nano supervisor && \
    apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as the default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --set python3 /usr/bin/python3.11 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --set python /usr/bin/python3.11

# Upgrade pip and essential Python tools
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --upgrade pip setuptools wheel

# CUDA compatibility
RUN ldconfig /usr/local/cuda-12.4/compat/

# Python uv
COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /uvx /bin/

# Install Python 3.11 for UV
RUN --mount=type=cache,target=/root/.cache \
    uv python install 3.11

# Copy worker source code
COPY src app

# Copy builder
COPY builder builder

# Install InvokeAI
RUN --mount=type=cache,target=/root/.cache/uv \
    mkdir -p invokeai && \
    uv venv --relocatable --prompt invoke --python 3.11 --python-preference only-managed invokeai/.venv && \
    /bin/bash -c "source invokeai/.venv/bin/activate && uv pip install invokeai==$INVOKEAI_VERSION --python 3.11 --python-preference only-managed --force-reinstall --extra-index-url https://download.pytorch.org/whl/cu124"

# Install app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv --relocatable --prompt app --python 3.11 --python-preference only-managed app/.venv && \
    /bin/bash -c "source app/.venv/bin/activate && uv pip install --python 3.11 --python-preference only-managed -r builder/requirements.txt"

# Supervisor
RUN python builder/generate_supervisor.py --workdir $PWD
RUN ln -s /etc/supervisor/conf.d/supervisor.conf /etc/supervisord.conf

# Clean up to reduce image size
RUN apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf builder

# Set start.sh as the entry point
RUN chmod +x app/start.sh
CMD ["./app/start.sh"]
