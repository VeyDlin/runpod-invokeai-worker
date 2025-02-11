import os
import yaml
from pathlib import Path
import shutil
import git
import subprocess
from runpod import RunPodLogger
from typing import Optional, Dict, Any, List
from invoke import Invoke
from .schema import ModelInfo, NodeInfo
from .stale_portaLock import StalePortaLock

log = RunPodLogger()


class InvokeManager:
    def __init__(self, invoke_path: Path, storage_path: Optional[Path] = None):
        if not storage_path:
            storage_path = invoke_path

        if not storage_path.is_dir():
            storage_path = invoke_path

        self.invoke_path = invoke_path.resolve()
        self.storage_path = storage_path.resolve()

        os.makedirs(self.invoke_path, exist_ok=True)
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.lock = StalePortaLock(self.storage_path, stale_threshold=60 * 10)
        self.lock.timeout = 30

        self.invoke_db_path = (self.invoke_path / "databases")
        self.storage_db_path = (self.storage_path / "databases")
        self.models_path = (self.storage_path / "models")
        self.nodes_path = (self.storage_path / "nodes")
        self.download_cache_path = (self.storage_path / "download_cache")


    async def install_models(self, models: Optional[List[ModelInfo]]):
        if not models:
            return
        
        try:
            async with Invoke() as invoke:
                all_models = await invoke.models.list()

                if self.is_storage_use():
                    self.lock.acquire()
                
                for model in models:
                    if not any(m.source == model.source for m in all_models):
                        log.log(f"Install model from: {model.source}")
                        await invoke.models.install(model.source, inplace=True)

                log.info("Wait install models...")
                await invoke.models.prune_completed_jobs()
                await invoke.wait_install_models(raise_on_error=True)
                log.info("All models installed")

                models_with_name = [model for model in models if model.name]
                if models_with_name:
                    all_models = await invoke.models.list()
                    for model in models_with_name:
                        result = next((m for m in all_models if (m.source == model.source)), None)
                        if result.name != model.name:
                            log.log(f"Rename model: {result.name} -> {model.name}")
                            await invoke.models.update(result.key, name=model.name)


        finally:
            self.lock.release()      


    async def install_nodes(self, nodes: Optional[List[NodeInfo]]):
        if not nodes:
            return
        
        need_reload = False
        try:
            if self.is_storage_use():
                self.lock.acquire()
                
            for node in nodes:
                repo_name = node.git.rstrip('/').split('/')[-1].replace('.git', '')
                target_path = self.nodes_path / repo_name
                if not target_path.exists():
                    need_reload = True
                    target_path.mkdir(parents=True, exist_ok=True)
                    repo = git.Repo.clone_from(node.git, target_path)
                    log.info(f"Repository {node.git} successfully cloned into {repo.working_tree_dir}")

                    requirements_path = target_path / "requirements.txt"
                    if requirements_path.exists():
                        activate_path = self.invoke_path / ".venv/bin/activate"
                        command = f"source {activate_path} && uv pip install -r {requirements_path}"
                        log.info(f"> {command}")
                        result = subprocess.run(command, shell=True, check=True, executable="/bin/bash")
                        log.log(result.stdout)

        finally:
            self.lock.release()

        return need_reload


    def is_storage_use(self):
        return self.invoke_path != self.storage_path


    def init_config(self):
        self._set_config({
            "db_dir": self.invoke_db_path.as_posix(),
            "models_dir": self.models_path.as_posix(),
            "custom_nodes_dir": self.nodes_path.as_posix(),
            "download_cache_dir": self.download_cache_path.as_posix()
        })


    def load_db(self):
        self.init_config()

        if not self.is_storage_use():
            return
        
        log.info("External storage is used")
        self.lock.acquire()
        try:
            # sync: storage -> invoke
            storage_db_path = self.storage_db_path / "invokeai.db"
            invoke_db_path = self.invoke_db_path / "invokeai.db"
            if storage_db_path.is_file():
                log.info(f"Sync: storage ({storage_db_path}) -> invoke ({storage_db_path})")
                shutil.copy2(storage_db_path, invoke_db_path)
        finally:
            self.lock.release()
    

    def save_db(self):
        if not self.is_storage_use():
            return
        
        self.lock.acquire()
        try:
            # sync: storage <- invoke
            storage_db_path = self.storage_db_path / "invokeai.db"
            invoke_db_path = self.invoke_db_path / "invokeai.db"
            log.info(f"Sync: storage ({storage_db_path}) <- invoke ({storage_db_path})")
            shutil.copy2(invoke_db_path, storage_db_path)
        finally:
            self.lock.release()


    def _set_config(self, config: Dict[str, Any]):
        base_config = {
            "schema_version": "4.0.2"
        }

        if len(config) > 0:
            path: Path = self.invoke_path / "invokeai.yaml"
            log.info(f"Set confog: {path}")
            merged_config = {**base_config, **config}
            with open(path, "w") as yaml_file:
                yaml.dump(merged_config, yaml_file, default_flow_style=False)