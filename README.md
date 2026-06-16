# 🤖 AI Document Intelligence System

An AI-powered document analysis system that allows users to upload multiple documents and ask questions using RAG (Retrieval Augmented Generation).

## 🚀 Live Demo
- **Frontend**: https://ai-document-intelligence-nine.vercel.app/
- **Backend API**: https://nico-dev-id-ai-document-intelligence-api.hf.space/docs
> ⚠️ Note: This is a portfolio project. 
> Please do not upload sensitive documents.

## ✨ Features
- 🔐 User authentication (JWT)
- 📄 Upload multiple PDF & TXT documents
- 🤖 AI-powered Q&A across all documents simultaneously
- 📚 Multi-document RAG pipeline
- 💾 Permanent file storage (Supabase Storage)
- 🔒 Data isolation per user

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL + SQLAlchemy
- LangChain + ChromaDB
- Groq API (LLaMA 3.3 70b)
- Supabase Storage
- JWT Authentication

**Frontend:**
- Next.js 15
- React
- Tailwind CSS

**Deployment:**
- Hugging Face Spaces (Backend)
- Vercel (Frontend)
- Supabase (Database + Storage)

## 🏗️ Architecture
User → Next.js Frontend → FastAPI Backend → PostgreSQL (metadata)
→ Supabase Storage (files)
→ ChromaDB (vectors)
→ Groq LLaMA (AI)

## 🚦 Getting Started

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📝 Environment Variables

### Backend (.env)
DATABASE_URL=postgresql://...
GROQ_API_KEY=gsk_...
SUPABASE_URL=https://...
SUPABASE_KEY=sb_...