import { nanoid } from 'nanoid'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import ChatHeader from '~/components/chats/ChatHeader'
import ChatInput from '~/components/chats/ChatInput'
import ChatMessages from '~/components/chats/ChatMessages'
import type { ChatMessage } from '~/types/chat'
import { getMessages, sendMessage, generateCaseNote, API_BASE_URL, getCaseNoteBySession } from '~/lib/api'
import type { CaseNote, CaseNoteMetadata } from '~/types/case-note'
import { toast } from 'react-toastify'

const buildIncidentSummary = (caseNote: CaseNote) => {
  const metadata = caseNote.metadata_json ?? ({} as CaseNoteMetadata)

  const rawConfidence = metadata.confidence
  const confidence =
    typeof rawConfidence === 'number'
      ? rawConfidence
      : typeof rawConfidence === 'string'
        ? Number(rawConfidence)
        : undefined

  return {
    caseNoteId: caseNote.id,
    incidentType: caseNote.incident_type || metadata.incident_type || metadata.report_type || 'Case Note',

    details: [
      caseNote.location ? `Location: ${caseNote.location}` : null,
      caseNote.injury_status ? `Injury/status: ${caseNote.injury_status}` : null,
      caseNote.incident_date ? `Date: ${caseNote.incident_date}` : null,
      caseNote.incident_time ? `Time: ${caseNote.incident_time}` : null,
      metadata.severity ? `Severity: ${metadata.severity}` : null,
      metadata.escalation_required ? `Escalation required: ${metadata.escalation_required}` : null
    ].filter(Boolean) as string[],
    confidence,
    createdAt: caseNote.reported_timestamp
  }
}

const createCaseNoteCardMessage = (caseNote: CaseNote): ChatMessage => {
  return {
    id: `case-note-${caseNote.id}`,
    sender: 'ai',
    structuredOutput: buildIncidentSummary(caseNote)
  }
}

