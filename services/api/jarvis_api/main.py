"""Health and contract foundation for JARVIS. No public deployment intended."""
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str
    retryable: bool = False


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    app = FastAPI(title="JARVIS API", version="0.0.1", lifespan=lifespan)

    @app.middleware("http")
    async def request_identity(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/api/v1/health/live", tags=["health"])
    async def live():
        return {"status": "alive", "service": "jarvis-api"}

    @app.get("/api/v1/health/ready", tags=["health"], responses={503: {"model": ErrorEnvelope}})
    async def ready(request: Request):
        database_url = os.getenv("JARVIS_DATABASE_URL")
        if not database_url:
            return JSONResponse(status_code=503, content={"error": {
                "code": "DATABASE_NOT_CONFIGURED", "message": "La base de datos no está configurada",
                "request_id": request.state.request_id, "retryable": True}})
        try:
            import psycopg
            with psycopg.connect(database_url, connect_timeout=2) as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        except psycopg.Error:
            return JSONResponse(status_code=503, content={"error": {
                "code": "DATABASE_UNAVAILABLE", "message": "La base de datos no está disponible",
                "request_id": request.state.request_id, "retryable": True}})
        return {"status": "ready", "service": "jarvis-api"}

    return app


app = create_app()
