from typing import List
from datetime import datetime

from fastapi import FastAPI, UploadFile
from pydantic import BaseModel, BaseSettings
from google.cloud import storage


class Settings(BaseSettings):
    BUCKET_NAME: str = "Awesome Bucket"


class Blob(BaseModel):
    id: str
    content_type: str
    size: int
    self_link: str
    media_link: str
    public_url: str
    updated_time: datetime


app = FastAPI()
settings = Settings()
storage_client = storage.Client()
bucket = storage_client.get_bucket(settings.BUCKET_NAME)


@app.get("/list/", response_model=List[Blob])
async def list_files():
    blob_list = []
    for blob in storage_client.list_blobs(bucket):
        blob_list.append(
            {
                "id": blob.id,
                "content_type": blob.content_type,
                "size": blob.size,
                "self_link": blob.self_link,
                "media_link": blob.media_link,
                "public_url": blob.public_url,
                "updated_time": blob.updated,
            }
        )
    return blob_list


@app.post("/upload/", response_model=Blob)
async def create_upload_file(file: UploadFile = File(...)):
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file.file)

    return {
        "id": blob.id,
        "content_type": blob.content_type,
        "size": blob.size,
        "self_link": blob.self_link,
        "media_link": blob.media_link,
        "public_url": blob.public_url,
        "updated_time": blob.updated,
    }
