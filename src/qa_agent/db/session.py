from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.qa_agent.config import settings

engine = create_async_engine(
    settings.resolved_database_url, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.resolved_database_url else {}
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db():
    async with SessionLocal() as db:
        yield db
