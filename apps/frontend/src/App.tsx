import { useState } from 'react'
import ChatView from './components/ChatView'
import Sidebar from './components/Sidebar'

/**
 * Root application component.
 *
 * Current: minimal chat UI placeholder.
 * Future: add routing, auth context, conversation management.
 */
function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0">
        <ChatView />
      </main>
    </div>
  )
}

export default App
