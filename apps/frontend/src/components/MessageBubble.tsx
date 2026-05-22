import { Message } from '../api/client'

interface MessageBubbleProps {
  message: Message
}

/**
 * Individual message bubble component.
 *
 * Renders user and assistant messages with different styles.
 * Future: markdown rendering, code highlighting, copy button.
 */
function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex items-start gap-3 animate-slide-up ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
          isUser
            ? 'bg-gradient-to-br from-violet-500 to-purple-600'
            : 'bg-gradient-to-br from-primary-500 to-primary-700'
        }`}
      >
        <span className="text-white font-bold text-xs">
          {isUser ? 'U' : 'IF'}
        </span>
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-primary-600/20 border border-primary-500/20 text-surface-100 rounded-tr-md'
            : 'glass-subtle text-surface-200 rounded-tl-md'
        }`}
      >
        {message.content}
      </div>
    </div>
  )
}

export default MessageBubble
