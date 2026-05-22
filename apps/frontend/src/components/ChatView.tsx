import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'
import { ApiClient, Message } from '../api/client'

interface ChatViewProps {
  activeConversationId: string | null;
  onMessageSent: () => void;
}

function ChatView({ activeConversationId, onMessageSent }: ChatViewProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [cancelStream, setCancelStream] = useState<(() => void) | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Load conversation messages when active ID changes
  useEffect(() => {
    if (activeConversationId) {
      loadMessages(activeConversationId)
    } else {
      setMessages([])
    }
  }, [activeConversationId])

  const loadMessages = async (id: string) => {
    try {
      const conv = await ApiClient.getConversation(id)
      setMessages(conv.messages)
    } catch (e) {
      console.error(e)
    }
  }

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const handleSend = async () => {
    if (!input.trim() || isLoading || !activeConversationId) return

    const userMessageContent = input.trim()
    setInput('')
    setIsLoading(true)

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessageContent,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMsg])

    // Optimistically add empty assistant message to stream into
    const tempAssistantId = (Date.now() + 1).toString()
    const tempAssistantMsg: Message = {
      id: tempAssistantId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempAssistantMsg])

    const cancel = ApiClient.streamChat(
      activeConversationId,
      userMessageContent,
      (data) => {
        // Handle token event
        setMessages(prev => {
          const newMsgs = [...prev]
          const lastIdx = newMsgs.length - 1
          const target = newMsgs[lastIdx]
          
          // Check if this is the target message (either matching the temp ID or the real ID if already updated)
          if (target && (target.id === tempAssistantId || target.id === data.message_id)) {
            newMsgs[lastIdx] = {
              ...target,
              content: target.content + data.content,
              id: data.message_id // update to real ID
            }
          }
          return newMsgs
        })
      },
      (data) => {
        // Handle done event
        setIsLoading(false)
        setCancelStream(null)
        onMessageSent() // Refresh conversation list in sidebar
      },
      (err) => {
        console.error("Stream error:", err)
        setIsLoading(false)
        setCancelStream(null)
      }
    )

    setCancelStream(() => cancel)
  }

  const handleCancel = () => {
    if (cancelStream) {
      cancelStream()
      setCancelStream(null)
      setIsLoading(false)
      onMessageSent()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!activeConversationId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-surface-400">
        <svg className="w-16 h-16 mb-4 text-surface-800" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p>Select or create a conversation to start chatting</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex-shrink-0 px-6 py-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-medium text-surface-100">Conversation</h2>
            <p className="text-xs text-surface-700 mt-0.5">Model: GPT-4 (placeholder)</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-slow" />
              Connected
            </span>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Typing indicator */}
          {isLoading && messages.length > 0 && messages[messages.length-1].role === 'user' && (
            <div className="flex items-start gap-3 animate-fade-in">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-xs">IF</span>
              </div>
              <div className="glass-subtle px-4 py-3 rounded-2xl rounded-tl-md">
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-surface-700 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 rounded-full bg-surface-700 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 rounded-full bg-surface-700 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-6 py-4 border-t border-white/[0.06]">
        <div className="max-w-3xl mx-auto">
          {isLoading && (
            <div className="flex justify-center mb-3">
              <button 
                onClick={handleCancel}
                className="text-xs px-3 py-1 rounded-full border border-surface-700 text-surface-300 hover:bg-surface-800 hover:text-white transition-colors"
              >
                Cancel Stream
              </button>
            </div>
          )}
          <div className="glass flex items-end gap-3 p-3 glow-primary">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Send a message..."
              rows={1}
              className="flex-1 bg-transparent text-surface-100 placeholder-surface-700 text-sm resize-none outline-none max-h-[200px] py-1.5 px-1"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="p-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 disabled:bg-surface-800 disabled:text-surface-700 text-white transition-all duration-200 flex-shrink-0"
              aria-label="Send message"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
          <p className="text-center text-xs text-surface-700 mt-2">
            InferFlow may produce inaccurate information. Verify important details.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ChatView
