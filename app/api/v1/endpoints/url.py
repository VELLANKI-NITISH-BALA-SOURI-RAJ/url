from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.url import URLCreate, URLResponse
from app.services.url_service import URLService
from app.services.cache_service import cache_service
from app.core.config import settings

router = APIRouter()

@router.post("/shorten", response_model=URLResponse)
async def shorten_url(
    url_in: URLCreate, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Basic Rate Limiting
    client_ip = request.client.host
    count = await cache_service.increment_rate_limit(client_ip)
    if count > 100: # 100 requests per minute
        raise HTTPException(status_code=429, detail="Too many requests")

    url_record = await URLService.shorten_url(
        db, 
        str(url_in.long_url), 
        url_in.custom_code,
        expires_at=url_in.expires_at,
        password=url_in.password
    )
    
    return {
        "long_url": url_record.long_url,
        "short_code": url_record.short_code,
        "short_url": f"{settings.BASE_URL}/{url_record.short_code}",
        "created_at": url_record.created_at
    }

@router.patch("/shorten/{short_code}", response_model=URLResponse)
async def update_url(
    short_code: str,
    url_in: URLCreate,
    db: AsyncSession = Depends(get_db)
):
    url_record = await URLService.update_url(db, short_code, str(url_in.long_url))
    if not url_record:
        raise HTTPException(status_code=404, detail="URL not found")
    
    return {
        "long_url": url_record.long_url,
        "short_code": url_record.short_code,
        "short_url": f"{settings.BASE_URL}/{url_record.short_code}",
        "created_at": url_record.created_at
    }

@router.patch("/shorten/{short_code}/code", response_model=URLResponse)
async def update_alias(
    short_code: str,
    url_in: URLCreate,
    db: AsyncSession = Depends(get_db)
):
    new_code = url_in.custom_code
    if not new_code:
        raise HTTPException(status_code=400, detail="New custom code required")
        
    url_record = await URLService.update_short_code(db, short_code, new_code)
    if not url_record:
        raise HTTPException(status_code=404, detail="URL not found")
    
    return {
        "long_url": url_record.long_url,
        "short_code": url_record.short_code,
        "short_url": f"{settings.BASE_URL}/{url_record.short_code}",
        "created_at": url_record.created_at
    }

@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    url_record = await URLService.get_url_record(db, short_code)
    
    if not url_record:
        raise HTTPException(status_code=404, detail="URL not found or expired")

    # Handle password protection
    if url_record.password_hash:
        password = request.query_params.get("p")
        if not password or not URLService.verify_password(password, url_record.password_hash):
            return {"detail": "Password required", "status": "password_protected"}

    # Async logging of analytics to not block the redirect
    background_tasks.add_task(
        URLService.record_click,
        db,
        short_code,
        request.client.host,
        request.headers.get("user-agent"),
        request.headers.get("referer")
    )

    return RedirectResponse(url=url_record.long_url, status_code=301)
