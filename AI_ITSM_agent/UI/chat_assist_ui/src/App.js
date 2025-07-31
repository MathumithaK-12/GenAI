import React, { useState } from 'react';
import './App.css';
import ChatScreen from './ChatScreen';
import { FaMoon, FaSun } from 'react-icons/fa';

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(prev => !prev);
  };

  const handleStartChat = () => {
    setChatStarted(true);
  };

  const handleEndChat = () => {
    setChatStarted(false);
  };

  return (
    <div className={`app-container ${darkMode ? 'dark' : ''}`}>
      <header className={`app-header ${darkMode ? 'dark' : ''}`}>
        <h1>Chat Assistant</h1>
        <button className="dark-toggle" onClick={toggleDarkMode}>
          {darkMode ? <FaSun /> : <FaMoon />}
        </button>
      </header>

      {!chatStarted ? (
        <main className="main-content">
          <div className="prompt-text">How can I help you today?</div>
          <div className="button-group">
            <button className="rounded-button" onClick={handleStartChat}>Pack ITSM Assist</button>
            <button className="rounded-button" onClick={handleStartChat}>Health Check Assist</button>
            <button className="rounded-button" onClick={handleStartChat}>HSM Code Assist</button>
            <button className="rounded-button" onClick={handleStartChat}>Location Assist</button>
            <button className="rounded-button" onClick={handleStartChat}>User Creation Assist</button>
            <button className="rounded-button" onClick={handleStartChat}>Design Assist</button>
          </div>
        </main>
      ) : (
        <div className="chat-wrapper">
          <ChatScreen onEndChat={handleEndChat} darkMode={darkMode}/>
        </div>
      )}
    </div>
  );
}

export default App;
