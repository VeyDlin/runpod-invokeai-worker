import os
import json
import argparse
from pathlib import Path
from app.invoke_manager import InvokeManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoke", type=str, required=True)
    args = parser.parse_args()
    invoke_path = Path(args.invoke)
    invoke_log_path = invoke_path / "invokeai.log"

    # Clear old log
    if invoke_log_path.exists():
        invoke_log_path.unlink()

    # Create InvokeManager
    storage_path=os.environ.get('STORAGE_PATH', None)
    manager = InvokeManager(
        invoke_path=Path(args.invoke),
        storage_path=Path(storage_path) if storage_path else None
    )

    # Set user invokeai config
    user_config = os.environ.get('INVOKEAI_CONFIG', None)
    if user_config:
        user_config = json.loads(user_config)

    # Init invokeai config
    manager.init_config(user_config)
    
    # Sync DB
    manager.load_db()


if __name__ == "__main__":
    main()