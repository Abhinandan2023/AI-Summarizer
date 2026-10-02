import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI,HTTPException, Depends
from sqlalchemy import DateTime, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy.engine import URL

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=int(POSTGRES_PORT),
    database=POSTGRES_DB,
)

class Base(DeclarativeBase):
    pass

class Summary(Base):
    __tablename__="summaries"

    id:Mapped[int]=mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    source_type: Mapped[str]=mapped_column(
        String(20),
        nullable=False,
    )

    source_name: Mapped[str]=mapped_column(
        String(500),
        nullable=False,
    )

    summary: Mapped[str]=mapped_column(
        Text,
        nullable=False,
    )

    page_count: Mapped[int | None]=mapped_column(
        Integer,
        nullable=True,
    )

    chunk_count: Mapped[int | None]=mapped_column(
        Integer,
        nullable=True,
    )

    input_tokens: Mapped[int | None]=mapped_column(
        Integer,
        nullable=True,
    )

    output_tokens: Mapped[int | None]=mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime]=mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

engine=create_engine(DATABASE_URL) 

Base.metadata.create_all(bind=engine)

SessionLocal=sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

app=FastAPI(
    title="SummarAI",
    description="AI-powered document summarization API",
    version="1.0.0"
)

@app.get("/")
def root():
    return{
        "message":"Welcome to SummarAI",
        "status":"running"
    }

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return{
        "status":"healthy",
        "database":"connected"
    }
    except Exception as e:
        return{
        "status":"unhealthy",
        "database":"disconnected",
        "error": str(e)
        }

    
@app.get("/history")
def get_history(db: Session= Depends(get_db)):
    summaries=(db.query(Summary).order_by(
        Summary.created_at.desc()
    ).all()
    )
    return summaries
