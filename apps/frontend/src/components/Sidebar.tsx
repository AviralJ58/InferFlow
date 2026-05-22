import { Conversation } from '../api/client'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  conversations: Conversation[]
  activeConversationId: string | null
  onSelect: (id: string) => void
  onCreate: () => void
  onDelete: (id: string) => void
}

function Sidebar({ isOpen, onToggle, conversations, activeConversationId, onSelect, onCreate, onDelete }: SidebarProps) {
  return (
    <aside
      className={`${
        isOpen ? 'w-72' : 'w-0'
      } transition-all duration-300 ease-in-out overflow-hidden flex-shrink-0 border-r border-white/[0.06] bg-surface-950`}
    >
      <div className="flex flex-col h-full p-4 w-72">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <span className="text-white font-bold text-sm">IF</span>
            </div>
            <h1 className="text-lg font-semibold gradient-text">InferFlow</h1>
          </div>
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-surface-200"
            aria-label="Toggle sidebar"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* New Chat Button */}
        <button 
          onClick={onCreate}
          className="w-full py-2.5 px-4 rounded-xl border border-white/10 hover:bg-white/5 transition-all duration-200 text-sm text-surface-200 hover:text-white flex items-center gap-2 mb-4"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Conversation
        </button>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto space-y-1">
          <p className="text-xs text-surface-700 uppercase tracking-wider px-2 mb-2">Recent</p>
          {conversations.length === 0 && (
            <p className="text-xs text-surface-600 px-2">No conversations yet.</p>
          )}
          {conversations.map(conv => (
            <div 
              key={conv.id} 
              className={`group w-full flex items-center justify-between py-2 px-3 rounded-lg text-sm transition-colors ${
                activeConversationId === conv.id 
                  ? 'bg-primary-600/20 text-white border border-primary-500/20' 
                  : 'text-surface-200 hover:bg-white/5 border border-transparent'
              }`}
            >
              <button
                className="flex-1 text-left truncate pr-2"
                onClick={() => onSelect(conv.id)}
              >
                {conv.title}
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-surface-800 text-surface-400 hover:text-red-400 transition-all"
                title="Delete"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-white/[0.06]">
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
              <span className="text-white text-xs font-medium">U</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-surface-200 truncate">User</p>
              <p className="text-xs text-surface-700">Local Dev</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
