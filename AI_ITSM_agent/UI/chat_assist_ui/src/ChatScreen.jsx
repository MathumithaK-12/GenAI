import React, { useState, useEffect } from 'react';
import './ChatScreen.css';
import { FaPaperPlane } from 'react-icons/fa';

const ChatScreen = ({ onEndChat }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [showWelcome, setShowWelcome] = useState(true);

  const handleSend = () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { sender: 'user', text: input }];
    setMessages(newMessages);

    setTimeout(() => {
      setMessages(prev => [...prev, { sender: 'assistant', text: "Got it! I'm processing your request..." }]);
    }, 500);

    setInput('');
    if (showWelcome) {
      setShowWelcome(false);
    }
  };

  const handleKeyPress = e => {
    if (e.key === 'Enter') handleSend();
  };

  return (
    <div className="chat-screen">
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
            {msg.text}
          </div>
        ))}
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
