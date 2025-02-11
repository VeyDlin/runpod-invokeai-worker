import os
import argparse
from pathlib import Path
from app.invoke_manager import InvokeManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoke", type=str, required=True)
    args = parser.parse_args()
    
    storage_path=os.environ.get('STORAGE_PATH', None)
    manager = InvokeManager(
        invoke_path=Path(args.invoke),
        storage_path=Path(storage_path) if storage_path else None
    )
    manager.load_db()


if __name__ == "__main__":
    main()