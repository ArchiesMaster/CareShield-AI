from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base, engine
from app.db.tables import ChatSession, User, Message, CaseNote
from app.api import chat_session, case_note


Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(chat_session.router, prefix=settings.api_prefix)
app.include_router(case_note.router, prefix=settings.api_prefix)

@app.get("/")
def root():
    return {"message": settings.app_name, "docs": "/docs"}

@app.get("/health")
def health():
    return{"status": "ok"}
