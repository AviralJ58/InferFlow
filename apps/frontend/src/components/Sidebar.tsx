interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

/**
 * Sidebar component — conversation list and navigation.
 *
 * Current: placeholder UI.
 * Future: list conversations, new chat button, settings.
 */
function Sidebar({ isOpen, onToggle }: SidebarProps) {
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
        <button className="w-full py-2.5 px-4 rounded-xl border border-white/10 hover:bg-white/5 transition-all duration-200 text-sm text-surface-200 hover:text-white flex items-center gap-2 mb-4">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Conversation
        </button>

        {/* Conversation List Placeholder */}
        <div className="flex-1 overflow-y-auto space-y-1">
          <p className="text-xs text-surface-700 uppercase tracking-wider px-2 mb-2">Recent</p>
          {['Welcome chat', 'Architecture discussion', 'API design review'].map((title, i) => (
            <button
              key={i}
              className="w-full text-left py-2.5 px-3 rounded-lg text-sm text-surface-200 hover:bg-white/5 transition-colors truncate"
            >
              {title}
            </button>
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
              <p className="text-xs text-surface-700">Free plan</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
