# CareShield – Conversational Case Noting System

## Overview

CareShield is a prototype conversational case noting application developed for an aged care setting. It combines a React interface with a FastAPI backend to help support workers capture information through text or voice and generate structured case notes using locally hosted AI models.

The project explores ways to reduce administrative work while preserving original input, translations and conversation history. This repository presents the prototype for demonstration and portfolio purposes.

## Project Status

The prototype includes a connected chat interface, backend API, database models, speech transcription and AI extraction pipeline. It is not production-ready.

Authentication and authorisation are not implemented. The API does not enforce user ownership of sessions or case notes, and the demonstration workflow uses a shared demo user. Run it only in a controlled development environment with synthetic data. Do not expose the API publicly or use real care records.

AI-generated notes require human review. Transcription, translation, classification and extraction can be incomplete or inaccurate.

---

## Features

- **Conversational capture:** enter case information through a chat interface.
- **Voice input:** transcribe browser audio using faster-whisper and FFmpeg.
- **Language handling:** detect input language and translate non-English content into English.
- **Follow-up questions:** generate questions to collect additional details, with limits to reduce repeated questioning.
- **Structured extraction:** extract report type, category, incident details, severity, escalation indicators and a summary.
- **Persistent records:** store sessions, messages and generated case notes in PostgreSQL.
- **Record browsing:** view previous conversations and generated case notes.
- **Optional email notifications:** send case note notifications when SMTP configuration is supplied and notifications are enabled.

The extraction pipeline distinguishes incident reports, feedback or complaints, and general case notes. These classifications are prototype AI outputs, not validated operational decisions.

---

## Technology Stack

| Layer                | Technologies                                        |
| -------------------- | --------------------------------------------------- |
| Frontend             | React, TypeScript, React Router, Vite, Tailwind CSS |
| Backend              | Python, FastAPI, Pydantic, SQLAlchemy               |
| Database             | PostgreSQL, psycopg                                 |
| Speech transcription | faster-whisper, FFmpeg                              |
| Language detection   | langdetect                                          |
| Language model       | Ollama with `qwen2.5:32b`                           |
| Packaging            | Separate frontend and backend Dockerfiles           |

---

## System Architecture

The system follows a layered architecture:

- **Frontend Layer**: User interface for chat interaction
- **Application Layer**:
  - Backend API (FastAPI)
  - Conversation Manager
  - Validation & Classification
- **AI Service Layer**:
  - Speech-to-Text (Whisper)
  - Language Detection & Translation
  - LLM (via Ollama)
- **Data Layer**:
  - PostgreSQL database

  The frontend sends text or audio to the FastAPI backend. Audio is converted and transcribed before entering the conversation pipeline. The backend detects language, requests translations or follow-up questions from Ollama, and saves messages to PostgreSQL. When a note is generated, the extraction pipeline produces structured fields and a summary for storage and display.

---

## Project Structure

```text
CareShield/
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py
│   └── app/
│       ├── main.py          # FastAPI entry point
│       ├── api/             # Session and case note endpoints
│       ├── core/            # Local configuration; excluded from Git
│       ├── db/              # Database connection and models
│       ├── schemas/         # API request and response schemas
│       └── services/        # Conversation, LLM, speech and email services
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── app/                 # Routes, components, types and API client
    └── public/              # Static assets
```

Local recordings, legacy scripts, environment files, databases and generated build files are excluded from the public source where configured in `.gitignore`.

---

## Local Setup

### Prerequisites

- Python 3.11 or later; the backend Dockerfile uses Python 3.11.
- A Node.js version compatible with the versions in `frontend/package-lock.json`.
- PostgreSQL running locally or in a development container.
- FFmpeg installed and available on `PATH`.
- Ollama installed and running, with enough memory for the selected model. `qwen2.5:32b` requires substantial resources.

### 1. Restore local configuration

The `backend/app/core/` directory is intentionally excluded from Git. Before starting the backend, create `backend/app/core/config.py` containing a `settings` object compatible with the imports in the application.

If a sanitised configuration template is included with your copy, use it as the starting point. A fresh clone cannot run without this local configuration. The following minimal example provides the settings used by the application:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CareShieldAPI"
    app_env: str = "development"
    debug: bool = False
    api_prefix: str = "/api"
    database_url: str
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "qwen2.5:32b"

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()
```

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=postgresql+psycopg://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/careshield
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:32b
DEBUG=false
```

Replace the database placeholders with local development credentials and create the `careshield` database before starting the backend. The application creates its tables at startup; schema migrations are not provided.

The relative `.env` path above assumes the backend is launched from the `backend/` directory. Keep `.env` out of Git. Any committed `.env.example` should contain placeholders only.

For containers, adjust hostnames to match your network. `host.docker.internal` can refer to the host from a suitably configured container; `localhost` refers to the container itself.

### 2. Prepare Ollama

```bash
ollama pull qwen2.5:32b
```

Ensure the Ollama service is running. Using another model may require prompt changes and additional validation.

### 3. Start the backend

From the project root:

```bash
cd backend
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Then install dependencies and start the API:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API documentation: <http://localhost:8000/docs>

Health endpoint: <http://localhost:8000/health>

Whisper model files may be downloaded on first use or startup. Model loading can take time.

### 4. Start the frontend

Create `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api
```

In a separate terminal:

```bash
cd frontend
npm ci --legacy-peer-deps
npm run dev
```

Open the URL printed by the development server. Microphone access requires browser permission and a secure context such as HTTPS or localhost.

The frontend API address must be reachable from the browser. Rebuild the frontend after changing its API URL for a production build.

---

### Optional email configuration

Notifications are disabled by default. To enable them, supply these variables in the backend process environment:

```dotenv
EMAIL_NOTIFICATIONS_ENABLED=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=YOUR_SMTP_USERNAME
SMTP_PASSWORD=YOUR_SMTP_PASSWORD
SMTP_FROM_EMAIL=demo@example.com
CARE_PARTNER_EMAIL=recipient@example.com
```

The email module reads variables through `os.getenv`; placing them in the Pydantic `.env` file alone does not populate the process environment for this module. Export them in your shell or supply them through your container runtime.

Notifications include case note details and a summary. Use a test mailbox and synthetic records for demonstrations.

---

## Limitations and Security

- Authentication, authorisation and per-user record access controls are absent.
- The API currently permits broad cross-origin access. Configure explicit allowed origins before deployment.
- Debug logging prints transcripts, translations and extracted reports. Remove or redact this logging before handling sensitive information.
- Audio upload limits, rate limits and processing timeouts require further hardening.
- AI extraction uses fallback behaviour when output cannot be parsed. Human review is required before relying on generated records or escalation indicators.
- A completed conversation does not guarantee that all required information has been collected.
- The prototype does not provide a complete operational audit, retention, backup or recovery system.
- Dockerfiles are provided, but database networking, model access, secrets and configuration must be supplied separately. They are not a complete deployment environment.

A VPN alone does not replace application access controls. Before operational use, implement security controls, validate AI behaviour and complete appropriate testing.

---

## Future Work

- Implement authentication, authorisation and record ownership checks.
- Add structured validation and human approval of generated case notes.
- Improve multilingual handling and extraction evaluation.
- Add automated backend and integration tests.
- Introduce database migrations and pinned Python dependencies.
- Harden logging, uploads, error handling and deployment configuration.
- Explore reporting and integration with existing care systems.
