import * as React from 'react';
import { useState, useRef, useEffect } from 'react';
import chatService, { ChatMessage } from '../../services/chatService';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatBotProps {
  isOpen: boolean;
  isHovered: boolean;
  toggleChat: () => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}

const ChatBot: React.FC<ChatBotProps> = ({ 
  isOpen, 
  isHovered, 
  toggleChat, 
  onMouseEnter, 
  onMouseLeave 
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingSpeech, setIsProcessingSpeech] = useState(false);
  const [isButtonHovered, setIsButtonHovered] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastActivity, setLastActivity] = useState<number>(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const autoSubmitTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Silence detection effect
  useEffect(() => {
    if (isRecording && lastActivity > 0) {
      // Clear any existing silence timeout
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
      
      // Set a new silence detection timeout
      silenceTimeoutRef.current = setTimeout(() => {
        console.log("Stopping recording due to silence detection");
        if (isRecording) {
          stopRecording();
        }
      }, 5000); // 5 seconds of silence

      return () => {
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = null;
        }
      };
    }
  }, [isRecording, lastActivity]);

  // Initialize speech recognition
  useEffect(() => {
    const setupRecognition = () => {
      // Check if browser supports speech recognition
      const SpeechRecognitionAPI = window.SpeechRecognition || 
                                window.webkitSpeechRecognition;
      
      if (SpeechRecognitionAPI) {
        const recognition = new SpeechRecognitionAPI();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        // Handle speech recognition results
        recognition.onresult = (event) => {
          // Get the full transcript from all results
          const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join(' ');
          
          console.log("Speech recognized:", transcript);
          setInputMessage(transcript);
          
          // Update the last activity timestamp
          setLastActivity(Date.now());
          
          // Scroll input field to the end to show latest text
          setTimeout(() => {
            if (inputRef.current) {
              inputRef.current.scrollLeft = inputRef.current.scrollWidth;
            }
          }, 10);
        };

        // Handle when speech recognition ends
        recognition.onend = () => {
          console.log("Speech recognition ended");
          
          // Only handle if we were actually recording
          if (isRecording) {
            setIsRecording(false);
            setIsProcessingSpeech(true);
            
            // Cleanup any silence detection
            if (silenceTimeoutRef.current) {
              clearTimeout(silenceTimeoutRef.current);
              silenceTimeoutRef.current = null;
            }
            
            // Simulate processing time
            setTimeout(() => {
              setIsProcessingSpeech(false);
              
              // Set auto-submit timeout if there's meaningful input
              if (inputMessage && inputMessage.trim() !== '') {
                console.log("Setting auto-submit timeout");
                
                if (autoSubmitTimeoutRef.current) {
                  clearTimeout(autoSubmitTimeoutRef.current);
                }
                
                autoSubmitTimeoutRef.current = setTimeout(() => {
                  console.log("Auto-submitting message");
                  handleSubmit(new Event('submit') as unknown as React.FormEvent);
                }, 3000);
              }
            }, 1000);
          }
        };

        // Handle speech recognition errors
        recognition.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
          
          // Don't stop recording on no-speech errors
          if (event.error !== 'no-speech') {
            setIsRecording(false);
            setIsProcessingSpeech(false);
          }
        };

        recognitionRef.current = recognition;
      }
    };

    setupRecognition();

    return () => {
      // Clean up
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (error) {
          console.error("Error aborting speech recognition:", error);
        }
      }
      
      // Clear any timeouts
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
      if (autoSubmitTimeoutRef.current) {
        clearTimeout(autoSubmitTimeoutRef.current);
        autoSubmitTimeoutRef.current = null;
      }
    };
  }, []);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      // Load initial chat history
      chatService.getChatHistory().then(history => {
        setMessages(history);
      });
    }
  }, [messages.length]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputMessage(e.target.value);
    
    // Clear auto-submit timeout if user is manually typing
    if (autoSubmitTimeoutRef.current) {
      clearTimeout(autoSubmitTimeoutRef.current);
      autoSubmitTimeoutRef.current = null;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() === '' || isLoading) return;
    
    // Clear any pending auto-submit
    if (autoSubmitTimeoutRef.current) {
      clearTimeout(autoSubmitTimeoutRef.current);
      autoSubmitTimeoutRef.current = null;
    }

    // Add user message
    const userMessage: ChatMessage = {
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // Add loading message
    const loadingMessage: ChatMessage = {
      text: '',
      sender: 'bot',
      timestamp: new Date(),
      isLoading: true
    };
    
    setMessages(prev => [...prev, loadingMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    try {
      // Send message to API
      const botResponse = await chatService.sendMessage(userMessage.text);
      
      // Replace loading message with actual response
      setMessages(prev => [
        ...prev.slice(0, -1), // Remove loading message
        botResponse
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Replace loading message with error message
      setMessages(prev => [
        ...prev.slice(0, -1), // Remove loading message
        {
          text: "I'm sorry, I encountered an error processing your request. Please try again later.",
          sender: 'bot',
          timestamp: new Date()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseChat = () => {
    setIsClosing(true);
    // Wait for animation to complete before actually closing
    setTimeout(() => {
      setIsClosing(false);
      toggleChat();
    }, 400); // Match animation duration
  };

  const handleResetChat = () => {
    // Reset session and conversation
    chatService.resetSession();
    
    // Clear all messages except the welcome message
    setMessages([
      {
        text: 'Welcome to Manipal University Jaipur! How can I help you today?',
        sender: 'bot',
        timestamp: new Date()
      }
    ]);
  };

  const startRecording = () => {
    // Clear any pending auto-submit
    if (autoSubmitTimeoutRef.current) {
      clearTimeout(autoSubmitTimeoutRef.current);
      autoSubmitTimeoutRef.current = null;
    }
    
    // Clear any silence detection
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    
    if (!recognitionRef.current) {
      // If recognition not initialized, set it up again
      const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognitionAPI) {
        recognitionRef.current = new SpeechRecognitionAPI();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = 'en-US';
        
        // Set up event handlers
        recognitionRef.current.onresult = (event) => {
          const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join(' ');
          
          console.log("Speech recognized:", transcript);
          setInputMessage(transcript);
          setLastActivity(Date.now());
          
          // Scroll input field to the end
          setTimeout(() => {
            if (inputRef.current) {
              inputRef.current.scrollLeft = inputRef.current.scrollWidth;
            }
          }, 10);
        };
        
        recognitionRef.current.onend = () => {
          console.log("Speech recognition ended");
          if (isRecording) {
            setIsRecording(false);
            setIsProcessingSpeech(true);
            
            // Clear any silence detection
            if (silenceTimeoutRef.current) {
              clearTimeout(silenceTimeoutRef.current);
              silenceTimeoutRef.current = null;
            }
            
            setTimeout(() => {
              setIsProcessingSpeech(false);
              
              if (inputMessage && inputMessage.trim() !== '') {
                if (autoSubmitTimeoutRef.current) {
                  clearTimeout(autoSubmitTimeoutRef.current);
                }
                
                autoSubmitTimeoutRef.current = setTimeout(() => {
                  console.log("Auto-submitting message after processing");
                  handleSubmit(new Event('submit') as unknown as React.FormEvent);
                }, 3000);
              }
            }, 1000);
          }
        };
        
        recognitionRef.current.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
          if (event.error !== 'no-speech') {
            setIsRecording(false);
            setIsProcessingSpeech(false);
          }
        };
      }
    }
    
    // Try to start recording
    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
        setIsRecording(true);
        setLastActivity(Date.now());
        console.log("Started speech recognition");
      } catch (error) {
        console.error('Error starting speech recognition:', error);
        
        // Try to create a new instance and start again
        try {
          const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (SpeechRecognitionAPI) {
            // Create new instance
            recognitionRef.current = new SpeechRecognitionAPI();
            recognitionRef.current.continuous = true;
            recognitionRef.current.interimResults = true;
            recognitionRef.current.lang = 'en-US';
            
            // Set up handlers again
            recognitionRef.current.onresult = (event) => {
              const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join(' ');
              
              console.log("Speech recognized:", transcript);
              setInputMessage(transcript);
              setLastActivity(Date.now());
              
              // Scroll input field to the end
              setTimeout(() => {
                if (inputRef.current) {
                  inputRef.current.scrollLeft = inputRef.current.scrollWidth;
                }
              }, 10);
            };
            
            recognitionRef.current.onend = () => {
              console.log("Speech recognition ended");
              if (isRecording) {
                setIsRecording(false);
                setIsProcessingSpeech(true);
                
                // Clear any silence detection
                if (silenceTimeoutRef.current) {
                  clearTimeout(silenceTimeoutRef.current);
                  silenceTimeoutRef.current = null;
                }
                
                setTimeout(() => {
                  setIsProcessingSpeech(false);
                  
                  if (inputMessage && inputMessage.trim() !== '') {
                    if (autoSubmitTimeoutRef.current) {
                      clearTimeout(autoSubmitTimeoutRef.current);
                    }
                    
                    autoSubmitTimeoutRef.current = setTimeout(() => {
                      console.log("Auto-submitting message after retry");
                      handleSubmit(new Event('submit') as unknown as React.FormEvent);
                    }, 3000);
                  }
                }, 1000);
              }
            };
            
            recognitionRef.current.onerror = (event: any) => {
              console.error('Speech recognition error:', event.error);
              if (event.error !== 'no-speech') {
                setIsRecording(false);
                setIsProcessingSpeech(false);
              }
            };
            
            // Try to start the new instance
            recognitionRef.current.start();
            setIsRecording(true);
            setLastActivity(Date.now());
            console.log("Started speech recognition after retry");
          }
        } catch (retryError) {
          console.error('Error on retry speech recognition:', retryError);
          alert('Speech recognition failed to start. Please try again or type your message.');
          setIsRecording(false);
        }
      }
    } else {
      alert('Speech recognition is not supported in your browser.');
    }
  };

  const stopRecording = () => {
    console.log("Manual stop recording called");
    
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
        console.log("Stopped speech recognition");
      } catch (error) {
        console.error('Error stopping speech recognition:', error);
      }
    }
    
    setIsRecording(false);
    
    // Clear any silence detection
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    
    // Show processing state 
    setIsProcessingSpeech(true);
    
    // Simulate processing time
    setTimeout(() => {
      setIsProcessingSpeech(false);
      
      // Set auto-submit timeout if there's input
      if (inputMessage && inputMessage.trim() !== '') {
        console.log("Setting auto-submit timeout after stopping");
        
        if (autoSubmitTimeoutRef.current) {
          clearTimeout(autoSubmitTimeoutRef.current);
        }
        
        autoSubmitTimeoutRef.current = setTimeout(() => {
          console.log("Auto-submitting message after stop");
          handleSubmit(new Event('submit') as unknown as React.FormEvent);
        }, 3000);
      }
    }, 1000);
  };

  const handleVoiceInput = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Loading dots animation component
  const LoadingDots = () => (
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
      <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
      <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
    </div>
  );

  return (
    <div 
      className="fixed bottom-6 right-6 z-50 flex items-center"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Always visible label, positioned to the left */}
      {!isOpen && (
        <div className="bg-white p-3 rounded-lg shadow-lg text-sm whitespace-nowrap mr-3 font-poppins">
          Hey! I am your student assistant.
        </div>
      )}
      
      {/* Always show the chatbot icon */}
      <button 
        onClick={toggleChat}
        onMouseEnter={() => setIsButtonHovered(true)}
        onMouseLeave={() => setIsButtonHovered(false)}
        className={`h-14 w-14 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 bg-orange-500 hover:bg-orange-600`}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>

      {isOpen && (
        <div 
          className={`fixed bottom-24 right-6 w-[500px] h-[600px] bg-white rounded-xl shadow-2xl flex flex-col overflow-hidden z-40 font-poppins origin-bottom-right ${
            isClosing ? 'animate-popdown' : 'animate-popup'
          }`}
        >
          {/* Chat header with minimize and restart buttons */}
          <div className="bg-orange-500 text-white p-4 font-bold flex justify-between items-center">
            <span>Student Assistance Chatbot</span>
            <div className="flex items-center space-x-2">
              {/* Restart conversation button */}
              <button 
                onClick={handleResetChat}
                className="h-8 w-8 rounded-full flex items-center justify-center hover:bg-orange-600 transition-colors"
                title="Restart conversation"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              
              {/* Minimize button */}
              <button 
                onClick={handleCloseChat}
                className="h-8 w-8 rounded-full flex items-center justify-center hover:bg-orange-600 transition-colors"
                title="Minimize chat"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages container */}
          <div className="flex-1 p-4 overflow-y-auto">
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`mb-4 flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.sender === 'bot' && (
                  <div className="h-8 w-8 rounded-full bg-orange-500 flex items-center justify-center mr-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                  </div>
                )}
                <div 
                  className={`max-w-[70%] p-3 rounded-lg ${
                    message.sender === 'user' 
                      ? 'bg-blue-500 text-white rounded-br-none' 
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                  } ${message.isLoading ? 'flex items-center justify-center min-h-[40px]' : ''}`}
                >
                  {message.isLoading ? (
                    <LoadingDots />
                  ) : message.sender === 'bot' ? (
                    // Render bot messages with markdown
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
                    </div>
                  ) : (
                    // Render user messages as plain text
                    message.text
                  )}
                </div>
                {message.sender === 'user' && (
                  <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center ml-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} /> {/* Auto-scroll anchor */}
          </div>

          {/* Input area */}
          <form onSubmit={handleSubmit} className="p-4 bg-gray-50 flex items-center">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={handleInputChange}
              placeholder="Ask me anything..."
              className="flex-1 border border-gray-300 rounded-l-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-orange-500 overflow-x-auto whitespace-nowrap"
              disabled={isLoading}
              style={{ scrollbarWidth: 'none' }} // Hide scrollbar for Firefox
            />
            <button
              type="button"
              onClick={handleVoiceInput}
              disabled={isProcessingSpeech || isLoading}
              className={`p-2 ${
                isRecording 
                  ? 'bg-red-500 text-white' 
                  : isProcessingSpeech 
                    ? 'bg-yellow-500 text-white' 
                    : isLoading
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-gray-200 hover:bg-gray-300'
              } transition-colors`}
              title={isRecording ? "Stop recording" : isProcessingSpeech ? "Processing speech..." : "Start voice input"}
            >
              {isRecording ? (
                // Recording icon (stop)
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                </svg>
              ) : isProcessingSpeech ? (
                // Processing icon (spinner)
                <svg className="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                // Microphone icon (start)
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>
            <button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              className={`${
                !inputMessage.trim() || isLoading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-orange-500 hover:bg-orange-600'
              } text-white p-2 rounded-r-full`}
            >
              {isLoading ? (
                // Loading icon
                <svg className="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                // Send icon
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default ChatBot; 