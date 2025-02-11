import base64
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from PIL import Image
from io import BytesIO
from .schema import ImageInfo, ImageData


class ImageProcessor:
    def __init__(self, bucket_name=None, endpoint_url=None, aws_access_key_id=None, aws_secret_access_key=None):
        self.bucket_client = None
        self.bucket_name = None

        if bucket_name and endpoint_url and aws_access_key_id and aws_secret_access_key:
            self.bucket_name = bucket_name
            self.bucket_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )


    def download_images(self, images: List[ImageInfo]) -> List[ImageData]:
        results = []

        with ThreadPoolExecutor() as executor:
            futures = []
            for image in images:
                if image.cdn_id and image.base64:
                    raise ValueError(f"Both 'cdn_id' and 'base64' provided for id {image.id}.")
                elif image.cdn_id:
                    if not self.bucket_client:
                        raise ValueError("Bucket configuration is missing but 'cdn_id' is provided.")
                    futures.append(executor.submit(self._download_from_cdn, image))
                elif image.base64:
                    futures.append(executor.submit(self._decode_base64, image))
                else:
                    raise ValueError(f"No valid data source ('cdn_id' or 'base64') for id {image.id}.")

            for future in as_completed(futures):
                results.append(future.result())

        return results


    def upload_images(self, images: List[ImageData]) -> List[ImageInfo]:
        results = []

        with ThreadPoolExecutor() as executor:
            futures = []
            for image in images:
                if self.bucket_client:
                    futures.append(executor.submit(self._upload_to_cdn, image))
                else:
                    futures.append(executor.submit(self._encode_base64, image))

            for future in as_completed(futures):
                results.append(future.result())

        return results


    def _download_from_cdn(self, image: ImageInfo) -> ImageData:
        try:
            response = self.bucket_client.get_object(Bucket=self.bucket_name, Key=image.cdn_id)
            data = response['Body'].read()
            return ImageData(data=data, id=image.id)
        except (BotoCoreError, NoCredentialsError) as e:
            raise RuntimeError(f"Failed to download image with cdn_id {image.cdn_id}: {e}")


    def _decode_base64(self, image: ImageInfo) -> ImageData:
        try:
            data = base64.b64decode(image.base64)
            return ImageData(data=data, id=image.id)
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to decode base64 for id {image.id}: {e}")


    def _upload_to_cdn(self, image: ImageData) -> ImageInfo:
        try:
            data = self._get_image_data(image)
            key = self._generate_image_key(image.data)
            self.bucket_client.put_object(Bucket=self.bucket_name, Key=key, Body=data)

            return ImageInfo(cdn_id=key, id=image.id)
        except (BotoCoreError, NoCredentialsError) as e:
            raise RuntimeError(f"Failed to upload image for id {image.id}: {e}")


    def _encode_base64(self, image: ImageData) -> ImageInfo:
        try:
            data = self._get_image_data(image)
            encoded_data = base64.b64encode(data).decode('utf-8')
            return ImageInfo(base64=encoded_data, id=image.id)
        except Exception as e:
            raise RuntimeError(f"Failed to encode base64 for id {image.id}: {e}")


    def _fetch_data_from_url(self, url: str) -> bytes:
        import requests
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch data from URL {url}: {e}")


    def _generate_image_key(self, data: bytes) -> str:
        try:
            image = Image.open(BytesIO(data))
            image_format = image.format.lower()  # Determine image format (e.g., jpg, png)
            return f"{uuid.uuid4()}.{image_format}"
        except Exception as e:
            raise RuntimeError(f"Failed to generate image key from data: {e}")
        

    def _get_image_data(self, image: ImageData) -> bytes:
        if image.data:
            return image.data
        elif image.download_url:
            return self._fetch_data_from_url(image.download_url)
        else:
            raise ValueError(f"No data or download_url provided for id {image.id}.")
