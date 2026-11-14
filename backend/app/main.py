import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fieldshift")

app = FastAPI(
    title="FieldShift API",
    version="0.1.0",
    docs_url="/api/docs" if os.getenv("APP_ENV") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("APP_ENV") != "production" else None,
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    max_age=86400,
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    logger.info(
        "http_request %s %s -> %s in %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        (time.time() - start_time) * 1000,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "path": request.url.path},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "path": request.url.path},
    )


app.include_router(routes_field.router)


@app.get("/")
def root():
    return {"status": "ok", "environment": os.getenv("APP_ENV", "development")}


@app.get("/health")
def health_check():
    return {"status": "healthy", "environment": os.getenv("APP_ENV", "development")}