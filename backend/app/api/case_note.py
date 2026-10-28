from app.services.email_module import send_case_note_notification_email
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date, time
import re

from app.db.base import get_db
from app.db.tables import ChatSession, Message, CaseNote
from app.schemas.case_note import CaseNoteResponse
from app.services.chat_module import final_extraction

router = APIRouter(prefix="/case-notes", tags=["case-notes"])

def parse_bool(value, default=False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    
    text = str(value).strip().lower()

    if text in {"true", "yes", "y", "1"}:
        return True
    
    if text in {"false", "no", "n", "0"}:
        return False
    
    return default

def parse_date(value):
    if not value:
        return None
    
    text = str(value).strip().lower()

    if text == "today":
        return date.today()
    
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None
    
def parse_time(value):
    if not value:
        return None
    
    text = str(value).strip().lower()

    # Remove approximate qualifiers
    text = text.replace("approximately", "").replace("approx.", "").replace("around", "").replace("about", "").strip()

    # Match 24-hour time formats (e.g. "14:30", "10:00")
    match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        return time(hour=hour, minute=minute)
    
    # Match 12-hour time formats (e.g. "3 PM", "10 AM")
    match = re.search(r"\b(1[0-2]|0?[1-9])\s*(am|pm)\b", text)
    if match:
        hour = int(match.group(1))
        meridiem = match.group(2)
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        return time(hour=hour, minute=0)
    
    return None


@router.get("", response_model=list[CaseNoteResponse])
def list_case_notes(db: Session = Depends(get_db)):
    return db.query(CaseNote).order_by(CaseNote.id.desc()).all()

@router.get("/by-session/{session_id}", response_model=CaseNoteResponse)
def get_case_note_by_session(session_id: int, db: Session = Depends(get_db)):
    case_note = (
        db.query(CaseNote)
        .filter(CaseNote.chat_session_id == session_id)
        .first()
    )
    if not case_note:
        raise HTTPException(status_code=404, detail="Case note not found for this session")
    
    return case_note

@router.get("/{case_note_id}", response_model=CaseNoteResponse)
def get_case_note(case_note_id: int, db: Session = Depends(get_db)):
    case_note = db.query(CaseNote).filter(CaseNote.id == case_note_id).first()
    if not case_note:
        raise HTTPException(status_code=404, detail="Case note not found")
    return case_note


@router.post("/{session_id}/generate", response_model=CaseNoteResponse)
def generate_case_note(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Prevent duplicate case notes
    existing = db.query(CaseNote).filter(CaseNote.chat_session_id == session_id).first()
    if existing:
        return existing
    
    messages = (
        db.query(Message)
        .filter(Message.chat_session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    if not messages:
        raise HTTPException(status_code=400, detail="No messages found")
    
    case_record = {
        "conversation_log": [],
        "full_original_text": "",
        "full_translated_text": "",
        "languages": [] 
    }

    for msg in messages:
        role = "user" if msg.message_sender_role == "user" else "assistant"

        detected_lang = (msg.detected_language or "en").lower()

        was_translated = bool(
            msg.translated_content
            and detected_lang != "en"
        )

        log_entry = {
            "role": role,
            "timestamp": str(msg.created_at),
            "message": msg.content,
            "translated_message": msg.translated_content,
            "original_language": detected_lang,
            "was_translated": was_translated,
            "input_type": msg.input_type,
        }

        case_record["conversation_log"].append(log_entry)

        if role == "user":
            # Accumulate original text
            case_record["full_original_text"] += " " + (msg.content or "")

            # Accumulate translated text (fallback to original if English)
            case_record["full_translated_text"] += " " + (
                msg.translated_content if msg.translated_content else msg.content
            )

            # Track languages (avoid duplicates)
            detected_lang = (msg.detected_language or "en").lower()
            if detected_lang not in case_record["languages"]:
                case_record["languages"].append(detected_lang)

    case_record["full_original_text"] = case_record["full_original_text"].strip()
    case_record["full_translated_text"] = case_record["full_translated_text"].strip()

    # Run AI extraction
    final_case = final_extraction(case_record)

    # Preserve detected languages inside metadata
    final_case["languages"] = case_record.get("languages", [])

    # Use first detected language for DB column compatibility
    primary_language = (
        case_record["languages"][0]
        if case_record.get("languages")
        else "en"
    )

    report_type = final_case.get("report_type") or "case_note"
    category = final_case.get("category") or "other"

    incident_occurred = parse_bool(
        final_case.get("incident_occurred"),
        default=(report_type == "incident")
    )

    incident_date = parse_date(final_case.get("incident_date"))
    incident_time = parse_time(final_case.get("incident_time"))
    incident_type = final_case.get("incident_type") or category
    location = final_case.get("location")
    injury_status = final_case.get("injury_status")
    summary = final_case.get("summary") or case_record["full_original_text"]
    reported_timestamp = datetime.now()

    case_note = CaseNote(
        chat_session_id=session_id,
        user_id=session.user_id,
        original_text=case_record["full_original_text"],
        original_language=primary_language,
        english_translation=case_record["full_translated_text"],
        incident_occurred=incident_occurred,
        incident_date=incident_date,
        incident_time=incident_time,
        incident_type=incident_type,
        location=location,
        injury_status=injury_status,
        summary=summary,
        metadata_json=final_case,
        reported_timestamp=reported_timestamp,
    )
    
    db.add(case_note)
    session.session_active = False
    session.ended_at = datetime.now()
    db.commit()
    db.refresh(case_note)

    send_case_note_notification_email(case_note)

    return case_note