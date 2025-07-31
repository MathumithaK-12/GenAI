import React, { useState, useEffect, useRef } from 'react';
import './ChatScreen.css';
import { FaPaperPlane } from 'react-icons/fa';

const ChatScreen = ({ onEndChat, darkMode }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [showWelcome, setShowWelcome] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');

    if (showWelcome) setShowWelcome(false);

    // Simulate assistant typing
    setIsTyping(true);
    const typingPlaceholder = { sender: 'assistant', text: 'typing...', isTyping: true };
    setMessages(prev => [...prev, typingPlaceholder]);

    setTimeout(() => {
      setMessages(prev => [
        ...prev.slice(0, -1), // remove 'typing...'
        {
          sender: 'assistant',
          text: "Thanks! Let me check that for you.",
          delayed: true,
        },
      ]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyPress = e => {
    if (e.key === 'Enter') handleSend();
  };

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping]);

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
            className={`chat-bubble ${msg.sender === 'user' ? 'user-msg' : 'assistant-msg'} ${
              msg.delayed ? 'delayed-appear' : ''
            }`}
            style={{ animationDelay: msg.delayed ? `${idx * 0.1}s` : '0s' }}
          >
            {msg.isTyping ? (
              <span className="typing-dots">
                <span>.</span><span>.</span><span>.</span>
              </span>
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
        />
        <button className="send-btn" onClick={handleSend}>
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
