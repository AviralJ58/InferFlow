import { useState, useEffect } from 'react'
import ChatView from './components/ChatView'
import Sidebar from './components/Sidebar'
import { ApiClient, Conversation } from './api/client'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const convs = await ApiClient.getConversations()
      setConversations(convs)
    } catch (e) {
      console.error(e)
    }
  }

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id)
  }

  const handleCreateConversation = async () => {
    try {
      const conv = await ApiClient.createConversation("New Conversation")
      setConversations([conv, ...conversations])
      setActiveConversationId(conv.id)
    } catch (e) {
      console.error(e)
    }
  }

  const handleDeleteConversation = async (id: string) => {
    try {
      await ApiClient.deleteConversation(id)
      setConversations(conversations.filter(c => c.id !== id))
      if (activeConversationId === id) {
        setActiveConversationId(null)
      }
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar 
        isOpen={sidebarOpen} 
        onToggle={() => setSidebarOpen(!sidebarOpen)} 
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelect={handleSelectConversation}
        onCreate={handleCreateConversation}
        onDelete={handleDeleteConversation}
      />
      <main className="flex-1 flex flex-col min-w-0">
        <ChatView 
          activeConversationId={activeConversationId} 
          onMessageSent={loadConversations} 
        />
      </main>
    </div>
  )
}

export default App
