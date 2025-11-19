from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import ai_api, minio_api
from core.config import settings
from db.session import engine, Base
from object_storage.minio_client import minio_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not minio_client.bucket_exists(settings.MINIO_BUCKET):
        minio_client.make_bucket(settings.MINIO_BUCKET)
        print("Bucket created")
    else:
        print("Bucket already exists")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database connected, tables created")

    yield

    await engine.dispose()
    print("Database disconnected")


app = FastAPI(title="ludicium backend", version="0.1.0", lifespan=lifespan)
app.include_router(ai_api.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(minio_api.router, prefix="/api/v1/minio", tags=["Minio"])


@app.get("/")
async def root():
    return {"message": "Ludicium is running!"}
