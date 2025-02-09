# Path: app\invokeai.py
import yaml
from pathlib import Path


def create_invokeai_yaml(path: Path, max_cache_ram_gb = None, max_cache_vram_gb = None, enable_partial_loading = None):
    config = {
        "schema_version": "4.0.2"
    }

    if max_cache_ram_gb is not None:
        print(f"Set max_cache_ram_gb = {max_cache_ram_gb}")
        config["max_cache_ram_gb"] = max_cache_ram_gb

    if max_cache_vram_gb is not None:
        print(f"Set max_cache_vram_gb = {max_cache_vram_gb}")
        config["max_cache_vram_gb"] = max_cache_vram_gb

    if enable_partial_loading is not None:
        print(f"Set enable_partial_loading = {enable_partial_loading}")
        config["enable_partial_loading"] = enable_partial_loading

    if len(config) > 1:
        with open(path, "w") as yaml_file:
            yaml.dump(config, yaml_file, default_flow_style=False)
        print("Created invokeai.yaml")