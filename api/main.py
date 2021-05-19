from typing import List
from datetime import datetime
from enum import Enum
import wave
import io

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
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


class SpeechModel(str, Enum):
    """The type of glass used for the cocktail."""

    DEFAULT = "default"
    VIDEO = "video"


app = FastAPI()
app.add_middleware(GZipMiddleware)
settings = Settings()
speech_client = speech.SpeechAsyncClient()
storage_client = storage.Client()
bucket = storage_client.get_bucket(settings.BUCKET_NAME)


@app.get("/list/", response_model=List[Blob])
async def list_files():
    """List all files ing Cloud Storage."""

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
    """Uploads a file to Cloud Storage."""
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
async def transcribe_uploaded_file(model: SpeechModel = SpeechModel.DEFAULT, file: UploadFile = File(...)):
    """Uploads a WAV file to Cloud Storage and returns a transcript."""
    # upload blob
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file.file)

    # detect audio info from file
    byte_stream = io.BytesIO(blob.download_as_string())
    reader = wave.open(byte_stream, 'rb')
    params = reader.getparams()
    audio_info = params._asdict()
    audio_info['duration'] = audio_info['nframes'] / float(audio_info['framerate'] * audio_info['nchannels'])
    audio_info['bytes'] = blob.size
    audio_info['file_name'] = blob.name
    audio_info['date'] = blob.updated
    reader.close()


    # configure speech client
    config = speech.RecognitionConfig(
        encoding="LINEAR16",
        sample_rate_hertz=audio_info['framerate'],
        audio_channel_count=audio_info['nchannels'],
        language_code="en-US",
        profanity_filter=True,
        enable_word_time_offsets=True,
        model=model,
    )

    # give it blob pointer
    audio = speech.RecognitionAudio(
        uri=f"gs://{settings.BUCKET_NAME}/{blob.name}"
    )

    try:
    # do async long-running recognize operation
        operation = await speech_client.long_running_recognize(config=config, audio=audio)
        response = await operation.result(timeout=90)

        transcript = ""
        blocks = []
        # generate transcript from reponse blocks and print info
        for result in response.results:
            # The first alternative is the most likely one for this portion.
            # print(u"Transcript: {}".format(result.alternatives[0].transcript))
            # print("Confidence: {}".format(result.alternatives[0].confidence))

            words = []
            # Go through the words and get their times
            for i in result.alternatives[0].words:
                words.append(
                    {
                        "word": i.word,
                        "start": i.start_time.total_seconds(),
                        "end": i.end_time.total_seconds()
                    }
                )
                # print(f"Words: {i.word} at {i.start_time.total_seconds()}")

            blocks.append(
                {
                    # "speaker": result.alternatives[0].speaker_tag,
                    "text": result.alternatives[0].transcript,
                    "confidence": result.alternatives[0].confidence,
                    "words": words
                }
            )
            # Append to transcript string
            transcript += result.alternatives[0].transcript

        return {
            "id": blob.id,
            "public_url": blob.public_url,
            "audio_info": audio_info,
            # "transcript_full": transcript,
            "transcription": {
                "vendor": "google",
                "model": model,
                "blocks": blocks,
            }
        }

    except Exception as error:
        print(error)
        if hasattr(error, "message"):
            raise HTTPException(status_code=400, detail=error.message)
        else:
            raise HTTPException(status_code=400, detail="Error transcribing audio")
