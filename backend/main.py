import os
import shutil
import uuid
import chromadb
from supabase import create_client, Client
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

# Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

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
    if not file.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Hanya file PDF dan TXT!")

    # Baca isi file
    file_content = file.file.read()
    
    # Upload ke Supabase Storage
    file_path = f"user_{current_user.id}/{file.filename}"
    
    supabase.storage.from_("documents").upload(
        path=file_path,
        file=file_content,
        file_options={"content-type": file.content_type}
    )

    # Simpan metadata ke database
    doc = DocumentModel(
        user_id=current_user.id,
        nama_file=file.filename,
        path_file=file_path  # simpan path di Supabase Storage
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

    # Hapus dari Supabase Storage
    try:
        supabase.storage.from_("documents").remove([doc.path_file])
    except:
        pass

    db.delete(doc)
    db.commit()
    return {"pesan": f"Dokumen {doc.nama_file} berhasil dihapus!"}

# ==================
# AI/RAG ENDPOINTS
# ==================

@app.post("/ask")
def tanya_semua_dokumen(
    data: PertanyaanInput,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Ambil semua dokumen user
    docs = db.query(DocumentModel).filter(
        DocumentModel.user_id == current_user.id
    ).all()
    
    if not docs:
        raise HTTPException(status_code=404, detail="Belum ada dokumen yang diupload!")
    
    # Load semua dokumen dari Supabase Storage
    all_chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for doc in docs:
        try:
            # Download file dari Supabase Storage
            file_content = supabase.storage.from_("documents").download(doc.path_file)
            
            # Simpan sementara untuk diproses
            temp_path = f"/tmp/{doc.nama_file}"
            with open(temp_path, "wb") as f:
                f.write(file_content)
            
            # Load dokumen
            if doc.path_file.endswith('.pdf'):
                loader = PyPDFLoader(temp_path)
            else:
                loader = TextLoader(temp_path, encoding="utf-8")
            
            dokumen = loader.load()
            
            for d in dokumen:
                d.metadata["nama_file"] = doc.nama_file
                d.metadata["doc_id"] = doc.id
            
            chunks = splitter.split_documents(dokumen)
            all_chunks.extend(chunks)
            
            # Hapus file temporary
            os.remove(temp_path)
            
        except Exception as e:
            print(f"Error loading {doc.nama_file}: {e}")
            continue
    
    if not all_chunks:
        raise HTTPException(status_code=500, detail="Gagal memproses dokumen!")
    
    # Buat vector database dari semua dokumen (unique collection, auto-cleanup)
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    client = chromadb.EphemeralClient()
    collection_name = f"user_{current_user.id}_{uuid.uuid4().hex[:8]}"

    vectordb = Chroma.from_documents(
        all_chunks,
        embeddings,
        client=client,
        collection_name=collection_name
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 8})

    # Cari konteks relevan
    docs_relevan = retriever.invoke(data.pertanyaan)
    
    # Kelompokkan berdasarkan dokumen sumber
    konteks_list = []
    for d in docs_relevan:
        nama_file = d.metadata.get("nama_file", "unknown")
        konteks_list.append(f"[Dari: {nama_file}]\n{d.page_content}")
    
    konteks = "\n\n".join(konteks_list)
    
    # Tanya AI
    llm = ChatGroq(
        api_key=os.environ.get("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile"
    )
    
    prompt = f"""Kamu adalah asisten AI yang membantu menganalisis dokumen.
    
    Berikut adalah potongan relevan dari dokumen-dokumen yang tersedia:
    {konteks}

    Pertanyaan: {data.pertanyaan}

    INSTRUKSI:
    - Jika pertanyaan bersifat umum dan ada beberapa dokumen berbeda topik, jawab untuk SETIAP dokumen secara terpisah
    - Jika pertanyaan spesifik, fokus jawab berdasarkan dokumen yang relevan
    - Sebutkan nama dokumen sumber untuk setiap informasi
    - Jawab dalam bahasa Indonesia dengan jelas"""

    jawaban = llm.invoke(prompt)
    
    # Simpan ke conversations
    # Gunakan doc_id pertama yang relevan
    doc_id_relevan = None

    if docs_relevan:
        meta_doc_id = docs_relevan[0].metadata.get("doc_id")
        if meta_doc_id:
            # Cek apakah dokumen masih ada
            doc_check = db.query(DocumentModel).filter(
                DocumentModel.id == meta_doc_id
            ).first()
            if doc_check:
                doc_id_relevan = meta_doc_id
    
    # Kalau tidak ada doc_id yang valid, pakai dokumen pertama user
    if not doc_id_relevan and docs:
        doc_id_relevan = docs[0].id

    if doc_id_relevan:
        conv = ConversationModel(
            user_id=current_user.id,
            document_id=doc_id_relevan,
            pertanyaan=data.pertanyaan,
            jawaban=jawaban.content
    )
    db.add(conv)
    db.commit()
    
    return {
        "pertanyaan": data.pertanyaan,
        "jawaban": jawaban.content,
        "sumber": [d.metadata.get("nama_file") for d in docs_relevan]
    }

# Endpoint untuk lihat semua conversations user
@app.get("/conversations")
def get_all_conversations(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    convs = db.query(ConversationModel).filter(
        ConversationModel.user_id == current_user.id
    ).order_by(ConversationModel.created_at.desc()).all()
    
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