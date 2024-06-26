import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.endpoints import router as api_router
from core.config import settings
from core.logging import setup_logging

logger = setup_logging()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(api_router)

if __name__ == "__main__":
    logger.info("Starting server...")
    uvicorn.run(app, host=os.environ.get("HOST"), port=os.environ.get("PORT"))
