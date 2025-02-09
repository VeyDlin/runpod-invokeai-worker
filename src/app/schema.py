# Path: app\schema.py
from pydantic import BaseModel
from typing import List, Optional, Any


class ImageData(BaseModel):
    data: Optional[bytes] = None
    download_url: Optional[str] = None
    id: str


class ImageInfo(BaseModel):
    cdn_id: Optional[str] = None
    base64: Optional[str] = None
    id: str


class JobTask(BaseModel):
    images: Optional[List[ImageInfo]] = None
    graph: str


class ResponseTask(BaseModel):
    error: Optional[str] = None
    images: Optional[List[ImageInfo]] = None
    meta_data: Optional[Any] = None