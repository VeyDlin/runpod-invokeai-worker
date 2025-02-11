import os
import aiohttp
import zipfile
import tarfile
import shutil
from pathlib import Path
from runpod import RunPodLogger

log = RunPodLogger()


class FileManager:
    @staticmethod
    async def download_file(url: str, dest: str) -> str:
        log.log(f"Starting download from '{url}'")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                filename = url.split("/")[-1]
                file_path = os.path.join(dest, filename)
                base, ext = os.path.splitext(file_path)
                counter = 1
                while os.path.exists(file_path):
                    file_path = f"{base}_{counter}{ext}"
                    counter += 1
                with open(file_path, 'wb') as f:
                    f.write(await response.read())
                log.log(f"Downloaded file to '{file_path}'")
                return file_path

    @staticmethod
    def extract_archive(file_path: str, dest: str) -> str:
        log.log(f"Extracting archive {file_path}")
        filename = os.path.basename(file_path)
        extract_path = os.path.join(dest, filename + "_extracted")
        counter = 1
        while os.path.exists(extract_path):
            extract_path = os.path.join(dest, f"{filename}_extracted_{counter}")
            counter += 1
        os.makedirs(extract_path, exist_ok=True)

        if zipfile.is_zipfile(file_path):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
                log.log(f"Extracted zip file to '{extract_path}'")
        elif tarfile.is_tarfile(file_path):
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_path)
                log.log(f"Extracted tar file to '{extract_path}'")
        else:
            raise ValueError(f"Unsupported archive format: '{file_path}'")

        os.remove(file_path)
        log.log(f"Removed archive file {file_path}")

        return extract_path
    
    @staticmethod
    def merge_directories(src: str, dest: str):
        log.log(f"Merging directories from '{src}' to '{dest}'")
        for root, dirs, files in os.walk(src):
            relative_path = os.path.relpath(root, src)
            dest_dir = os.path.join(dest, relative_path)
            os.makedirs(dest_dir, exist_ok=True)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                shutil.copy2(src_file, dest_file)
                log.log(f"Copied {src_file} to {dest_file}")

    @staticmethod
    async def get_files(path: str, temp: str) -> Path:
        log.log(f"Getting files from '{path}' to '{temp}'")
        os.makedirs(temp, exist_ok=True)

        if path.startswith("http://") or path.startswith("https://"):
            path = await FileManager.download_file(path, temp)

        if os.path.isfile(path):
            if zipfile.is_zipfile(path) or tarfile.is_tarfile(path):
                path = FileManager.extract_archive(path, temp)

        path = Path(path).resolve()
        log.log(f"Final path is {path}")
        return path