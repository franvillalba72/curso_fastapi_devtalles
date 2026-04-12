import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.auth.router import router as auth_router
from app.api.v1.posts.router import router as posts_router
from app.api.v1.uploads.router import router as upload_router
from app.api.v1.tags.router import router as tags_router
from app.core.db import Base, engine

load_dotenv()

MEDIA_DIR = "app/media"


def create_app() -> FastAPI:
    app = FastAPI(title="Mini Blog", version="1.0")

    # Solo desarrollo, en producción se usaría Alembic para migraciones
    Base.metadata.create_all(bind=engine)

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(upload_router, prefix="/api/v1")
    app.include_router(posts_router, prefix="/api/v1")
    app.include_router(tags_router, prefix="/api/v1")

    os.makedirs(MEDIA_DIR, exist_ok=True)  # Asegura que el directorio exista
    app.mount(
        "/media", StaticFiles(directory=MEDIA_DIR), name="media"
    )  # Monta el directorio de media para servir archivos estáticos en localhost:8000/media/filename.ext

    return app


app = create_app()
