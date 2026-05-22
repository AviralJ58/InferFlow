import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import ChatView from './components/ChatView'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import { ApiClient, Conversation, LLMModel } from './api/client'

function ChatApp() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  
  // Model Selection State
  const [models, setModels] = useState<LLMModel[]>([])
  const [activeModelId, setActiveModelId] = useState<string>("gemini-2.5-flash")

  useEffect(() => {
    loadConversations()
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      const fetchedModels = await ApiClient.getModels()
      setModels(fetchedModels)
      if (fetchedModels.length > 0 && !fetchedModels.find(m => m.id === activeModelId)) {
        setActiveModelId(fetchedModels[0].id)
      }
    } catch (e) {
      console.error(e)
    }
  }

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
    setActiveConversationId('new')
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
          onCreateConversation={async (title) => {
            const conv = await ApiClient.createConversation(title)
            setConversations(prev => [conv, ...prev])
            setActiveConversationId(conv.id)
            return conv.id
          }}
          models={models}
          activeModelId={activeModelId}
          onModelChange={setActiveModelId}
        />
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatApp />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
