from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.errors import DocumentConversionError


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": settings.app_name}

    @app.exception_handler(DocumentConversionError)
    async def conversion_error_handler(_: Request, exc: DocumentConversionError):
        body = {"code": exc.code, "message": exc.message}
        if exc.details:
            body["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "code": "bad_request",
                "message": "Invalid request.",
                "details": {"errors": exc.errors()},
            },
        )

    return app


app = create_app()
