from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List, Optional
from analyser.AnalyzerPipeline import SentimentAnalyzer
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime


DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

engine = create_async_engine(DATABASE_URL, echo=True)  #изменить на False потом!!!!
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)

class FeedbackDB(Base):
    __tablename__ = "users_feedback"
    
    source_id: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
    DateTime,
    server_default=func.now())
    send_time: Mapped[DateTime] = mapped_column(DateTime)
    meta_data: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)



class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"

class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped["User"] = relationship(back_populates="addresses")
    def __repr__(self) -> str:
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"



'''----------------------------------------------------------'''
app = FastAPI() 

sentiment_analyzer = SentimentAnalyzer(
    ru_anchors_path='sentiment_anchors_ru.json', 
    en_anchors_path='anchors.json'
)

@app.get("/health")
def health_check():
    return Response(status_code=200)

class FeedbackData(BaseModel):
    source_id: str
    external_id: str
    text: str
    category: str | None = None
    created_at: datetime
    send_time: datetime | None = None
    meta_data: Dict[str, Any] | None = None

@app.post("/analyse")
def analyse_data(feedback: FeedbackData):

    analyzed_result = sentiment_analyzer.smart_analyze(feedback.text)

    db_record = FeedbackDB(
        

    )
    return {
        "source_id": feedback.source_id,
        "external_id": feedback.external_id,
        "status": "success",
        "analysis": analyzed_result
    }

    
    
    
