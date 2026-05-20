from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sentry_sdk import init as sentry_init
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.scripts.bootstrap import main as bootstrap_main
from app.utils.rate_limit import limiter, rate_limit_exception_handler

setup_logging()

if settings.sentry_dsn:
    sentry_init(dsn=settings.sentry_dsn, traces_sample_rate=settings.sentry_traces_sample_rate)

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"
STATIC_DIR = FRONTEND_DIR / "static"

@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_main()
    yield


app = FastAPI(title="VR Garage API", version="2.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "assets")), name="assets")
app.mount("/admin", StaticFiles(directory=str(BASE_DIR / "admin"), html=True), name="admin")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/")
def root() -> FileResponse:
    return FileResponse(PAGES_DIR / "index.html")


@app.get("/index.html")
def root_index() -> FileResponse:
    return FileResponse(PAGES_DIR / "index.html")


@app.get("/catalog")
def catalog_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "catalog.html")


@app.get("/catalog.html")
def catalog_html() -> FileResponse:
    return FileResponse(PAGES_DIR / "catalog.html")


@app.get("/about")
def about_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "about.html")


@app.get("/about.html")
def about_html() -> FileResponse:
    return FileResponse(PAGES_DIR / "about.html")


@app.get("/contacts")
def contacts_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "contacts.html")


@app.get("/contacts.html")
def contacts_html() -> FileResponse:
    return FileResponse(PAGES_DIR / "contacts.html")


@app.get("/faq")
def faq_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "faq.html")


@app.get("/faq.html")
def faq_html() -> FileResponse:
    return FileResponse(PAGES_DIR / "faq.html")


@app.get("/car")
def car_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "car.html")


@app.get("/car.html")
def car_html() -> FileResponse:
    return FileResponse(PAGES_DIR / "car.html")


@app.get("/vr-test")
def vr_test_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "vr-test.html")


@app.get("/vr-test.html")
def vr_test_html() -> FileResponse:
    return FileResponse(PAGES_DIR / "vr-test.html")
