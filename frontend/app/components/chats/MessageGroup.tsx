import MessageBubble from './MessageBubble'
import StatusBubble from './StatusBubble'
import Avatar from './Avatar'
import userAvatar from '~/assets/images/avatar.png'
import aiAvatar from '~/assets/images/avatar-ai.svg'

import type { ChatMessage } from '~/types/chat'
import IncidentSummaryCard from './IncidentSummaryCard'

interface MessageGroupProps {
  group: ChatMessage[]
}

const MessageGroup = ({ group }: MessageGroupProps) => {
  const isUser = group[0].sender === 'user'
  const avatarSrc = isUser ? userAvatar : aiAvatar
  const avatarAlt = isUser ? 'User' : 'AI'

  return (
    <div className={`flex flex-col gap-1 sm:gap-2 ${isUser ? 'items-end' : 'items-start'}`}>
      {group.map((msg, idx) => {
        const isFirst = idx === 0
        return (
          <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} items-end`}>
            {/* Display avatar for the first message in the group */}
            {isFirst && !isUser && <Avatar src={avatarSrc} alt={avatarAlt} className='mr-2 sm:mr-3' />}
            <div className={isFirst ? '' : isUser ? 'mr-10 sm:mr-12 max-w-[80vw] sm:max-w-md' : 'ml-10 sm:ml-12 max-w-[80vw] sm:max-w-md'}>
              {msg.structuredOutput ? (
                <IncidentSummaryCard summary={msg.structuredOutput} />
              ) : msg.status ? (
                <StatusBubble status={msg.status} />
              ) : (
                <MessageBubble text={msg.text || ''} sender={msg.sender} />
              )}
            </div>
            {isFirst && isUser && <Avatar src={avatarSrc} alt={avatarAlt} className='ml-2 sm:ml-3' />}
          </div>
        )
      })}
    </div>
  )
}

export default MessageGroup
