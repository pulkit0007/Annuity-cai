from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.config import POSTGRES_PORT, POSTGRES_PASS, POSTGRES_SERVER, POSTGRES_DB, POSTGRES_NAME
from app.logger import get_logger

logger = get_logger(__name__)

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_DB}:{POSTGRES_PASS}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_NAME}"

logger.info(f"Connecting to database: {SQLALCHEMY_DATABASE_URL}")

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with async_session() as session:
        yield session