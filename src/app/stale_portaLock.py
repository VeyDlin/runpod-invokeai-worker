import portalocker
from pathlib import Path
import time
import os
import json


class StalePortaLock:
    def __init__(self, path: Path, stale_threshold=600):
        self.lock_path = (path / ".lock").resolve()
        self.data_path = (path / ".lock.data").resolve()
        self.stale_threshold = stale_threshold
        self.lock = None
        self.timeout = None
        
    def _write_lock_data(self):
        data = {
            'timestamp': time.time(),
            'pid': os.getpid()
        }
        with open(self.data_path, 'w') as f:
            json.dump(data, f)
            
    def _read_lock_data(self):
        try:
            with open(self.data_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
            
    def _is_stale(self):
        data = self._read_lock_data()
        if not data:
            return True
        lock_time = data.get('timestamp', 0)
        return (time.time() - lock_time) > self.stale_threshold
        
    def acquire(self, timeout=None):
        timeout = timeout if timeout else self.timeout
        start_time = time.time()
        
        while True:
            if self._is_stale():
                try:
                    os.remove(self.lock_path)
                    os.remove(self.data_path)
                except FileNotFoundError:
                    pass
            
            try:
                self.lock = open(self.lock_path, 'wb')
                portalocker.lock(self.lock, portalocker.LOCK_EX | portalocker.LOCK_NB)
                self._write_lock_data()
                return True
            except (portalocker.LockException, OSError):
                if self.lock:
                    self.lock.close()
                    self.lock = None
                
                if timeout is not None:
                    if time.time() - start_time >= timeout:
                        raise TimeoutError(f"Could not acquire lock on {self.lock_path} within {timeout} seconds")
                
                time.sleep(0.1)
        
    def release(self):
        if self.lock:
            try:
                os.remove(self.data_path)
            except FileNotFoundError:
                pass
            portalocker.unlock(self.lock)
            self.lock.close()
            self.lock = None
            
    def __enter__(self):
        self.acquire()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()