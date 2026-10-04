# SummarAI

> AI-powered document summarization and RAG-based question answering application.

SummarAI is a full-stack Generative AI project that allows users to upload PDF documents, generate structured summaries, and ask questions about document content using Retrieval-Augmented Generation (RAG).

Live Demo: https://cloud-ai-summarizer.streamlit.app/

## ✨ Features

- PDF upload and text extraction
- Intelligent text chunking
- RAG-based document question answering
- Structured PDF summarization
- Chroma Cloud vector storage
- PostgreSQL persistence for documents, summaries and Q&A
- Token usage tracking
- History and document deletion
- Streamlit frontend
- FastAPI backend
- Cloud deployment with Streamlit Cloud and Render
- Environment-based secret management

## 🏗️ Architecture

```text
Streamlit Cloud
      │
      ▼
Render FastAPI
   ┌──┴──────┐
   ▼         ▼
Supabase   Chroma Cloud
PostgreSQL     │
   │           │
   └─────┬─────┘
         ▼
     Mistral API
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| Database | PostgreSQL / Supabase |
| ORM | SQLAlchemy |
| Vector Database | Chroma Cloud |
| LLM | Mistral |
| Embeddings | Mistral `mistral-embed` |
| PDF Processing | PyMuPDF |
| Text Splitting | LangChain RecursiveCharacterTextSplitter |
| Server | Uvicorn |
| Deployment | Streamlit Cloud + Render |
| Language | Python |

## 🔄 RAG Pipeline

```text
PDF
 ↓
PyMuPDF extraction
 ↓
Recursive chunking
 ↓
Mistral embeddings
 ↓
Chroma Cloud
```

For a question:

```text
Question
 ↓
Semantic search
 ↓
Top relevant chunks
 ↓
Document context + question
 ↓
Mistral LLM
 ↓
Answer
 ↓
PostgreSQL history
```

The model is instructed to answer using the retrieved document context and to state when the answer cannot be found.

## 📝 PDF Summarization

Large PDFs are summarized hierarchically:

```text
PDF chunks
 ↓
Groups of chunks
 ↓
Intermediate summaries
 ↓
Combined summaries
 ↓
Final structured summary
```

The final summary covers overall content, important points, concepts, technical details, numbers, names, dates, conditions, lists and conclusions.

## 🗄️ Persistence

PostgreSQL stores:

- Documents
- Summaries
- Questions and answers
- Token usage
- Page counts
- Chunk counts
- Timestamps

Chroma Cloud stores the vectorized document content used for semantic retrieval.

## 🔐 Configuration

Secrets are stored outside Git using environment variables.

```env
POSTGRES_HOST=...
POSTGRES_PORT=5432
POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...

MISTRAL_API_KEY=...
MISTRAL_MODEL=ministral-14b-2512

CHROMA_API_KEY=...
CHROMA_TENANT=...
CHROMA_DATABASE=...
```

Never commit `.env` or API keys.

## 🚀 Run Locally

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Start Streamlit in another terminal:

```bash
streamlit run streamlit_app.py
```

## ☁️ Deployment

The production architecture uses:

- Streamlit Cloud — frontend
- Render — FastAPI backend
- Supabase — PostgreSQL
- Chroma Cloud — vector storage
- Mistral — LLM and embeddings

## 🔮 Future Improvements

- User authentication
- Per-user document/history isolation
- Authorization and ownership checks
- URL ingestion
- Direct text input
- Source/page citations
- RAG evaluation
- Streaming responses
- Production logging and monitoring
- Rate limiting

## 👨‍💻 Project Goal

SummarAI demonstrates practical skills across RAG, LLM integration, embeddings, vector databases, REST APIs, PostgreSQL, cloud deployment, frontend/backend integration, Git/GitHub and production-oriented debugging.

Author:

Abhinandan Maity
