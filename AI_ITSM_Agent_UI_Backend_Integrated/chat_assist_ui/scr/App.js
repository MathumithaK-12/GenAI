import React, { useState } from 'react';
import './App.css';
import ChatScreen from './ChatScreen';
import { FaMoon, FaSun, FaPaperPlane } from 'react-icons/fa';


const API_URL = process.env.REACT_APP_API_URL;

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);
  const [selectedAssist, setSelectedAssist] = useState(null);
  const [prechatInput, setPrechatInput] = useState('');

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
    setPrechatInput("");
  };

  const handlePrechatSubmit = async () => {
  if (!prechatInput.trim()) return;

  try {
    const response = await fetch(`${API_URL}/classify_intent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: prechatInput }),
    });

    const data = await response.json();
    const type = data.agent_type;

    // ✅ Check for "unknown" and handle it gracefully
    if (type && type !== "unknown") {
      setSelectedAssist(type);
      setChatStarted(true);
    } else {
      alert("Sorry, we couldn't understand your issue. Could you please rephrase it?");
      setPrechatInput(""); 
    }
  } catch (error) {
    console.error("Error classifying intent:", error);
    alert("Something went wrong while classifying the issue. Please try again.");
  }
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
          <div className="prechat-input-wrapper">
            <input
              type="text"
              placeholder="Describe your issue..."
              value={prechatInput}
              onChange={(e) => setPrechatInput(e.target.value)}
              className="prechat-input"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault(); // prevent form submission if inside a form
                  handlePrechatSubmit();
                }
              }}
            />
            <button className="send-button" onClick={handlePrechatSubmit}>
              <FaPaperPlane />
            </button>
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
