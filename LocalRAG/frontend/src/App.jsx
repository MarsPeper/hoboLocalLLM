import React, { useState } from 'react';
import Chat from './components/Chat';
import DocumentManager from './components/DocumentManager';
import Settings from './components/Settings';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-icon">🎛️</div>
          <div>
            <h1 className="app-title">LocalRAG</h1>
            <p className="app-subtitle">Private Local Knowledge</p>
          </div>
        </div>
        
        <nav className="nav-menu">
          <button
            onClick={() => setActiveTab('chat')}
            className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
          >
            <span className="nav-icon">💬</span>
            <span className="nav-text">RAG Chat</span>
          </button>
          
          <button
            onClick={() => setActiveTab('documents')}
            className={`nav-item ${activeTab === 'documents' ? 'active' : ''}`}
          >
            <span className="nav-icon">📂</span>
            <span className="nav-text">Document Library</span>
          </button>
          
          <button
            onClick={() => setActiveTab('settings')}
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
          >
            <span className="nav-icon">⚙️</span>
            <span className="nav-text">RAG Config</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="status-indicator">
            <span className="status-dot online"></span>
            <span className="status-text">Local API (Port 8000)</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="main-header">
          <h2>
            {activeTab === 'chat' && 'Semantic Search & Chat'}
            {activeTab === 'documents' && 'Document Ingestion Registry'}
            {activeTab === 'settings' && 'System Parameters & Configurations'}
          </h2>
          <div className="header-actions">
            <span className="badge">GGUF Inference</span>
            <span className="badge">Qdrant Client</span>
          </div>
        </header>

        <div className="content-viewport">
          {activeTab === 'chat' && <Chat />}
          {activeTab === 'documents' && <DocumentManager />}
          {activeTab === 'settings' && <Settings />}
        </div>
      </main>
    </div>
  );
}
