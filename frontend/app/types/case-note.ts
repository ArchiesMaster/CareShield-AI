export type ConversationEntry = {
  role: string
  timestamp: string
  message: string
  translated_message?: string
  original_language?: string
  was_translated?: boolean
  input_type?: string // Added
}

export type CaseNoteMetadata = {
  conversation_log: ConversationEntry[]
  languages?: string[]
  patient?: string | null
  client?: string | null
  participant?: string | null
  severity?: string | null
  escalation_required?: string | null
  report_type?: string | null
  category?: string | null
  incident_type?: string | null
  confidence?: number | null
  last_updated?: string
}

export type CaseNote = {
  id: number
  chat_session_id: number
  original_text: string
  original_language: string
  english_translation?: string | null
  incident_occurred: boolean
  incident_date?: string | null
  incident_time?: string | null
  incident_type?: string | null
  location?: string | null
  injury_status: string | null
  summary: string
  metadata_json?: CaseNoteMetadata | null
  reported_timestamp: string
}
