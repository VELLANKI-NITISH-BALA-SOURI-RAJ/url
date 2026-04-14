from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List

class URLBase(BaseModel):
    long_url: HttpUrl

class URLCreate(URLBase):
    custom_code: Optional[str] = None
    expires_at: Optional[datetime] = None
    password: Optional[str] = None

class URLResponse(URLBase):
    short_code: str
    short_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class AnalyticsBase(BaseModel):
    clicked_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    referer: Optional[str]

    class Config:
        from_attributes = True

class URLStats(BaseModel):
    short_code: str
    long_url: str
    total_clicks: int
    recent_clicks: List[AnalyticsBase]

    class Config:
        from_attributes = True
