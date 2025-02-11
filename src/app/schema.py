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


class NodeInfo(BaseModel):
    git: str
    commit: Optional[str] = None
    update: bool = False


class ModelInfo(BaseModel):
    source: str
    name: Optional[str] = None
    hash: Optional[str] = None
    access_token: Optional[str] = None
    update: bool = False


class JobTask(BaseModel):
    images: Optional[List[ImageInfo]] = None
    graph: str
    nodes: Optional[List[NodeInfo]] = None
    models: Optional[List[ModelInfo]] = None
    hugging_face_token: Optional[str] = None


class ResponseTask(BaseModel):
    error: Optional[str] = None
    images: Optional[List[ImageInfo]] = None
    meta_data: Optional[Any] = None