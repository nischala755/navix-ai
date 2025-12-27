"""API dependencies."""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.services.crud import CRUDService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_crud(session: AsyncSession) -> CRUDService:
    """Get CRUD service."""
    return CRUDService(session)
