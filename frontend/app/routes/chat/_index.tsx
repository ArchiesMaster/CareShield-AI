import { useState } from 'react'
import type { Route } from '../chat/+types/_index'
import ChatHeader from '~/components/chats/ChatHeader'
import ChatInput from '~/components/chats/ChatInput'
import WelcomePanel from '~/components/chats/WelcomePanel'
import { useNavigate } from 'react-router'
import { startChatSession, startChatSessionWithAudio } from '~/lib/api'

export const meta = ({}: Route.MetaArgs) => {
  return [
    { title: 'Chat' },
    {
      name: 'description',
      content: 'Chat with the AI assistant and get insights.'
    }
  ]
}

const ChatPage = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const navigate = useNavigate()

  const handleSendFirstMessage = async (message: string) => {
    const trimmed = message.trim()
    if (!trimmed || isUploading) return

    try {
      setIsUploading(true)

      const data = await startChatSession(trimmed)

      navigate(`/sessions/${data.chat_session_id}`)
    } catch (error) {
      console.error('Error creating chat session with first message:', error)
    } finally {
      setIsUploading(false)
    }
  }

  const handleSendFirstAudio = async (audioBlob: Blob) => {
    if (isUploading) return

    try {
      setIsUploading(true)

      const data = await startChatSessionWithAudio(audioBlob)

      navigate(`/sessions/${data.chat_session_id}`)
    } catch (error) {
      console.error('Error creating chat session with first audio message:', error)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className='flex flex-col h-[calc(100vh-56px)] bg-gray-100'>
      <ChatHeader />
      <WelcomePanel />
      <ChatInput
        onSend={handleSendFirstMessage}
        onSendAudio={handleSendFirstAudio}
        onRecordingStateChange={setIsRecording}
        isUploading={isUploading}
        isRecording={isRecording}
      />
    </div>
  )
}

export default ChatPage