const SessionDetailPage = () => {
  const { id: sessionId } = useParams()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isRecording, setIsRecording] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isGeneratingNote, setIsGeneratingNote] = useState(false)
  const [isAwaitingResponse, setIsAwaitingResponse] = useState(false)
  const [sessionTitle, setSessionTitle] = useState('Chat Session')

  // Fetch existing messages when the page loads
  useEffect(() => {
    const fetchSessionMessages = async () => {
      if (!sessionId) return

      try {
        const data = await getMessages(Number(sessionId))

        // Map backend messages to frontend format
        const mappedMessages: ChatMessage[] = data.map((msg: any) => ({
          id: msg.id.toString(),
          sender: msg.message_sender_role === 'assistant' ? 'ai' : 'user',
          text: msg.content
        }))

        const existingCaseNote = await getCaseNoteBySession(Number(sessionId))

        if (existingCaseNote) {
          const caseNoteCard = createCaseNoteCardMessage(existingCaseNote)
          setMessages([...mappedMessages, caseNoteCard])
        } else {
          setMessages(mappedMessages)
        }

        // Set session title based on first message (kept for internal use if needed)
        if (mappedMessages.length > 0 && mappedMessages[0]?.text) {
          setSessionTitle(mappedMessages[0].text.slice(0, 50))
        }
      } catch (error) {
        console.error('Error fetching session messages:', error)
      }
    }

    fetchSessionMessages()
  }, [sessionId])

  // Send text message to backend and handle automatic case note generation
  const handleSend = async (text: string) => {
    if (!sessionId || isGeneratingNote || isAwaitingResponse) return

    setIsAwaitingResponse(true)

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: nanoid(),
      sender: 'user',
      text
    }

    const typingId = nanoid()

    setMessages((prev) => [
      ...prev,
      userMessage,
      {
        id: typingId,
        sender: 'ai',
        status: 'typing'
      }
    ])

    try {
      const reply = await sendMessage(Number(sessionId), text)

      // Replace typing indicator with real AI response
      if (reply.assistant_message) {
        setMessages((prev) =>
          prev
            .filter((msg) => msg.id !== typingId)
            .concat({
              id: reply.assistant_message.id.toString(),
              sender: 'ai',
              text: reply.assistant_message.content
            })
        )
      }

      if (reply.note_ready) {
        setIsGeneratingNote(true)

        setMessages((prev) => [
          ...prev,
          {
            id: nanoid(),
            sender: 'ai',
            text: 'All required information has been collected. Generating case note...'
          }
        ])

        try {
          const caseNote = await generateCaseNote(Number(sessionId))

          setMessages((prev) => [
            ...prev.filter((msg) => !msg.status && msg.id !== `case-note-${caseNote.id}`),
            {
              id: nanoid(),
              sender: 'ai',
              text: 'All required information has been collected. The case note has been generated below.'
            },
            createCaseNoteCardMessage(caseNote)
          ])

          toast.success(
            <div>
              <div>Case note generated successfully!</div>
              <div>A notification email has been sent to the care partner.</div>
            </div>
          )
        } catch (error) {
          console.error('Error generating case note:', error)
          setMessages((prev) => [
            ...prev,
            {
              id: nanoid(),
              sender: 'ai',
              text: 'There was an error generating the case note. Please try again.'
            }
          ])
          toast.error('Failed to generate case note.')
        } finally {
          setIsGeneratingNote(false)
          setIsAwaitingResponse(false)
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages((prev) => prev.filter((msg) => msg.id !== typingId))
    } finally {
      setIsAwaitingResponse(false)
    }
  }

  // Audio handling
  const handleSendAudio = async (audioBlob: Blob) => {
    if (!sessionId || isGeneratingNote || isAwaitingResponse) return

    setIsAwaitingResponse(true)

    const tempId = nanoid()
    const typingId = nanoid()

    setMessages((msgs) => [
      ...msgs,
      { id: tempId, sender: 'user', status: 'uploading' },
      { id: typingId, sender: 'ai', status: 'typing' }
    ])

    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')

      const response = await fetch(`${API_BASE_URL}/chat-session/${sessionId}/message/audio`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Failed to send audio message')
      }

      const reply = await response.json()

      // Replace uploading + typing with real messages
      setMessages((msgs) =>
        msgs
          .filter((msg) => msg.id !== tempId && msg.id !== typingId)
          .concat(
            [
              {
                id: reply.user_message.id.toString(),
                sender: 'user',
                text: reply.user_message.content
              },
              reply.assistant_message && {
                id: reply.assistant_message.id.toString(),
                sender: 'ai',
                text: reply.assistant_message.content
              }
            ].filter(Boolean)
          )
      )

      if (reply.note_ready) {
        setIsGeneratingNote(true)

        setMessages((prev) => [
          ...prev,
          {
            id: nanoid(),
            sender: 'ai',
            text: 'All required information has been collected. Generating case note...'
          }
        ])

        const caseNote = await generateCaseNote(Number(sessionId))

        setMessages((prev) => [
          ...prev.filter((msg) => !msg.status && msg.id !== `case-note-${caseNote.id}`),
          {
            id: nanoid(),
            sender: 'ai',
            text: 'All required information has been collected. The case note has been generated below.'
          },
          createCaseNoteCardMessage(caseNote)
        ])

        toast.success(
          <div>
            <div>Case note generated successfully!</div>
            <div>A notification email has been sent to the care partner.</div>
          </div>
        )

        setIsGeneratingNote(false)
      }
    } catch (error) {
      console.error('Error uploading audio:', error)
      toast.error('Failed to upload audio.')

      setMessages((msgs) =>
        msgs
          .filter((msg) => msg.id !== tempId && msg.id !== typingId)
          .concat({
            id: nanoid(),
            sender: 'ai',
            text: 'There was an error processing the audio. Please try again.'
          })
      )
    } finally {
      setIsUploading(false)
      setIsAwaitingResponse(false)
    }
  }

  // Handle recording state changes to show "Recording..." message
  const handleRecordingStateChange = (recording: boolean) => {
    setIsRecording(recording)
    if (recording) {
      setMessages((msgs) => [
        ...msgs,
        {
          id: nanoid(),
          sender: 'user',
          status: 'recording'
        }
      ])
    } else {
      setMessages((msgs) => msgs.filter((msg) => !(msg.sender === 'user' && msg.status === 'recording')))
    }
  }

  return (
    <div className='flex flex-col h-[calc(100vh-56px)] bg-gray-100'>
      <ChatHeader />

      <ChatMessages messages={messages} />

      <ChatInput
        onSend={handleSend}
        onSendAudio={handleSendAudio}
        onRecordingStateChange={handleRecordingStateChange}
        isUploading={isUploading || isGeneratingNote || isAwaitingResponse}
        isRecording={isRecording}
      />
    </div>
  )
}

export default SessionDetailPage
