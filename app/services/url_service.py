from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.url import URL, Analytics
from app.core.utils import encode_base62
from app.services.cache_service import cache_service
from passlib.context import CryptContext
from datetime import datetime, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class URLService:
    @staticmethod
    async def shorten_url(db: AsyncSession, long_url: str, custom_code: str = None, expires_at: datetime = None, password: str = None) -> URL:
        hashed_password = pwd_context.hash(password) if password else None
        if custom_code:
            # Check if custom code is already taken
            result = await db.execute(select(URL).filter(URL.short_code == custom_code))
            if result.scalars().first():
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Custom alias already taken")
            
            new_url = URL(
                long_url=long_url, 
                short_code=custom_code,
                expires_at=expires_at,
                password_hash=hashed_password
            )
            db.add(new_url)
            await db.commit()
            await db.refresh(new_url)
        else:
            # Traditional Base62 generation
            new_url = URL(
                long_url=long_url, 
                short_code="temp",
                expires_at=expires_at,
                password_hash=hashed_password
            )
            db.add(new_url)
            await db.commit()
            await db.refresh(new_url)

            short_code = encode_base62(new_url.id)
            new_url.short_code = short_code
            await db.commit()
            await db.refresh(new_url)
        
        # Cache the result
        await cache_service.set_url(new_url.short_code, long_url)
        
        return new_url

    @staticmethod
    async def get_url_record(db: AsyncSession, short_code: str) -> URL:
        result = await db.execute(select(URL).filter(URL.short_code == short_code))
        url_record = result.scalars().first()
        
        if url_record:
            # Check expiration
            if url_record.expires_at and url_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                url_record.is_active = 0
                await db.commit()
                return None
            
            if url_record.is_active == 0:
                return None
                
        return url_record

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if not hashed_password:
            return True
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    async def record_click(db: AsyncSession, short_code: str, ip: str, ua: str, referer: str):
        result = await db.execute(select(URL.id).filter(URL.short_code == short_code))
        url_id = result.scalars().first()
        
        if url_id:
            analytics = Analytics(
                url_id=url_id,
                ip_address=ip,
                user_agent=ua,
                referer=referer
            )
            db.add(analytics)
            await db.commit()

    @staticmethod
    async def get_stats(db: AsyncSession, short_code: str):
        result = await db.execute(select(URL).filter(URL.short_code == short_code))
        url_record = result.scalars().first()
        
        if not url_record:
            return None

        # Get total clicks
        clicks_count = await db.execute(
            select(func.count(Analytics.id)).filter(Analytics.url_id == url_record.id)
        )
        total_clicks = clicks_count.scalar()

        # Get last 10 clicks
        recent_clicks_result = await db.execute(
            select(Analytics).filter(Analytics.url_id == url_record.id).order_by(Analytics.clicked_at.desc()).limit(10)
        )
        recent_clicks = recent_clicks_result.scalars().all()

        return {
            "short_code": url_record.short_code,
            "long_url": url_record.long_url,
            "total_clicks": total_clicks,
            "recent_clicks": recent_clicks
        }

    @staticmethod
    async def update_url(db: AsyncSession, short_code: str, new_long_url: str) -> URL:
        result = await db.execute(select(URL).filter(URL.short_code == short_code))
        url_record = result.scalars().first()
        
        if not url_record:
            return None
        
        url_record.long_url = new_long_url
        await db.commit()
        await db.refresh(url_record)
        
        # Update cache
        await cache_service.set_url(short_code, new_long_url)
        
        return url_record

    @staticmethod
    async def update_short_code(db: AsyncSession, old_code: str, new_code: str) -> URL:
        # Check if new code is already taken
        result = await db.execute(select(URL).filter(URL.short_code == new_code))
        if result.scalars().first():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="New alias already taken")

        result = await db.execute(select(URL).filter(URL.short_code == old_code))
        url_record = result.scalars().first()
        
        if not url_record:
            return None
        
        old_long_url = url_record.long_url
        url_record.short_code = new_code
        await db.commit()
        await db.refresh(url_record)
        
        # Update cache: Delete old, set new
        await cache_service.delete_url(old_code)
        await cache_service.set_url(new_code, old_long_url)
        
        return url_record
