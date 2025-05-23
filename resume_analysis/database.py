from sqlalchemy import Column, String, Text, DateTime, select, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import datetime
import json
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Define the Pydantic schema for input
class SaveResumeAnalysis(BaseModel):
    task_id: str
    resume_text: str 
    job_description: str
    analysis_results: Optional[Dict] = None

# Async DB (for FastAPI)
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./resume_analysis.db"
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync DB (for Celery)
SYNC_DATABASE_URL = "sqlite:///./resume_analysis.db"
sync_engine = create_engine(SYNC_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=sync_engine)

# Declare Base
Base = declarative_base()

# SQLAlchemy ORM model
class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(String, primary_key=True, index=True)
    resume_text = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    analysis_results = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "resume_text": self.resume_text,
            "job_description": self.job_description,
            "analysis_results": json.loads(self.analysis_results) if self.analysis_results else None,
            "timestamp": self.timestamp.isoformat()
        }

# Async DB dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Async save function (FastAPI)
async def save_resume_analysis(data: SaveResumeAnalysis, db: AsyncSession) -> ResumeAnalysis:
    analysis_json = json.dumps(data.analysis_results) if data.analysis_results else None
    analysis = ResumeAnalysis(
        id=data.task_id,
        resume_text=data.resume_text,
        job_description=data.job_description,
        analysis_results=analysis_json
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis

# Sync save function (Celery)
def save_resume_analysis_sync(ResumeData: SaveResumeAnalysis) -> ResumeAnalysis:
    db = SessionLocal()
    try:
        analysis_json = json.dumps(ResumeData.analysis_results) if ResumeData.analysis_results else None
        analysis = ResumeAnalysis(
            id=ResumeData.task_id,
            resume_text=ResumeData.resume_text,
            job_description=ResumeData.job_description,
            analysis_results=analysis_json
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# Async get function (FastAPI)
async def get_resume_analysis(task_id: str, db: AsyncSession) -> Optional[ResumeAnalysis]:
    result = await db.execute(select(ResumeAnalysis).where(ResumeAnalysis.id == task_id))
    return result.scalars().first()
