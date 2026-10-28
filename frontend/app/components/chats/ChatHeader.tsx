import { FaArrowLeft } from 'react-icons/fa'
import { useNavigate } from 'react-router'

interface ChatHeaderProps {
  title?: string
  showBackButton?: boolean
}

const ChatHeader = ({ title, showBackButton }: ChatHeaderProps) => {
  const navigate = useNavigate()

  return (
    <>
      <div className='relative flex items-center gap-2 px-2 sm:px-4 py-2 border-b bg-white'>
        {showBackButton && (
          <>
            <button
              className='absolute left-2 sm:left-4 flex items-center gap-1 px-2 sm:px-4 py-1.5 sm:py-2 rounded-2xl text-xs sm:text-sm text-white bg-gray-400 hover:bg-purple-400 cursor-pointer'
              onClick={() => navigate(-1)}
            >
              <FaArrowLeft /> Back
            </button>
          </>
        )}
        {title ? (
          <>
            <div className='flex-1 flex justify-center'>
              <span className='font-bold text-base sm:text-xl text-purple-700 truncate'>{title || 'AI Assistant'}</span>
            </div>
          </>
        ) : (
          <>
            <span className='font-semibold text-purple-700 text-base sm:text-lg'>AI Assistant</span>
            <span className='text-xs sm:text-sm text-green-500'>● Online</span>
          </>
        )}
      </div>
    </>
  )
}

export default ChatHeader
