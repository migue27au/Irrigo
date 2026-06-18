from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# DATABASE URL (ej: postgresql+asyncpg://user:pass@host/db)
DATABASE_URL = settings.DATABASE_URL


# Engine principal (async)
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # pon False en producción
    pool_pre_ping=True
)


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Dependency for FastAPI
async def get_db():
    async with SessionLocal() as session:
        yield session