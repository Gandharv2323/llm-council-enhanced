/**
 * API client for the LLM Council backend.
 * Includes demo mode fallback when backend is unavailable.
 */

// In production, use relative URLs (same origin); in dev, use localhost
const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8001';

// Demo mode storage (localStorage fallback)
const DEMO_STORAGE_KEY = 'llm_council_demo_conversations';

function getDemoConversations() {
  const stored = localStorage.getItem(DEMO_STORAGE_KEY);
  return stored ? JSON.parse(stored) : [];
}

function saveDemoConversations(conversations) {
  localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(conversations));
}

function generateId() {
  return crypto.randomUUID ? crypto.randomUUID() : 'demo-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

// Check if we're in demo mode (backend unavailable)
let isDemoMode = false;

async function checkDemoMode() {
  try {
    const response = await fetch(`${API_BASE}/`, { method: 'GET', signal: AbortSignal.timeout(2000) });
    isDemoMode = !response.ok;
  } catch {
    isDemoMode = true;
  }
  if (isDemoMode) {
    console.log('🎮 Running in DEMO MODE (backend unavailable)');
  }
  return isDemoMode;
}

// Initialize demo mode check
checkDemoMode();

export const api = {
  /**
   * List all conversations.
   */
  async listConversations() {
    if (isDemoMode) {
      return getDemoConversations().map(c => ({
        id: c.id,
        created_at: c.created_at,
        title: c.title,
        message_count: c.messages.length
      }));
    }

    try {
      const response = await fetch(`${API_BASE}/api/conversations`);
      if (!response.ok) {
        throw new Error('Failed to list conversations');
      }
      return response.json();
    } catch (e) {
      // Fallback to demo mode
      isDemoMode = true;
      return this.listConversations();
    }
  },

  /**
   * Create a new conversation.
   */
  async createConversation() {
    if (isDemoMode) {
      const conversations = getDemoConversations();
      const newConv = {
        id: generateId(),
        created_at: new Date().toISOString(),
        title: 'New Conversation',
        messages: []
      };
      conversations.unshift(newConv);
      saveDemoConversations(conversations);
      return newConv;
    }

    try {
      const response = await fetch(`${API_BASE}/api/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });
      if (!response.ok) {
        throw new Error('Failed to create conversation');
      }
      return response.json();
    } catch (e) {
      // Fallback to demo mode
      isDemoMode = true;
      return this.createConversation();
    }
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId) {
    if (isDemoMode) {
      const conversations = getDemoConversations();
      const conv = conversations.find(c => c.id === conversationId);
      if (!conv) {
        throw new Error('Conversation not found');
      }
      return conv;
    }

    try {
      const response = await fetch(
        `${API_BASE}/api/conversations/${conversationId}`
      );
      if (!response.ok) {
        throw new Error('Failed to get conversation');
      }
      return response.json();
    } catch (e) {
      isDemoMode = true;
      return this.getConversation(conversationId);
    }
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    return response.json();
  },

  /**
   * Send a message and receive streaming updates.
   * @param {string} conversationId - The conversation ID
   * @param {string} content - The message content
   * @param {function} onEvent - Callback function for each event: (eventType, data) => void
   * @returns {Promise<void>}
   */
  async sendMessageStream(conversationId, content, onEvent) {
    if (isDemoMode) {
      // Demo mode: simulate streaming response
      const conversations = getDemoConversations();
      const conv = conversations.find(c => c.id === conversationId);
      if (conv) {
        // Update title if first message
        if (conv.messages.length === 0) {
          conv.title = content.substring(0, 50) + (content.length > 50 ? '...' : '');
        }

        // Add user message
        conv.messages.push({ role: 'user', content });
        saveDemoConversations(conversations);

        // Simulate streaming with demo responses
        await new Promise(r => setTimeout(r, 500));
        onEvent('stage1_start', {});

        await new Promise(r => setTimeout(r, 1000));
        const demoStage1 = [
          { model: 'Model A', response: '🎮 Demo Mode: This is a simulated response. Start the backend for real AI responses!' },
          { model: 'Model B', response: '🎮 Demo Mode: The shader spheres look amazing! The backend is needed for actual LLM council functionality.' }
        ];
        onEvent('stage1_complete', { data: demoStage1 });

        await new Promise(r => setTimeout(r, 500));
        onEvent('stage2_start', {});

        await new Promise(r => setTimeout(r, 800));
        onEvent('stage2_complete', { data: [], metadata: {} });

        await new Promise(r => setTimeout(r, 500));
        onEvent('stage3_start', {});

        await new Promise(r => setTimeout(r, 800));
        onEvent('stage3_complete', { data: '🎮 **Demo Mode Active**\n\nThe beautiful shader spheres are working! To get real AI council responses, start the backend server.' });

        onEvent('title_complete', { data: { title: conv.title } });
        onEvent('complete', {});
      }
      return;
    }

    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const event = JSON.parse(data);
            onEvent(event.type, event);
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        }
      }
    }
  },

  /**
   * Get available models (demo fallback).
   */
  async getModels() {
    if (isDemoMode) {
      return [
        { id: 'demo-model-1', name: 'Demo Model A' },
        { id: 'demo-model-2', name: 'Demo Model B' }
      ];
    }

    try {
      const response = await fetch(`${API_BASE}/api/models`);
      if (!response.ok) throw new Error();
      const data = await response.json();
      return data.council_models?.map(id => ({ id, name: id })) || [];
    } catch {
      isDemoMode = true;
      return this.getModels();
    }
  }
};

