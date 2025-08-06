import React, { useState, useEffect, useRef } from 'react';
import './ChatScreen.css';
import { FaPaperPlane } from 'react-icons/fa';

const API_URL = process.env.REACT_APP_API_URL;

const ChatScreen = ({ onEndChat, darkMode, assistType, autoInitiate }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [showWelcome, setShowWelcome] = useState(true);
  const [sessionId] = useState(() => Date.now().toString());
  const [isTyping, setIsTyping] = useState(false); // ⬅️ NEW STATE
  const messagesEndRef = useRef(null);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return; // ⬅️ BLOCK MULTIPLE SENDS

    const userMsg = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');

    if (showWelcome) setShowWelcome(false);

    if (assistType !== 'itsm') {
      const unsupportedMsg = {
        sender: 'assistant',
        text: `Sorry, ${assistType} assistant is not yet supported.`,
      };
      setMessages(prev => [...prev, unsupportedMsg]);
      return;
    }

    const typingPlaceholder = {
      id: Date.now(),
      sender: 'assistant',
      text: '',
      isTyping: true,
    };
    setMessages(prev => [...prev, typingPlaceholder]);
    setIsTyping(true); // ⬅️ START TYPING STATE

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
        }),
      });

      const data = await res.json();
      const reply = data.response || 'Sorry, no response received.';

      const characters = reply.split('');
      let currentText = '';
      const msgId = typingPlaceholder.id;

      let i = 0;
      const typeNextChar = () => {
        if (i < characters.length) {
          currentText += characters[i];
          i++;
          setMessages(prev =>
            prev.map(msg =>
              msg.id === msgId ? { ...msg, isTyping: false, text: currentText } : msg
            )
          );
          setTimeout(typeNextChar, 20);
        } else {
          setIsTyping(false); // ⬅️ DONE TYPING
        }
      };

      setTimeout(typeNextChar, 300);
    } catch (err) {
      setIsTyping(false); // ⬅️ FAILSAFE
      setMessages(prev => [
        ...prev.filter(m => !m.isTyping),
        { sender: 'assistant', text: 'Failed to connect to backend.' },
      ]);
    }
  };

  const handleKeyPress = e => {
    if (e.key === 'Enter') handleSend();
  };

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    if (autoInitiate && assistType) {
      const getLLMIntro = async () => {
        try {
          const response = await fetch(`${API_URL}/generate_intro`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agent_type: assistType })
          });
          const data = await response.json();
          const introMessage = data.intro_message || "Hello, how can I help you today?";
          setMessages([{ sender: "bot", text: introMessage }]); // Inject LLM-generated intro
        } catch (error) {
          console.error("Failed to fetch LLM intro:", error);
          setMessages([{ sender: "bot", text: "Hi, I’m your assistant. How can I help you today?" }]);
        }
      };
  
      getLLMIntro();
    }
  }, [autoInitiate, assistType]); 
  
  return (
    <div className={`chat-screen ${darkMode ? 'dark' : ''}`}>
      {showWelcome && (
        <div className="welcome-banner">
          <h2>Welcome to Chat Mode</h2>
          <p>This is your smart assistant. Start typing your issue below.</p>
        </div>
      )}

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-bubble ${msg.sender === 'user' ? 'user-msg' : 'assistant-msg'}`}
          >
            {msg.isTyping ? (
              <span className="typing-dots"><span></span><span></span><span></span></span>
            ) : (
              msg.text
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <input
          className="chat-input"
          type="text"
          placeholder="Type something..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isTyping}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={isTyping}
          title={isTyping ? "Assistant is typing..." : "Send message"}
        >
          <FaPaperPlane />
        </button>
      </div>

      <button className="end-chat-btn" onClick={onEndChat}>
        End Chat
      </button>
    </div>
  );
};

export default ChatScreen;
