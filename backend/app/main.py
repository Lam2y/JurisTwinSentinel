from contextlib import asynccontextmanager
from pathlib import Path
import logging
import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .core.config import get_settings
from .db.database import Base, SessionLocal, engine
from .db.seed import seed_database
from .routers import admin, ask, auth, governance, integration
from .services.policy_ml import get_policy_ai
from .services.retention import apply_resolved_gap_retention

settings = get_settings()
logger = logging.getLogger("juristwin")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _windows.clear()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        apply_resolved_gap_retention(db, actor="system-startup")
        get_policy_ai()  # warm the local learned layer before the first live question
    finally:
        db.close()
    yield


app = FastAPI(
    title="JurisTwin Sentinel API",
    version=settings.VERSION,
    description="Contradiction-safe enterprise decision memory with human governance, runtime evidence intake, resilience controls and measurable adoption telemetry.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "X-Request-ID"])

_windows: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def hardening(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"JT-{uuid4().hex[:10].upper()}"
    request.state.request_id = request_id
    started = time.perf_counter()

    # Production transfer/data routes fail closed when TLS is required. Reverse proxies may
    # terminate TLS and forward X-Forwarded-Proto=https. Local finals demo remains loopback HTTP.
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    if settings.REQUIRE_HTTPS and request.url.scheme != "https" and forwarded_proto != "https":
        response = JSONResponse(status_code=426, content={"detail": "HTTPS/TLS is required for this JurisTwin deployment.", "request_id": request_id})
        response.headers["X-Request-ID"] = request_id
        return response

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.MAX_REQUEST_BYTES:
                response = JSONResponse(status_code=413, content={"detail": "Request is too large for the governed API boundary.", "request_id": request_id})
                response.headers["X-Request-ID"] = request_id
                return response
        except ValueError:
            pass

    now = time.monotonic()
    key = f"{request.client.host if request.client else 'unknown'}:{request.url.path}"
    q = _windows[key]
    while q and now - q[0] > 60:
        q.popleft()
    limit = 12 if request.url.path.endswith("/auth/login") else 180
    if len(q) >= limit:
        response = JSONResponse(status_code=429, content={"detail": "Too many requests. Please retry shortly.", "request_id": request_id})
        response.headers["Retry-After"] = "2"
    else:
        q.append(now)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled JurisTwin error %s", request_id)
            response = JSONResponse(status_code=500, content={"detail": "JurisTwin contained an unexpected error without publishing a new decision.", "request_id": request_id})

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter()-started)*1000:.2f}"
    response.headers["X-JurisTwin-Governed"] = "true"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={
        "detail": "Please check the highlighted input and try again.",
        "request_id": getattr(request.state, "request_id", None),
        "errors": [{"field": ".".join(str(x) for x in e.get("loc", [])[1:]), "message": e.get("msg")} for e in exc.errors()],
    })


for router in [auth.router, ask.router, admin.router, governance.router, integration.router]:
    app.include_router(router, prefix=settings.API_PREFIX)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/finals")


@app.get("/finals", include_in_schema=False)
def finals():
    return FileResponse(STATIC_DIR / "finals.html")
