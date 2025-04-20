import axios from 'axios';

// Define base URL for the backend API
const API_URL = 'http://localhost:8000';

export interface ChatMessage {
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isLoading?: boolean;
}

interface RagResponse {
  answer: string;
  session_id: string;
  model: {
    value: string;
    name: string;
  }
}

// Store the session ID for maintaining conversation context
let sessionId: string | null = null;
let selectedModel = 'llama-3.1-8b-instant'; // Default model

export const chatService = {
  // Send a message to the chatbot API
  async sendMessage(message: string): Promise<ChatMessage> {
    try {
      if (!sessionId) {
        // Generate a random session ID if none exists
        sessionId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
      }

      const response = await axios.post<RagResponse>(`${API_URL}/chat`, {
        question: message,
        session_id: sessionId,
        model: selectedModel
      });
      
      return {
        text: response.data.answer,
        sender: 'bot',
        timestamp: new Date()
      };
    } catch (error) {
      console.error('Error sending message:', error);
      // Return an error message if the API call fails
      return {
        text: "I'm sorry, I encountered an error processing your request. Please try again later.",
        sender: 'bot',
        timestamp: new Date()
      };
    }
  },

  // Get chat history
  async getChatHistory(): Promise<ChatMessage[]> {
    // We'll maintain chat history in the frontend for now
    // In a full implementation, we would fetch this from the backend
    return [
      {
        text: 'Welcome to Manipal University Jaipur! How can I help you today?',
        sender: 'bot',
        timestamp: new Date()
      }
    ];
  },

  // Set the model to use for RAG
  setModel(model: string): void {
    selectedModel = model;
  },

  // Get the current session ID
  getSessionId(): string | null {
    return sessionId;
  },

  // Reset the session ID to start a new conversation
  resetSession(): void {
    sessionId = null;
  }
};

export default chatService; 