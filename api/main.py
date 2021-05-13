from typing import List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, BaseSettings
from google.cloud import storage
from google.cloud import speech

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
speech_client = speech.SpeechAsyncClient()
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


@app.post("/transcribe/")
async def transcribe_uploaded_file(file: UploadFile = File(...)):
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file.file)

    config = speech.RecognitionConfig(
        encoding="LINEAR16",
        sample_rate_hertz=44100,
        # audio_channel_count=2,
        language_code="en-US",
    )
    audio = speech.RecognitionAudio(
        uri=f"gs://{settings.BUCKET_NAME}/{blob.name}"
    )

    operation = await speech_client.long_running_recognize(config=config, audio=audio)
    response = await operation.result(timeout=90)
    
    transcript = ""

    for result in response.results:
        # The first alternative is the most likely one for this portion.
        print(u"Transcript: {}".format(result.alternatives[0].transcript))
        print("Confidence: {}".format(result.alternatives[0].confidence))
        transcript += result.alternatives[0].transcript

    return transcript
