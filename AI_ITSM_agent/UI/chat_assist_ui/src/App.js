import React, { useState } from 'react';
import './App.css';
import ChatScreen from './ChatScreen';
import { FaSun, FaMoon } from 'react-icons/fa';

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);

  const handleStartChat = () => {
    setChatStarted(true);
  };

  const handleEndChat = () => {
    setChatStarted(false);
  };

  return (
    <div className={`app-container ${darkMode ? 'dark' : ''}`}>
      <div className="app-header">
        <h1>Chat Assistant</h1>
        <button className="dark-toggle" onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? <FaSun /> : <FaMoon />}
        </button>
      </div>

      {chatStarted ? (
        <ChatScreen onEndChat={handleEndChat} />
      ) : (
        <div className="main-content">
          <div className="prompt-text">How can I help you today?</div>
          <div className="button-group">
            <button className="rounded-button" onClick={handleStartChat}>Packing ITSM Assist</button>
            <button className="rounded-button" onClick={handleStartChat}>HSN code Assist</button>
            <button className="rounded-button" onClick={handleStartChat}>Location Creation Assist</button>
            <button className="rounded-button" onClick={handleStartChat}>User Creation Assist</button>
            <button className="rounded-button" onClick={handleStartChat}>WMS Design Assist</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
