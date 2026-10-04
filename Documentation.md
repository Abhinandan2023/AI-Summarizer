# SummarAI — Technical Documentation

## 1. Project Overview

SummarAI is an AI-powered document summarization and question-answering application.

The project evolved from a basic summarization application into a RAG-based system capable of answering questions from uploaded PDF documents.

The goal was to build an end-to-end Generative AI application covering document ingestion, retrieval, LLM generation, persistence, frontend integration and cloud deployment.

---

## 2. Project Objectives

The application was designed to support:

1. PDF ingestion
2. Text extraction
3. Chunking
4. Embedding generation
5. Vector storage
6. Semantic retrieval
7. LLM-based question answering
8. Document summarization
9. History persistence
10. Document deletion
11. Cloud deployment

---

## 3. Architecture

```text
                    USER
                     │
                     ▼
             Streamlit Cloud
                Frontend
                     │
                     ▼
               Render
             FastAPI Backend
                │       │
        ┌───────┘       └────────┐
        ▼                        ▼
    Supabase                Chroma Cloud
   PostgreSQL                Vector Store
        │                        │
        └──────────┬─────────────┘
                   ▼
              Mistral API
             LLM + Embeddings
```

---

## 4. Technology Decisions

### FastAPI

FastAPI provides the REST backend connecting the frontend with the database, vector store and AI services.

Main endpoints include:

```text
GET  /
GET  /health
GET  /history

POST /summarize/text
POST /upload/pdf
POST /ask
POST /summarize/pdf

DELETE /documents/{document_id}
```

### Streamlit

Streamlit provides the user interface for uploading PDFs, generating summaries, asking questions, viewing history and deleting documents.

### PostgreSQL

PostgreSQL stores application-level information such as documents, summaries, questions, answers, token usage and timestamps.

### Chroma Cloud

The initial implementation used local Chroma storage. For cloud deployment, the vector database was moved to Chroma Cloud so vector data is not dependent on the FastAPI server filesystem.

### Mistral

Mistral is used for both generation and embeddings.

LLM:

```text
ministral-14b-2512
```

Embedding model:

```text
mistral-embed
```

---

## 5. RAG Pipeline

### 5.1 PDF Extraction

PyMuPDF extracts text from each PDF page and records the page count.

```text
PDF → PyMuPDF → Raw text
```

### 5.2 Chunking

The extracted text is split using `RecursiveCharacterTextSplitter`.

Current configuration:

```text
chunk_size = 1000
chunk_overlap = 200
```

Overlap helps preserve context between adjacent chunks.

### 5.3 Embedding

Each chunk is converted into a vector using Mistral embeddings and stored in Chroma Cloud.

Each document uses its own collection:

```text
document_<document_id>
```

### 5.4 Retrieval

When a question is submitted, semantic similarity search retrieves the top four relevant chunks.

### 5.5 Generation

The retrieved chunks are provided to Mistral along with the question.

The prompt instructs the model to use only the supplied document context and to explicitly say when the answer cannot be found.

---

## 6. PDF Summarization

Large PDFs are not sent to the model as one huge prompt.

The implementation uses hierarchical summarization:

```text
All chunks
   ↓
Groups of 12
   ↓
Intermediate summaries
   ↓
Combined summaries
   ↓
Final summary
```

Intermediate summaries preserve main ideas, concepts, technical details, numbers, names, dates, conditions, lists and conclusions.

Token usage from the summarization calls is accumulated and stored in PostgreSQL.

---

## 7. Database Design

### Document

```text
id
filename
page_count
chunk_count
created_at
```

### Summary

```text
id
document_id
source_type
source_name
summary
page_count
chunk_count
input_tokens
output_tokens
created_at
```

### QuestionAnswer

```text
id
document_id
question
answer
input_tokens
output_tokens
created_at
```

---

## 8. History and Deletion

History combines each document with its associated summaries and Q&A records.

Deletion performs a complete cleanup:

1. Delete related summaries.
2. Delete related Q&A records.
3. Delete the document record.
4. Delete the associated Chroma collection.
5. Remove the document from the Streamlit history view.

This avoids leaving orphaned application records and vectors.

---

# 9. Challenges and Solutions

## Challenge 1 — LLM Provider and Rate Limits

### Problem

The project initially experimented with Groq. Rate/token-per-minute limitations became a practical issue during testing.

### Solution

The application moved to Mistral and selected:

```text
ministral-14b-2512
```

This provided a better fit for the application's workload.

---

## Challenge 2 — Large PDF Token Limits

### Problem

Sending an entire large PDF to an LLM can exceed context limits and increase cost.

### Solution

The project introduced chunking and RAG.

For questions, only relevant chunks are retrieved.

For full-document summaries, hierarchical summarization is used.

---

## Challenge 3 — Local Chroma Was Not Suitable for Cloud Persistence

### Problem

The first implementation stored Chroma data locally in:

```text
./chroma_db
```

A cloud deployment should not depend on an ephemeral application filesystem.

### Solution

The vector store was migrated to Chroma Cloud.

This separates persistent vector storage from the FastAPI server.

---

## Challenge 4 — Chroma Cloud Client Error

### Problem

The Chroma SDK produced:

```text
TypeError: CloudClient() got an unexpected keyword argument 'host'
```

### Solution

The client was configured using the supported cloud client parameters:

