from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine_args = {
    "echo": False,
    "future": True,
    "connect_args": {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
}

if "sqlite" not in settings.DATABASE_URL:
    engine_args["pool_size"] = 5
    engine_args["max_overflow"] = 10

engine = create_async_engine(settings.DATABASE_URL, **engine_args)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
