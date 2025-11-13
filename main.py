from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

from api import ai_api
from db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Database connected, tables created")
    yield
    await engine.dispose()
    print("Database disconnected")

app = FastAPI(title="ludicium backend", version="0.1.0", lifespan=lifespan)
app.include_router(ai_api.router, prefix="/api/v1/ai", tags=["AI"])

@app.get("/")
async def root():
    return {"message": "Ludicium is running!"}
