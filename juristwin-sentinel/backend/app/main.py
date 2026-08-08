from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from .core.config import get_settings
from .db.database import Base, engine, SessionLocal
from .db.seed import seed_database
from .routers import auth, system, dashboard, cases, conflicts, simulations, approvals, memory, ledger, bodyguard, integrations, search, demo

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(title="JurisTwin Sentinel API", version="1.6.0", description="Grand Finals live decision intelligence and governance system", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for router in [auth.router, system.router, dashboard.router, cases.router, conflicts.router, simulations.router, approvals.router, memory.router, ledger.router, bodyguard.router, integrations.router, search.router, demo.router]:
    app.include_router(router, prefix=settings.API_PREFIX)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def root(): return RedirectResponse("/finals")

@app.get("/finals", include_in_schema=False)
def finals(): return FileResponse(STATIC_DIR / "finals.html")
