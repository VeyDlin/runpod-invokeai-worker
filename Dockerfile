# Base image with CUDA 12.4.1 and Ubuntu 22.04
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04


# Builder config
ARG CONFIG_FILE=config.user.yml
ARG INVOKEAI_VERSION=5.6.0


# Set the working directory in the container
WORKDIR /worker-app


# Python uv
COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /uvx /bin/


# Copy worker source code
COPY src app


# Run builder
COPY builder builder
RUN --mount=type=cache,target=/root/.cache \
    chmod +x builder/install.sh && \
    CONFIG_FILE=$CONFIG_FILE INVOKEAI_VERSION=$INVOKEAI_VERSION ./builder/install.sh


# Clean up to reduce image size
RUN apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf builder


# Set invokeai and handler.py as the entry point
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["./app/start.sh"]