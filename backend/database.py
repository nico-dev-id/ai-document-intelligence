import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:admin123@localhost:5432/docapp"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Model tabel users
class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    documents = relationship("DocumentModel", back_populates="user")

# Model tabel documents
class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nama_file = Column(String, nullable=False)
    path_file = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("UserModel", back_populates="documents")
    conversations = relationship("ConversationModel", back_populates="document", cascade="all, delete-orphan")

# Model tabel conversations
class ConversationModel(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    pertanyaan = Column(Text, nullable=False)
    jawaban = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("DocumentModel", back_populates="conversations")

# Buat semua tabel
Base.metadata.create_all(bind=engine)

print("Database siap!")