interface MessageBubbleProps {
  text: string
  sender: 'user' | 'ai'
}

const MessageBubble = ({ text, sender }: MessageBubbleProps) => {
  const isUser = sender === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} items-end`}>
      <div
        className={`rounded-lg px-3 sm:px-4 py-2 sm:py-2.5 text-sm sm:text-base shadow max-w-[80vw] sm:max-w-md md:max-w-lg wrap-break-word
          ${isUser ? 'bg-purple-600 text-white ml-auto' : 'bg-white border text-gray-900 mr-auto'}`}
        style={{ whiteSpace: 'pre-wrap' }}
      >
        {text}
      </div>
    </div>
  )
}

export default MessageBubble
