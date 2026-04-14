from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.url import URLStats
from app.services.url_service import URLService

router = APIRouter()

@router.get("/{short_code}/stats", response_model=URLStats)
async def get_url_stats(
    short_code: str,
    db: AsyncSession = Depends(get_db)
):
    stats = await URLService.get_stats(db, short_code)
    if not stats:
        raise HTTPException(status_code=404, detail="URL not found")
    
    return stats
