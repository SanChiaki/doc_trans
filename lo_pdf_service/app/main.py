from __future__ import annotations

from fastapi import FastAPI

from app.api.conversions import router as conversions_router

app = FastAPI(title="LibreOffice PDF Conversion Service", version="0.1.0")
app.include_router(conversions_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
