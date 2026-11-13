import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import structlog

# Structlog production-structured logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ]
)

app = FastAPI(
    title="FieldShift API",
    version="0.1.0",
    docs_url="/api/docs" if os.getenv("APP_ENV") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("APP_ENV") != "production" else None,
)

# Production security middleware
if os.getenv("APP_ENV") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["your-domain.com", ".your-domain.com"],
    )

# CORS - production-ready configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    allow_origins_regex=None,
    max_age=86400,
)

# Structured request logging middleware
@app.middleware("http")
async def structured_logging(request: Request, call_next):
    import time
    start time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    structlog.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        process_time=f"{process_time:.3f}",
        client_host=request.client.host,
        client_port=request.client.port,
        env=os.getenv("APP_ENV", "development"),
    )
    return response

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "path": request.url.path},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    structlog.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "path": request.url.path},
    )


@app.get("/")
def root():
    {"status": "ok", "environment": os.getenv("APP_ENV", "development")}


@app.get("/health")
def health_check():
    {"status": "healthy", "environment": os.getenv("APP_ENV", "development")}