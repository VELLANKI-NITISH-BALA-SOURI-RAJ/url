from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1.endpoints import url, stats
from app.core.config import settings
from app.models.url import Base
from app.db.session import engine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup():
    # We now use Alembic for migrations instead of create_all
    pass

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join("frontend", "index.html"))

# Endpoints
app.include_router(url.router, tags=["URL Management"])
app.include_router(stats.router, prefix="/api/v1", tags=["Analytics"])

