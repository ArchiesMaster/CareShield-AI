from datetime import datetime, date, time
from pydantic import BaseModel

class CaseNoteResponse(BaseModel):
    id: int
    chat_session_id: int
    original_text: str
    original_language: str
    english_translation: str | None
    incident_occurred: bool
    incident_date: date | None
    incident_time: time | None
    incident_type: str | None
    location: str | None
    injury_status: str | None
    summary: str
    metadata_json: dict | None
    reported_timestamp: datetime

    class Config:
        from_attributes = True
        