from pathlib import Path
from contextlib import asynccontextmanager
import logging
import time
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from .core.config import get_settings
from .services.observability import telemetry, rate_limiter
from .services.policy_ml import get_policy_ai
from .db.database import Base, engine, SessionLocal
from .db.seed import seed_database
from .routers import auth, system, dashboard, cases, conflicts, simulations, approvals, memory, ledger, bodyguard, integrations, search, demo, live, assurance

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        # Warm the local learned NLP layer before judges interact with Evidence Lab. The model is
        # retrained from the bundled labelled corpus and remains fully offline.
        get_policy_ai()
    finally:
        db.close()
    yield

app = FastAPI(title="JurisTwin Sentinel API", version="5.5.0", description="JurisTwin Sentinel decision assurance, policy reasoning, live evidence challenge, impact intelligence and governed decision system", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

logger = logging.getLogger("juristwin")

@app.middleware("http")
async def request_trace(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"JT-{uuid4().hex[:10].upper()}"
    request.state.request_id = request_id
    started = time.perf_counter()

    # Production-style containment without introducing a fragile external gateway dependency.
    client = request.client.host if request.client else "unknown"
    path = request.url.path
    if path.startswith("/api/auth/login"):
        limit = 30
    elif request.method.upper() not in {"GET", "HEAD", "OPTIONS"}:
        limit = 180
    else:
        limit = 600
    allowed, retry_after = rate_limiter.allow(f"{client}:{path}", limit=limit, window_seconds=60)
    if not allowed:
        response = JSONResponse(status_code=429, content={
            "detail":"Sentinel rate containment activated",
            "request_id":request_id,
            "retry_after_seconds":retry_after,
        })
        response.headers["Retry-After"] = str(retry_after)
    else:
        response = await call_next(request)

    elapsed = round((time.perf_counter()-started)*1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    response.headers["X-JurisTwin-Governed"] = "true"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'"
    telemetry.record(request.method, path, response.status_code, elapsed, request_id)
    return response

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail":"Input rejected by Sentinel validation",
            "request_id":getattr(request.state,"request_id",None),
            "errors":[{
                "field":".".join(str(x) for x in e.get("loc",[])[1:]),
                "message":e.get("msg"),
                "type":e.get("type"),
            } for e in exc.errors()],
        },
    )

@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    request_id = getattr(request.state,"request_id",f"JT-{uuid4().hex[:10].upper()}")
    logger.exception("Unhandled JurisTwin error %s", request_id)
    return JSONResponse(
        status_code=500,
        content={
            "detail":"Sentinel contained an unexpected error; approved state was not intentionally changed.",
            "request_id":request_id,
        },
    )


for router in [auth.router, system.router, dashboard.router, cases.router, conflicts.router, simulations.router, approvals.router, memory.router, ledger.router, bodyguard.router, integrations.router, search.router, demo.router, live.router, assurance.router]:
    app.include_router(router, prefix=settings.API_PREFIX)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def root(): return RedirectResponse("/finals")

@app.get("/finals", include_in_schema=False)
def finals(): return FileResponse(STATIC_DIR / "finals.html")

@app.get("/favicon.ico", include_in_schema=False)
def favicon(): return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")
