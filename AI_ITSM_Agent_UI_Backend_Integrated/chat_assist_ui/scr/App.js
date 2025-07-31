import React, { useState } from 'react';
import './App.css';
import ChatScreen from './ChatScreen';
import { FaMoon, FaSun } from 'react-icons/fa';

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);
  const [selectedAssist, setSelectedAssist] = useState(null);

  const toggleDarkMode = () => {
    setDarkMode(prev => !prev);
  };

  const handleStartChat = (type) => {
    setSelectedAssist(type);
    setChatStarted(true);
  };

  const handleEndChat = () => {
    setChatStarted(false);
    setSelectedAssist(null);
  };

  return (
    <div className={`app-container ${darkMode ? 'dark' : ''}`}>
      <header className={`app-header ${darkMode ? 'dark' : ''}`}>
        <h1>Chat Assistant</h1>
        <button className={`dark-toggle ${darkMode ? 'rotate-left' : 'rotate-right'}`} onClick={toggleDarkMode}>
          {darkMode ? <FaSun /> : <FaMoon />}
        </button>
      </header>

      {!chatStarted ? (
        <main className="main-content">
          <div className="prompt-text">How can I help you today?</div>
          <div className="button-group">
            <button className="rounded-button" onClick={() => handleStartChat('itsm')}>Pack ITSM Assist</button>
            <button className="rounded-button" onClick={() => handleStartChat('health')}>Health Check Assist</button>
            <button className="rounded-button" onClick={() => handleStartChat('hsm')}>HSM Code Assist</button>
            <button className="rounded-button" onClick={() => handleStartChat('location')}>Location Assist</button>
            <button className="rounded-button" onClick={() => handleStartChat('user')}>User Creation Assist</button>
            <button className="rounded-button" onClick={() => handleStartChat('design')}>Design Assist</button>
          </div>
        </main>
      ) : (
        <div className="chat-wrapper">
          <ChatScreen onEndChat={handleEndChat} darkMode={darkMode} assistType={selectedAssist} />
        </div>
      )}
    </div>
  );
}

export default App;