```python
chromadb.CloudClient(
    api_key=CHROMA_API_KEY,
    tenant=CHROMA_TENANT,
    database=CHROMA_DATABASE,
)
```

The Chroma connection was then verified successfully.

---

## Challenge 5 — Render Memory Limit

### Problem

The initial Render deployment exceeded the free instance's 512 MB memory limit.

The dependency tree included large ML packages such as:

```text
torch
transformers
sentence-transformers
CUDA packages
```

### Solution

The original local embedding implementation used:

```text
sentence-transformers/all-MiniLM-L6-v2
```

This was replaced with:

```text
MistralAIEmbeddings
mistral-embed
```

This removed the need to load the local Sentence Transformers/PyTorch stack on the Render backend and reduced the deployment memory footprint.

---

## Challenge 6 — Streamlit Cloud Could Not Reach Localhost

### Problem

The Streamlit application initially called:

```text
http://127.0.0.1:8000
```

This worked on the developer's machine but failed on Streamlit Cloud because `127.0.0.1` refers to the machine running the Streamlit application.

### Solution

FastAPI was deployed separately on Render.

Streamlit now receives the backend URL through an environment/secret configuration:

```toml
API_URL = "https://your-render-backend-url"
```

The resulting architecture is:

```text
Streamlit Cloud
      ↓
Render FastAPI
      ↓
Supabase + Chroma Cloud + Mistral
```

---

## Challenge 7 — Git Remote Was Ahead

### Problem

A push was rejected because the remote branch contained commits that were not present locally.

### Solution

Instead of force pushing, the branch was synchronized with:

```bash
git pull --rebase origin feature/ai-summarizer
```

followed by:

```bash
git push origin feature/ai-summarizer
```

This preserved the commit history.

---

## Challenge 8 — Secret Management

The application requires PostgreSQL, Mistral and Chroma credentials.

These are kept out of Git using:

```text
.env
```

and cloud secret/environment-variable configuration.

The `.gitignore` also excludes:

```text
.env
.venv/
__pycache__/
.vscode/
chroma_db/
```

No API keys or database passwords should be committed.

---

# 10. Development Journey

The project was developed incrementally:

```text
FastAPI + PostgreSQL
        ↓
Text summarization
        ↓
PDF processing
        ↓
RAG
        ↓
Chroma Cloud
        ↓
Streamlit UI
        ↓
History
        ↓
Document deletion
        ↓
Cloud deployment
        ↓
Render memory optimization
```

This approach allowed individual problems to be isolated and solved before moving to the next layer.

---

# 11. Git Workflow

The project uses:

```text
feature/ai-summarizer
```

Important development milestones included:

```text
Setup FastAPI and PostgreSQL
Implement Groq text summarization
Complete PDF RAG and summarization
Add PostgreSQL document, summary and Q&A persistence
Fix PDF processing and finalize RAG backend
Add Streamlit history and document deletion
Use Mistral embeddings for cloud deployment
```

The branch-based workflow provides a traceable history of the application's evolution.

---

# 12. Security and Current Limitation

Authentication has not yet been implemented.

The current system should therefore not be considered a production multi-user application for private history.

The next security milestone is:

```text
Authentication
      ↓
Users table
      ↓
User-owned documents
      ↓
Authorization checks
      ↓
Private history
```

Importantly, ownership must be enforced in FastAPI, not only hidden in Streamlit.

---

# 13. Future Roadmap

### Security

- Signup/login
- Password hashing
- Session or JWT authentication
- User-owned documents
- Authorization checks
- Private history

### Input Expansion

- URL ingestion
- Direct text input
- Additional document formats

### RAG Improvements

- Source/page citations
- Better chunking
- Hybrid retrieval
- Reranking
- RAG evaluation

### Production Improvements

- Streaming responses
- Rate limiting
- Structured logging
- Monitoring
- Usage controls
- Better error handling

---

# 14. What the Project Demonstrates

### Generative AI

- LLM integration
- Prompt engineering
- RAG
- Embeddings
- Vector search
- Document summarization
- Token tracking

### Backend

- FastAPI
- REST APIs
- SQLAlchemy
- PostgreSQL
- Persistence

### Frontend

- Streamlit
- API integration
- Session state
- Interactive workflows

### Cloud

- Streamlit Cloud
- Render
- Supabase
- Chroma Cloud
- Secret management

### Engineering

- Git/GitHub
- Branch-based development
- Debugging
- Dependency optimization
- Cloud deployment
- Memory optimization

---

# 15. Final Perspective

The key learning from SummarAI was not simply integrating an LLM with a PDF.

The project encountered real engineering constraints:

```text
Provider limits
      ↓
Document size
      ↓
RAG design
      ↓
Vector persistence
      ↓
Cloud configuration
      ↓
Memory limits
      ↓
Frontend/backend networking
      ↓
Deployment
```

Each challenge required investigation and an architectural or implementation change.

The result is a practical full-stack Generative AI application rather than a simple LLM demo.

## Current Core Status

- PDF upload ✅
- PDF extraction ✅
- Chunking ✅
- Mistral embeddings ✅
- Chroma Cloud RAG ✅
- Question answering ✅
- Document summarization ✅
- PostgreSQL persistence ✅
- History ✅
- Document deletion ✅
- Streamlit frontend ✅
- FastAPI backend ✅
- Cloud deployment architecture ✅

### Next major milestone

**Authentication + user-specific history**

