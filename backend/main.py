import os
import shutil
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from database import engine, SessionLocal, UserModel, DocumentModel, ConversationModel, Base
from auth import hash_password, verifikasi_password, buat_token, verifikasi_token
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_groq import ChatGroq

load_dotenv()

app = FastAPI(title="AI Document Intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Buat folder uploads
os.makedirs("uploads", exist_ok=True)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verifikasi_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token tidak valid!")
    user = db.query(UserModel).filter(UserModel.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan!")
    return user

# Schemas
class RegisterInput(BaseModel):
    nama: str
    email: str
    password: str

class PertanyaanInput(BaseModel):
    pertanyaan: str

# ==================
# AUTH ENDPOINTS
# ==================

@app.post("/register")
def register(data: RegisterInput, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar!")
    user_baru = UserModel(
        nama=data.nama,
        email=data.email,
        password=hash_password(data.password)
    )
    db.add(user_baru)
    db.commit()
    db.refresh(user_baru)
    return {"pesan": "Registrasi berhasil!", "nama": user_baru.nama}

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == form.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Email tidak ditemukan!")
    if not verifikasi_password(form.password, user.password):
        raise HTTPException(status_code=401, detail="Password salah!")
    token = buat_token({"sub": user.email, "nama": user.nama})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/profil")
def profil(current_user: UserModel = Depends(get_current_user)):
    return {"nama": current_user.nama, "email": current_user.email}

# ==================
# DOCUMENT ENDPOINTS
# ==================

@app.post("/documents/upload")
def upload_dokumen(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Cek tipe file
    if not file.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Hanya file PDF dan TXT!")

    # Simpan file
    user_folder = f"uploads/user_{current_user.id}"
    os.makedirs(user_folder, exist_ok=True)
    path_file = f"{user_folder}/{file.filename}"

    with open(path_file, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Simpan ke database
    doc = DocumentModel(
        user_id=current_user.id,
        nama_file=file.filename,
        path_file=path_file
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "pesan": "Dokumen berhasil diupload!",
        "dokumen": {
            "id": doc.id,
            "nama_file": doc.nama_file,
            "created_at": doc.created_at
        }
    }

@app.get("/documents")
def get_documents(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    docs = db.query(DocumentModel).filter(
        DocumentModel.user_id == current_user.id
    ).all()
    return {
        "total": len(docs),
        "documents": [
            {
                "id": d.id,
                "nama_file": d.nama_file,
                "created_at": d.created_at
            } for d in docs
        ]
    }

@app.delete("/documents/{doc_id}")
def hapus_dokumen(
    doc_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(DocumentModel).filter(
        DocumentModel.id == doc_id,
        DocumentModel.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan!")

    # Hapus file fisik
    if os.path.exists(doc.path_file):
        os.remove(doc.path_file)

    db.delete(doc)
    db.commit()
    return {"pesan": f"Dokumen {doc.nama_file} berhasil dihapus!"}

# ==================
# AI/RAG ENDPOINTS
# ==================

@app.post("/documents/{doc_id}/ask")
def tanya_dokumen(
    doc_id: int,
    data: PertanyaanInput,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Cek dokumen
    doc = db.query(DocumentModel).filter(
        DocumentModel.id == doc_id,
        DocumentModel.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan!")

    # Load dokumen
    if doc.path_file.endswith('.pdf'):
        loader = PyPDFLoader(doc.path_file)
    else:
        loader = TextLoader(doc.path_file, encoding="utf-8")

    dokumen = loader.load()

    # Potong dokumen
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(dokumen)

    # Buat vector database
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=f"chroma_db/doc_{doc_id}"
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    # Cari konteks relevan
    docs_relevan = retriever.invoke(data.pertanyaan)
    konteks = "\n".join([d.page_content for d in docs_relevan])

    # Tanya AI
    llm = ChatGroq(
        api_key=os.environ.get("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile"
    )

    prompt = f"""Berdasarkan dokumen berikut:
{konteks}

Jawab pertanyaan: {data.pertanyaan}
Jawab dalam bahasa Indonesia dengan jelas dan lengkap."""

    jawaban = llm.invoke(prompt)

    # Simpan ke database
    conv = ConversationModel(
        user_id=current_user.id,
        document_id=doc_id,
        pertanyaan=data.pertanyaan,
        jawaban=jawaban.content
    )
    db.add(conv)
    db.commit()

    return {
        "pertanyaan": data.pertanyaan,
        "jawaban": jawaban.content,
        "dokumen": doc.nama_file
    }

@app.get("/documents/{doc_id}/conversations")
def get_conversations(
    doc_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    convs = db.query(ConversationModel).filter(
        ConversationModel.document_id == doc_id,
        ConversationModel.user_id == current_user.id
    ).all()
    return {
        "total": len(convs),
        "conversations": [
            {
                "id": c.id,
                "pertanyaan": c.pertanyaan,
                "jawaban": c.jawaban,
                "created_at": c.created_at
            } for c in convs
        ]
    }