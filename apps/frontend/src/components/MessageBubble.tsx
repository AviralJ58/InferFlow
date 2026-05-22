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
        {message.content === '' && !isUser && !message.error ? (
          <div className="flex gap-1.5 h-5 items-center px-1">
            <span className="w-2 h-2 rounded-full bg-white animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 rounded-full bg-white animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 rounded-full bg-white animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {message.content && <div>{message.content}</div>}
            {message.error && (
              <div className="text-red-400 text-sm flex items-center gap-2 bg-red-500/10 p-2.5 rounded border border-red-500/20 mt-1">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{message.error}</span>
              </div>
            )}
          </div>
        )}
        
        {/* Metadata Footer */}
        {message.metadata && Object.keys(message.metadata).length > 0 && !isUser && (
          <div className="mt-3 pt-2 border-t border-surface-700/50 flex items-center justify-between text-[10px] text-surface-400 font-mono">
            <div className="flex gap-3">
              {message.metadata.provider && (
                <span>{message.metadata.provider.toUpperCase()} : {message.metadata.model}</span>
              )}
              {message.metadata.ttft_ms && (
                <span>TTFT: {message.metadata.ttft_ms}ms</span>
              )}
              {message.metadata.total_latency_ms && (
                <span>Total: {(message.metadata.total_latency_ms / 1000).toFixed(2)}s</span>
              )}
            </div>
            {message.metadata.request_id && (
              <span className="opacity-50" title={message.metadata.request_id}>
                {message.metadata.request_id.split('-')[0]}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
