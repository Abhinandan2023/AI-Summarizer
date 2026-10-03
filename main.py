import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, UploadFile, File
from sqlalchemy import DateTime, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy.engine import URL
from langchain_groq import ChatGroq
from pydantic import BaseModel
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0.3,
)

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

class Document(Base):
    __tablename__="documents"

    id: Mapped[int]=mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    filename: Mapped[str]=mapped_column(
        String(500),
        nullable=False,
    )
    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    chunk_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

class QuestionAnswer(Base):
    __tablename__ = "questions_answers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

class SummarizeRequest(BaseModel):
    text: str

class QuestionRequest(BaseModel):
    document_id: str
    question: str

class PDFSummaryRequest(BaseModel):
    document_id: str

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

def extract_pdf_text(file):
    document=fitz.open(stream=file, filetype="pdf")
    text=""
    for page in document:
        text+=page.get_text()
    page_count=len(document)
    document.close()
    return text, page_count

text_splitter=RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

embeddings=HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def get_vectorstore(document_id: str):
    return Chroma(
        collection_name=f"document_{document_id}",
        embedding_function=embeddings,
        persist_directory="./chroma_db",
    )

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

@app.post("/summarize/text")
def summarize_text(request: SummarizeRequest, db: Session=Depends(get_db)):
    response=llm.invoke(
         f"""
       Summarize the following text clearly and concisely.
        Provide:
        1. A short summary
        2. The key points
        Text:
        {request.text}
        """
    )
    usage= response.usage_metadata

    summary=Summary(
        source_type="text",
        source_name="Direct Text Input",
        summary=response.content,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )

    db.add(summary)
    db.commit()
    db.refresh(summary)
    return {
        "id": summary.id,
        "source_type": summary.source_type,
        "source_name": summary.source_name,
        "summary": summary.summary,
        "input_tokens": summary.input_tokens,
        "output_tokens": summary.output_tokens,
        "created_at": summary.created_at,
        
    }

@app.post("/upload/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    pdf_bytes = await file.read()

    text, page_count = extract_pdf_text(pdf_bytes)

    chunks = text_splitter.split_text(text)

    document = Document(
        filename=file.filename,
        page_count=page_count,
        chunk_count=len(chunks),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    document_id = document.id

    vectorstore = get_vectorstore(str(document_id))

    vectorstore.add_texts(
        texts=chunks,
        metadatas=[
            {
                "source": file.filename,
                "page_count": page_count,
            }
            for _ in chunks
        ],
    )

    return {
        "document_id": document_id,
        "filename": file.filename,
        "page_count": page_count,
        "text_length": len(text),
        "chunk_count": len(chunks),
        "message": "PDF processed and stored successfully",
    }
    
@app.post("/ask")
def ask_question(request: QuestionRequest, db: Session=Depends(get_db)):

    vectorstore = get_vectorstore(request.document_id)
    relevant_chunks= vectorstore.similarity_search(
        request.question,
        k=4,
    )

    context="".join(
        document.page_content for document in relevant_chunks
    )

    response=llm.invoke(
         f"""
        Answer the user's question using only the information
        provided in the document context below.

        If the answer cannot be found in the context, say:
        "I could not find the answer in the uploaded document."

        Document context:
        {context}

        User question:
        {request.question}
        """
    )
    usage=response.usage_metadata

    question_answer=QuestionAnswer(
        document_id=int(request.document_id),
        question=request.question,
        answer=response.content,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )

    db.add(question_answer)
    db.commit()
    db.refresh(question_answer)

    return{
        "id": question_answer.id,
        "question": question_answer.question,
        "answer": question_answer.answer,
        "sources": len(relevant_chunks),
        "input_tokens": question_answer.input_tokens,
        "output_tokens": question_answer.output_tokens,
        "created_at": question_answer.created_at,
    }

@app.post("/summarize/pdf")
def summarize_pdf(
    request: PDFSummaryRequest,
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == int(request.document_id)
    ).first()

    if not document:
        return {
            "error": "Document not found"
        }
    vectorstore = get_vectorstore(request.document_id)

    collection_data = vectorstore.get()
    documents = collection_data["documents"]

    if not documents:
        return {
            "document_id": request.document_id,
            "summary": "No content found for this document.",
            "sources": 0,
        }

    context = "\n\n".join(documents)

    response = llm.invoke(
        f"""
        Summarize the following document clearly and accurately.

        Include:
        - A concise overall summary
        - The most important points
        - Important numbers, dates, names, or conditions
        - Important lists or items mentioned in the document

        Do not invent information that is not present in the document.

        Document:
        {context}
        """
    )

    usage = response.usage_metadata

    summary = Summary(
        source_type="pdf",
        source_name=document.filename,
        summary=response.content,
        page_count=document.page_count,
        chunk_count=document.chunk_count,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )

    db.add(summary)
    db.commit()
    db.refresh(summary)

    return {
        "id": summary.id,
        "document_id": document.id,
        "source_type": summary.source_type,
        "source_name": summary.source_name,
        "summary": summary.summary,
        "page_count": summary.page_count,
        "chunk_count": summary.chunk_count,
        "input_tokens": summary.input_tokens,
        "output_tokens": summary.output_tokens,
        "created_at": summary.created_at,
        "sources": len(documents),
    }