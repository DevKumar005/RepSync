import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.app.api.endpoints import router
from backend.app.db import init_db
from backend.app.limiter import limiter

# Load environment
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Setup Logging (M3-API-7)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("repsync.api")




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and platforms are seeded (M3-DB-1, M3-DB-4)
    init_db()
    try:
        from sqlmodel import Session
        from backend.app.db import engine
        from backend.app.seed import seed_platforms, seed_demo_outlets, seed_demo_user
        with Session(engine) as session:
            seed_platforms(session)
            user = seed_demo_user(session)
            seed_demo_outlets(session, user)
        logger.info("Database initialized and seeded successfully on startup.")
    except Exception as e:
        logger.warning(f"Auto-seed during startup notice: {e}")
    yield


app = FastAPI(
    title="RepSync API",
    description="Local Business Multi-Platform Reputation Manager API (KRITICAL HACKS'26)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Correlation ID and Request Logging Middleware (M3-API-7)
@app.middleware("http")
async def correlation_id_and_logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    t0 = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - t0) * 1000)
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(
        f"cid={correlation_id} method={request.method} path={request.url.path} "
        f"status={response.status_code} duration_ms={duration_ms}"
    )
    return response


# CORS configuration (M3-API-2)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
if FRONTEND_ORIGIN and FRONTEND_ORIGIN not in origins:
    origins.append(FRONTEND_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Consistent error response shape: {error, detail, code} (M3-API-3)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "HTTP Exception",
            "detail": exc.detail,
            "code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "code": 422,
        },
    )


# Register all API endpoints
app.include_router(router)

