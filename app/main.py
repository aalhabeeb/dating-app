import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
import os

from .routers import auth_router, profiles_router, matches_router, admin_router, photos_router

STATIC_DIR = pathlib.Path(__file__).parent / "static"
UPLOAD_DIR = pathlib.Path(os.getenv("UPLOAD_DIR", "/uploads"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic for production migrations)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Dating App API",
    description="Een dating app API met profielen, swipen en matches",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(profiles_router.router)
app.include_router(matches_router.router)
app.include_router(admin_router.router)
app.include_router(photos_router.router)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin", include_in_schema=False)
def admin_page():
    return FileResponse(STATIC_DIR / "admin.html")
