export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface StreamEventData {
  message_id: string;
  conversation_id: string;
  content: string;
  is_done: boolean;
}

const API_BASE = '/api/v1';

export const ApiClient = {
  // --- Conversations ---
  
  async getConversations(): Promise<Conversation[]> {
    const res = await fetch(`${API_BASE}/conversations`);
    if (!res.ok) throw new Error('Failed to fetch conversations');
    return res.json();
  },

  async getConversation(id: string): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/conversations/${id}`);
    if (!res.ok) throw new Error('Failed to fetch conversation');
    return res.json();
  },

  async createConversation(title?: string): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error('Failed to create conversation');
    return res.json();
  },

  async deleteConversation(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete conversation');
  },

  // --- Chat Streaming ---

  streamChat(
    conversationId: string, 
    message: string, 
    onToken: (data: StreamEventData) => void,
    onDone: (data: StreamEventData) => void,
    onError: (err: any) => void
  ): () => void {
    const controller = new AbortController();
    
    // We use fetch instead of EventSource so we can send a POST request with a JSON body
    fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: message
      }),
      signal: controller.signal
    }).then(async (response) => {
      if (!response.ok || !response.body) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          
          // Keep the last partial line in the buffer
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              try {
                const data: StreamEventData = JSON.parse(dataStr);
                if (data.is_done) {
                  onDone(data);
                } else {
                  onToken(data);
                }
              } catch (e) {
                console.error('Error parsing SSE data', e, dataStr);
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          onError(err);
        }
      }
    }).catch(err => {
      if (err.name !== 'AbortError') {
        onError(err);
      }
    });

    // Return a cancel function
    return () => controller.abort();
  }
};
