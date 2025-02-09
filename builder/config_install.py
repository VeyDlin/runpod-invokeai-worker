from typing import List, Dict, Union, Any
import requests
import yaml


class ConfigInstall:
    def __init__(self, config_path: str):
        self.config_data = self.load_config(config_path)
        self.copy: List[str] = self.config_data.get("copy", [])
        self.nodes: Dict[str, Union[List[str], bool]] = self.config_data.get("nodes", {})
        self.models: List[str] = self.config_data.get("models", [])

        self.git_nodes: List[str] = self.nodes.get("git", [])
        self.pip_nodes: List[str] = self.nodes.get("pip", [])
        self.node_requirements: bool = self.nodes.get("node_requirements", True)

    def load_config(self, config_path: str) -> Dict[str, Any]:
        if config_path.startswith("http://") or config_path.startswith("https://"):
            response = requests.get(config_path)
            response.raise_for_status()
            config_data = yaml.safe_load(response.text)
        else:
            with open(config_path, 'r') as file:
                config_data = yaml.safe_load(file)
        return config_data

    def __repr__(self):
        return (f"ConfigInstall(copy={self.copy}, nodes={self.nodes}, models={self.models}, "
                f"git_nodes={self.git_nodes}, pip_nodes={self.pip_nodes}, node_requirements={self.node_requirements})")
