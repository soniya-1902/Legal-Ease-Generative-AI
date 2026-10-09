from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import get_settings

settings = get_settings()

app = FastAPI(
    title="LegalEase API",
    description="AI-assisted legal document drafting and export API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def root():
    return {
        "message": "LegalEase API is running",
        "docs": "/docs",
        "health": "/health",
    }


app.include_router(router)
