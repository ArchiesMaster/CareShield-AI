from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import tempfile
import os

from app.db.base import get_db
from app.db.tables import ChatSession, Message, User
from app.schemas.chat import (
    ChatReply,
    ChatSessionResponse,
    ChatSessionListItem,
    MessageCreate,
    MessageResponse,
    StartChatSessionRequest,
    StartChatSessionResponse,
)
from app.services.chat_module import (
    process_input,
    generate_assistant_reply,
    detect_text_language,
    translate_and_detect_language,
    is_termination_message
)

# Whisper model for transcription
from faster_whisper import WhisperModel
from app.services.whisper_module import transcribe_audio

router = APIRouter(prefix="/chat-session", tags=["chat-session"])

# Helper function to get demo user (replace with real auth in production)
def get_or_create_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.id == 1).first()

    if user:
        return user
    
    user = User(
        id = 1,
        first_name = "Demo",
        last_name = "User",
        email = "demo.user@careshield.local",
        password = "password",
        role = "support_worker",
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Helper function to build chat reply
def build_chat_reply_from_text(
        db: Session,
        session_id: int,
        original_text: str,
        input_type: str = "text"
) -> ChatReply:
    case_record = {
        "conversation_log": [],
        "full_original_text": "",
        "full_translated_text": "",
        "languages": [],
    }

    # Rebuild conversation log for context
    existing_messages = (
        db.query(Message)
        .filter(Message.chat_session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    for msg in existing_messages:
        case_record["conversation_log"].append(
            {
                "role": "user" if msg.message_sender_role == "user" else "assistant",
                "timestamp": str(msg.created_at),
                "message": msg.content,
            }
        )

    detected_language, _ = detect_text_language(original_text)
    detected_language = (detected_language or "en").lower()

    # Translate if necessary
    translated_text = None
    if detected_language != "en":
        translation_result = translate_and_detect_language(original_text)
        translated_text = translation_result.get("translated_text", original_text)
    
    # Process transcription through existing pipeline
    case_record = process_input(original_text, False, case_record)

    # Save user message (transcribed audio or text)
    user_message = Message(
        chat_session_id=session_id,
        message_sender_role="user",
        content=original_text,
        translated_content=translated_text,
        detected_language=detected_language,
        input_type=input_type,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    assistant_message = None

    # If the user explicitly wants to end the case note, do not ask the LLM for more questions.
    if is_termination_message(original_text):
        return ChatReply(
            chat_session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            note_ready=True,
            missing_slots=[],
        )

    # Generate assistant reply
    assistant_text, case_record = generate_assistant_reply(case_record)

    user_message_count = (
        db.query(Message)
        .filter(
            Message.chat_session_id == session_id,
            Message.message_sender_role == "user"
        )
        .count()
    )

    termination_requested = is_termination_message(original_text)

    note_ready = termination_requested or (assistant_text == "" and user_message_count >= 2)

    if not assistant_text and not note_ready:
        assistant_text = (
            "Thanks. I have recorded the information provided so far. "
            "Please add any further relevant details, or say 'no further information required' to generate the case note."
        )

    if assistant_text:
        assistant_lang, _ = detect_text_language(assistant_text)
        assistant_lang = (assistant_lang or "en").lower()

        assistant_translated = None
        if assistant_lang != "en":
            translation_result = translate_and_detect_language(assistant_text)
            assistant_translated = translation_result.get("translated_text", assistant_text)

        assistant_message = Message(
            chat_session_id=session_id,
            message_sender_role="assistant",
            content=assistant_text,
            translated_content=assistant_translated,
            detected_language=assistant_lang,
        )

        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

    return ChatReply(
        chat_session_id=session_id,
        user_message=user_message,
        assistant_message=assistant_message,
        note_ready=note_ready,
        missing_slots=[],
    )

# Initialise Whisper model once at startup
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

# NEW SESSION ENDPOINT
@router.post("", response_model=ChatSessionResponse)
def create_chat_session(db: Session = Depends(get_db)):
    session = ChatSession(user_id=1, session_active=True)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

# GET CHAT SESSION LIST ENDPOINT
@router.get("", response_model=list[ChatSessionListItem])
def list_chat_sessions(db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .order_by(ChatSession.started_at.desc())
        .all()
    )

    results : list[ChatSessionListItem] = []

    for session in sessions:
        messages = (
            db.query(Message)
            .filter(Message.chat_session_id == session.id)
            .order_by(Message.created_at.asc())
            .all()
        )

        first_user_message = next(
            (msg for msg in messages if msg.message_sender_role == "user"),
            None
        )

        last_message = messages[-1] if messages else None

        if first_user_message and first_user_message.content.strip():
            title = first_user_message.content.strip()[:50]
        else:
            title = f"Chat Session {session.id}"
        
        results.append(
            ChatSessionListItem(
                id = session.id,
                session_active = session.session_active,
                started_at = session.started_at,
                ended_at = session.ended_at,
                title = title,
                last_message = last_message.content if last_message else None,
                last_message_at = last_message.created_at if last_message else None,
            )
        )

        results.sort(
            key=lambda x: x.last_message_at or x.started_at,
            reverse=True
        )

    return results

# START NEW SESSION WITH FIRST MESSAGE ENDPOINT
@router.post("/start", response_model=StartChatSessionResponse)
def start_chat_session(payload: StartChatSessionRequest, db: Session = Depends(get_db)):
    original_text = payload.content.strip()
    if not original_text:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
    
    demo_user = get_or_create_demo_user(db)

    # Create new chat session
    session = ChatSession(
        user_id=demo_user.id, 
        session_active=True
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    reply = build_chat_reply_from_text(
        db=db,
        session_id=session.id,
        original_text=original_text,
        input_type="text",
    )

    return StartChatSessionResponse(
        chat_session_id=session.id,
        user_message=reply.user_message,
        assistant_message=reply.assistant_message,
        note_ready=reply.note_ready,
        missing_slots=reply.missing_slots,
    )

@router.post("/start/audio", response_model=StartChatSessionResponse)
async def start_chat_session_with_audio(
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    demo_user = get_or_create_demo_user(db)

    session = ChatSession(
        user_id=demo_user.id,
        session_active=True
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name
    
    try:
        transcription, detected_language, confidence = transcribe_audio(tmp_path)
        detected_language = (detected_language or "en").lower()
    finally:
        os.remove(tmp_path)

    if not transcription:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")
    
    reply = build_chat_reply_from_text(
        db=db,
        session_id=session.id,
        original_text=transcription,
        input_type="audio",
    )

    return StartChatSessionResponse(
        chat_session_id=session.id,
        user_message=reply.user_message,
        assistant_message=reply.assistant_message,
        note_ready=reply.note_ready,
        missing_slots=reply.missing_slots,
    )

# DATABASE MESSAGES ENDPOINT
@router.get("/{session_id}/message", response_model=list[MessageResponse])
def list_message(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    return (
        db.query(Message)
        .filter(Message.chat_session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )

# TEXT MESSAGE ENDPOINT
@router.post("/{session_id}/message", response_model=ChatReply)
def send_text_message(session_id: int, payload: MessageCreate, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    original_text = payload.content.strip()
    if not original_text:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    return build_chat_reply_from_text(
        db=db,
        session_id=session_id,
        original_text=original_text,
        input_type="text",
    )


# AUDIO MESSAGE ENDPOINT
@router.post("/{session_id}/message/audio", response_model=ChatReply)
async def send_audio_message(
    session_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Save uploaded audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name


    try:
        transcription, detected_language, confidence = transcribe_audio(tmp_path)
        detected_language = (detected_language or "en").lower()
    finally:
        os.remove(tmp_path)

    if not transcription:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    return build_chat_reply_from_text(
        db=db,
        session_id=session_id,
        original_text=transcription,
        input_type="audio",
    )