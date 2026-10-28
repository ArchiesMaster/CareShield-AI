export type SessionListItem = {
  id: number
  session_active: boolean
  started_at: string
  ended_at: string | null
  title: string
  last_message: string | null
  last_message_at: string | null
}

export type StartChatSessionResponse = {
  chat_session_id: number
  user_message: {
    id: number
    message_sender_role: string
    content: string
    translated_content?: string | null
    detected_language: string
    created_at: string
    was_translated: boolean
  }
  assistant_message: {
    id: number
    message_sender_role: string
    content: string
    translated_content?: string | null
    detected_language: string
    created_at: string
    was_translated: boolean
  } | null
  note_ready: boolean
  missing_slots: string[]
}
