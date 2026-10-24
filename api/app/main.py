"""Veda API."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import check_db
from app.routers import auth, filings, system

VERSION = "0.4.0"

app = FastAPI(title="Veda API", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ERROR_CODES = {
    400: "invalid_input",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "invalid_input",
    502: "hedera_error",
}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": _ERROR_CODES.get(exc.status_code, "internal_error"),
                "message": message,
                "details": {},
            }
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "invalid_input",
                "message": "validation failed",
                "details": jsonable_encoder(exc.errors()),
            }
        },
    )


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "db": check_db(), "version": VERSION}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(filings.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
