from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.db.session import get_async_db, get_db


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_db():
        yield session


def get_sync_database() -> Generator[Session, None, None]:
    yield from get_db()