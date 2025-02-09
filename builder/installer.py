import os
import argparse
import asyncio
import shutil
import git
import subprocess
from pathlib import Path
from typing import List
from invoke import Invoke
from config_install import ConfigInstall
from file_manager import FileManager


async def copy_files(path: str, invoke_path: Path, temp: Path):
    path = await FileManager.get_files(path, temp)
    if os.path.isdir(path):
        FileManager.merge_directories(path, invoke_path)
        return
    
    if os.path.isfile(path):
        shutil.copy2(path, invoke_path)
        return
    
    raise Exception("copy_files WTF")


async def install_model(invoke: Invoke, path: str, temp: Path):
    path = await FileManager.get_files(path, temp)

    if os.path.isdir(path):   
        print(f"Scan folder: {path}")
        scanned_models = await invoke.models.scan_folder(path)
        not_installed_models = [model.path for model in scanned_models if not model.is_installed]
        for model in not_installed_models:
            print(f"Install model from folder: {model}")
            await invoke.models.install(model, inplace=False)
        return
    
    if os.path.isfile(path):
        print(f"Install model from file: {path}")
        await invoke.models.install(path, inplace=False)
        return
    
    raise Exception("install_model WTF")
    


async def pip_install(pip_list: List[str], invoke_path: Path):
    pip_list = [pkg for pkg in [pkg.strip() for pkg in pip_list] if pkg]
    if pip_list:  
        pip_install_str = ' '.join(pip_list)
        activate_path = invoke_path / ".venv/bin/activate"
        command = f"source {activate_path.resolve()} && uv pip install {pip_install_str}"
        print(f"> uv pip install {pip_install_str}")
        result = subprocess.run(command, shell=True, check=True, executable="/bin/bash")
        print(result.stdout)



async def install_nodes_git(repo_url: str, nodes_path: Path):
    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    target_path = nodes_path / repo_name

    if not target_path.exists():
        target_path.mkdir(parents=True, exist_ok=True)

    repo = git.Repo.clone_from(repo_url, target_path)
    print(f"Repository {repo_url} successfully cloned into {repo.working_tree_dir}")



async def install(invoke: Invoke, invoke_path: Path, builder_path: Path, config: ConfigInstall): 
    temp_path = builder_path / ".temp"
    nodes_path = invoke_path / "nodes"

    if not os.path.exists(nodes_path):
        os.makedirs(nodes_path)

    for path in config.copy:
        print("Copy files")
        await copy_files(path, invoke_path, temp_path)
        print("All files copied")

    for path in config.models:
        print("Install models")
        await invoke.models.prune_completed_jobs()
        await install_model(invoke, path, temp_path)

    if config.models:
        print("Wait install models...")
        await invoke.wait_install_models(raise_on_error=True)
        print("All models installed")

    if config.pip_nodes:
        print("Install pip requirements for nodes")
        await pip_install(config.pip_nodes, invoke_path)
        print("All pip requirements installed")

    for repo_url in config.git_nodes:
        print("Install nodes from git")
        await install_nodes_git(repo_url, nodes_path)
        print("All nodes installed")

    if config.node_requirements:
        node_directories = [name for name in os.listdir(nodes_path) if os.path.isdir(os.path.join(nodes_path, name))]
        for node in node_directories:
            requirements_path = nodes_path / node / "requirements.txt"
            if os.path.exists(requirements_path):
                print(f"pip requirements for {node}")
                with open(requirements_path, 'r', encoding='utf-8') as file:
                    await pip_install(file.readlines(), invoke_path)



async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--invoke", type=str, required=True)
    parser.add_argument("--builder", type=str, required=True)
    args = parser.parse_args()
    config = ConfigInstall(args.config)
    invoke_path = Path(args.invoke).resolve()
    builder_path = Path(args.builder).resolve()

    async with Invoke() as invoke:
        print(f"==== Install start ====")
        print(f"config: {args.config}")
        print(f"invoke: {args.invoke}; invoke_path: {invoke_path}")
        print(f"builder: {args.builder}; builder_path: {builder_path}")
        print("Wait InvokeAI")
        version = await invoke.wait_invoke()
        print(f"InvokeAI Version = {version}")
        await install(
            invoke=invoke, 
            invoke_path=invoke_path, 
            builder_path=builder_path, 
            config=config
        )
        print(f"==== Install done ====")



if __name__ == "__main__":
    asyncio.run(main())