import os
import asyncio
import runpod
import traceback
import argparse
from pathlib import Path
from runpod import RunPodLogger
from typing import List
from invoke import Invoke
from invoke.graph_builder.components import Batch, BatchRoot, Graph
from invoke.api.images import Categories
from app.schema import *
from app.image_processor import ImageProcessor
from app.invoke_manager import InvokeManager
from concurrent.futures import ThreadPoolExecutor

log = RunPodLogger()


async def handler(task: JobTask, invoke_path: Path) -> ResponseTask:
    async with Invoke() as invoke:
        # Image file manager
        log.debug("Create Invoke manager")
        storage_path=os.environ.get('STORAGE_PATH', None)
        manager = InvokeManager(
            invoke_path=invoke_path,
            storage_path=Path(storage_path) if storage_path else None
        )

        # Install requirements
        if task.models or task.nodes:
            await manager.install_models(task.models)
            need_reload = await manager.install_nodes(task.nodes)
            manager.save_db()


        # Image file manager
        log.debug("Create Image file manager")
        image_processor = ImageProcessor(
            bucket_name=os.environ.get('BUCKET_NAME', None),
            endpoint_url=os.environ.get('BUCKET_ENDPOINT_URL', None),
            aws_access_key_id=os.environ.get('BUCKET_ACCESS_KEY_ID', None),
            aws_secret_access_key=os.environ.get('BUCKET_SECRET_ACCESS_KEY', None)
        )

        # Create batch
        log.debug("Create batch")
        batch = Batch(
            graph=Graph.model_validate_json(task.graph)
        )

        # Update and validate models hash
        log.debug("Update and validate models hash")
        all_models = await invoke.models.list()
        if not all_models:
            raise Exception("Failed to get models list")
        for record in all_models:
            log.debug(f"{record.base}:{record.type}:{record.name}")
        batch.update_models_hash(all_models)
            
        # Clear
        log.debug("Clear")
        old_images = await invoke.images.list_image_dtos(offset=0, limit=1000)
        old_images_names = [item.image_name for item in old_images.items]
        for record in old_images_names:
            log.debug(f"Delete: {record}")
        await invoke.images.delete_by_list(old_images_names)
        await invoke.queue.clear()
        await invoke.images.clear_intermediates()
        await invoke.app.clear_invocation_cache()
        
        # Upload images
        log.debug("Upload images")
        # TODO add ThreadPoolExecutor 
        upload_images: List[str] = []
        if task.images:        
            download_images = image_processor.download_images(task.images)
            for item in download_images:
                log.debug(f"Image download: {item.id}")
                image = await invoke.images.upload(item.data, Categories.User)
                batch.graph.nodes[item.id]["image"] = {
                    "image_name": image.image_name
                }
                upload_images.append(image.image_name)

        # Run batch
        log.debug("Run batch")
        batch_root = BatchRoot(batch=batch).model_dump_json()
        enqueue_batch = await invoke.queue.enqueue_batch(batch_root)
        log.debug("Wait... batch")
        await invoke.wait_batch(enqueue_batch)

        # Delete upload images
        log.debug("Delete upload images")
        if upload_images:
            log.debug("upload_images")
            await invoke.images.delete_by_list(upload_images)

        # Get last generate images
        log.debug("Get last generate images")
        last_images = await invoke.images.list_image_dtos(offset=0, limit=1000)

        # Upload last generate images
        log.debug("Upload last generate images")
        generate_images: List[ImageData] = []
        for item in last_images.items:
            if not item.is_intermediate:
                item_data = await invoke.images.get_full(item.image_name)
                generate_images.append(ImageData(
                    data=item_data, 
                    id=item.image_name
                ))
        out_images = image_processor.upload_images(generate_images)

        # Delete last generate images
        log.debug("Delete last generate images")
        await invoke.images.delete_by_list([item.image_name for item in last_images.items])
        
        return ResponseTask(
            images=out_images
        )


def create_handler(job):
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--invoke", type=str, required=True)
        args = parser.parse_args()

        log.info("Start job")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with ThreadPoolExecutor() as executor:
            future = executor.submit(loop.run_until_complete, handler(
                invoke_path=Path(args.invoke),
                task=JobTask.model_validate(job['input'])
            ))
            response: ResponseTask = future.result()
            log.info("Done")
            return response.model_dump()
    except Exception as e:
        return ResponseTask(
            error=str(e), 
            meta_data={
                "error": str(e), 
                "traceback": traceback.format_exc()
            }
        ).model_dump()
        

async def setup():
    async with Invoke() as invoke:
        log.info("Wait InvokeAI...")
        version = await invoke.wait_invoke()
        log.info(f"version = {version}")


def main():
    asyncio.run(setup())
    runpod.serverless.start({"handler": create_handler})


if __name__ == "__main__":
    main()