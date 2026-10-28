import { useState, useRef } from 'react'
import { FaMicrophone, FaStop, FaPaperPlane, FaSpinner } from 'react-icons/fa'

interface ChatInputProps {
  onSend: (text: string) => void
  onSendAudio: (audio: Blob) => Promise<void>
  isUploading: boolean
  isRecording: boolean
  onRecordingStateChange: (recording: boolean) => void
}

const ChatInput = ({ onSend, onSendAudio, isUploading, isRecording, onRecordingStateChange }: ChatInputProps) => {
  const [value, setValue] = useState('')

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  // Handle text input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value)
  }

  // Send text message
  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (value.trim()) {
      onSend(value)
      setValue('')
    }
  }

  // Start recording
  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      alert('Your browser does not support audio recording.')
      return
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus'
    })

    mediaRecorderRef.current = mediaRecorder
    chunksRef.current = []

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunksRef.current.push(e.data)
      }
    }

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(chunksRef.current, {
        type: 'audio/webm;codecs=opus'
      })

      chunksRef.current = []

      await onSendAudio(audioBlob)
    }

    mediaRecorder.start()
    onRecordingStateChange(true)
  }

  // Stop recording
  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    onRecordingStateChange(false)
  }

  return (
    <form
      className='flex items-center gap-2 px-2 sm:px-4 py-2 sm:py-3 border-t bg-white relative'
      onSubmit={handleSend}
    >
      {/* Voice button - left */}
      <button
        type='button'
        onClick={isRecording ? stopRecording : startRecording}
        className={`absolute left-3 sm:left-6 p-2 sm:p-3 rounded-full ${
          isRecording ? 'bg-red-100' : 'bg-gray-100'
        } hover:bg-purple-200 transition-colors`}
        aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
        style={{ zIndex: 2 }}
        disabled={isUploading}
      >
        {isRecording ? (
          <FaStop className='w-5 h-5 sm:w-6 sm:h-6 text-red-600' />
        ) : (
          <FaMicrophone className='w-5 h-5 sm:w-6 sm:h-6 text-purple-700' />
        )}
      </button>

      {/* Input - center */}
      <input
        className='flex-1 border rounded-full px-12 py-2 sm:py-3 focus:outline-none bg-gray-50 text-gray-900 placeholder-gray-400 text-sm sm:text-base'
        placeholder={
          isRecording
            ? 'Recording...'
            : isUploading
              ? 'Uploading...'
              : 'Type or press the mic to record your message...'
        }
        value={value}
        onChange={handleChange}
        autoComplete='off'
        disabled={isRecording || isUploading}
        style={{ textIndent: 8, paddingRight: 48 }}
      />

      {/* Send button - right */}
      <button
        type='submit'
        className='absolute right-3 sm:right-6 bg-purple-700 text-white p-2 sm:p-3 rounded-full flex items-center justify-center transition-colors'
        aria-label='Send message'
        style={{ zIndex: 2 }}
        disabled={isRecording || isUploading || !value.trim()}
      >
        {isUploading ? (
          <FaSpinner className='w-5 h-5 sm:w-6 sm:h-6 animate-spin' />
        ) : (
          <FaPaperPlane
            className={`w-5 h-5 sm:w-6 sm:h-6 ${isRecording || isUploading || !value.trim() ? 'opacity-50' : ''}`}
          />
        )}
      </button>
    </form>
  )
}

export default ChatInput
