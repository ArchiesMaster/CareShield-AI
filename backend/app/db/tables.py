from datetime import datetime , date, time
from sqlalchemy import DateTime, Integer, String, ForeignKey, Boolean, Text, JSON, Date, Time, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

"""
User
1 user to N chat sessions
1 user to N case notes

ChatSession
1 chat session to 1 user
1 chat session to N messages
1 chat session to 1 case note

Message
1 message to 1 chat session

CaseNote
1 case note to 1 user
1 case note to 1 chat session
"""

#----------------
### USERS TABLE ###
#----------------
class User(Base):
    __tablename__ = "user"

    #Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    first_name: Mapped[str] = mapped_column(String(63), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(63), nullable=True)
    last_name: Mapped[str] = mapped_column(String(63), nullable=False)

    email: Mapped[str] = mapped_column(String(255),unique=True, index=True, nullable=False)
    #hashed password
    password: Mapped[str] = mapped_column(String(63), nullable=False)

    role: Mapped[str] = mapped_column(String(63), default="support_worker")

    # 1:N
    chat_session = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

    case_note = relationship("CaseNote", back_populates="user", cascade="all, delete-orphan")



#----------------
### CHAT SESSION TABLE ###
#----------------
class ChatSession(Base):
    __tablename__ = "chat_session"

    #Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    #Foreign key
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    session_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 1:N
    user = relationship("User", back_populates="chat_session")
    # 1:N
    message = relationship("Message", back_populates="chat_session", cascade="all, delete-orphan")
    # 1:1
    case_note = relationship("CaseNote", back_populates="chat_session", uselist=False)



#----------------
### MESSAGE TABLE ###
#----------------
class Message(Base):
    __tablename__ = "message"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Foreign key
    chat_session_id: Mapped[int] = mapped_column(ForeignKey("chat_session.id"), nullable=False)

    message_sender_role: Mapped[str] = mapped_column(String(63), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    translated_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_language: Mapped[str] = mapped_column(String(63), default="en")
    input_type = Column(String, default="text") # Added
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Add was_translated property flag
    @property
    def was_translated(self) -> bool:
        return bool(
            self.translated_content
            and self.detected_language
            and self.detected_language.lower() != "en"
        )

    chat_session = relationship("ChatSession", back_populates="message")

#----------------
### CASE NOTES TABLE ###
#----------------

class CaseNote(Base):
    __tablename__ = "case_note"
    #Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    #Foreign key
    chat_session_id: Mapped[int] = mapped_column(ForeignKey("chat_session.id"), nullable=False, unique=True)
    #Foreign key
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    original_language: Mapped[str] = mapped_column(String(63), default="en")
    english_translation: Mapped[str | None] = mapped_column(Text, nullable=True)

    incident_occurred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    incident_date : Mapped[date | None] = mapped_column(Date, nullable=True)
    incident_time : Mapped[time | None] = mapped_column(Time, nullable=True)
    incident_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    injury_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reported_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    summary: Mapped[str] = mapped_column(Text, nullable=False)

    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    user = relationship("User", back_populates="case_note")
    chat_session = relationship("ChatSession", back_populates="case_note")




