import type { StartChatSessionResponse } from '~/types/session'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://host.docker.internal:8000/api'

export async function createChatSession() {
  const res = await fetch(`${API_BASE_URL}/chat-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  if (!res.ok) throw new Error('Failed to create chat session')
  return res.json()
}

export async function getChatSessions() {
  const res = await fetch(`${API_BASE_URL}/chat-session`)
  if (!res.ok) throw new Error('Failed to fetch chat sessions')
  return res.json()
}

export async function sendMessage(sessionId: number, content: string) {
  const res = await fetch(`${API_BASE_URL}/chat-session/${sessionId}/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content })
  })
  if (!res.ok) throw new Error('Failed to send message')
  return res.json()
}

export async function getMessages(sessionId: number) {
  const res = await fetch(`${API_BASE_URL}/chat-session/${sessionId}/message`)
  if (!res.ok) throw new Error('Failed to fetch messages')
  return res.json()
}

export async function generateCaseNote(sessionId: number) {
  const res = await fetch(`${API_BASE_URL}/case-notes/${sessionId}/generate`, {
    method: 'POST'
  })
  if (!res.ok) throw new Error('Failed to generate case note')
  return res.json()
}

export async function getCaseNotes() {
  const res = await fetch(`${API_BASE_URL}/case-notes`)
  if (!res.ok) throw new Error('Failed to fetch case notes')
  return res.json()
}

export async function getCaseNote(id: number) {
  const res = await fetch(`${API_BASE_URL}/case-notes/${id}`)
  if (!res.ok) throw new Error('Failed to fetch case note')
  return res.json()
}

export async function getCaseNoteBySession(sessionId: string | number) {
  const res = await fetch(`${API_BASE_URL}/case-notes/by-session/${sessionId}`)

  if (res.status === 404) {
    return null // No case note for this session, but that's not an error
  }

  if (!res.ok) throw new Error('Failed to fetch case note for session')
  return res.json()
}

export async function startChatSession(content: string): Promise<StartChatSessionResponse> {
  const res = await fetch(`${API_BASE_URL}/chat-session/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content })
  })

  if (!res.ok) throw new Error('Failed to start chat session')
  return res.json()
}

export async function startChatSessionWithAudio(audioBlob: Blob): Promise<StartChatSessionResponse> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')

  const res = await fetch(`${API_BASE_URL}/chat-session/start/audio`, {
    method: 'POST',
    body: formData
  })

  if (!res.ok) throw new Error('Failed to start chat session with audio')
  return res.json()
}
