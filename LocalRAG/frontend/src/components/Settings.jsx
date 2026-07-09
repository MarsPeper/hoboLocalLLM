import React, { useState, useEffect } from 'react';

export default function Settings() {
  const [config, setConfig] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null); // { state: 'success'|'error'|'saving', message: '' }
  const [isLoading, setIsLoading] = useState(true);
  const [renderError, setRenderError] = useState(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setIsLoading(true);
    setRenderError(null);
    try {
      const response = await fetch('http://localhost:8000/api/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      } else {
        throw new Error(`Failed to load configuration. Server returned status ${response.status}`);
      }
    } catch (err) {
      console.error("Fetch config error:", err);
      setSaveStatus({ state: 'error', message: 'Could not fetch config from FastAPI backend. Make sure the backend server is running.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (category, field, value) => {
    setConfig((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        [category]: {
          ...(prev[category] || {}),
          [field]: value,
        },
      };
    });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaveStatus({ state: 'saving', message: 'Saving configuration and hot-reloading pipeline...' });

    try {
      const response = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      const result = await response.json();
      if (response.ok) {
        setSaveStatus({ state: 'success', message: 'Configuration saved and pipeline components reloaded.' });
        setTimeout(() => setSaveStatus(null), 3000);
      } else {
        throw new Error(result.detail || 'Failed to save configuration');
      }
    } catch (err) {
      console.error("Save config error:", err);
      setSaveStatus({ state: 'error', message: err.message || 'Error occurred while saving configurations.' });
    }
  };

  if (isLoading) {
    return (
      <div className="loading-spinner-wrapper" style={{ padding: '40px', textAlign: 'center', color: '#fff' }}>
        <div className="spinner"></div>
        <p style={{ marginTop: '15px' }}>Fetching active settings from backend...</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="settings-error-state" style={{ padding: '40px', textAlign: 'center', color: '#fff', border: '1px solid #333', borderRadius: '12px', background: '#111', maxWidth: '600px', margin: '40px auto' }}>
        <p style={{ fontSize: '16px', color: '#ff4d4d' }}>⚠️ Cannot connect to backend configuration endpoint.</p>
        <p style={{ fontSize: '13px', color: '#aaa', margin: '15px 0' }}>Please ensure the FastAPI backend is running locally on port 8000.</p>
        <button onClick={fetchConfig} className="retry-btn" style={{ padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Retry Connection</button>
      </div>
    );
  }

  // Wrap the render block in a try-catch to prevent blank screens if the API JSON has missing/malformed objects
  try {
    return (
      <div className="settings-container">
        <form onSubmit={handleSave}>
          <div className="settings-grid">
            
            {/* Section 1: RAG Settings */}
            <div className="settings-card">
              <h3>RAG Chunking & Retrieval Settings</h3>
              <p className="card-desc">Modify document partitioning logic and advanced retrieval pipelines.</p>
              
              <div className="form-group-row">
                <div className="form-group">
                  <label>Chunk Size (Characters)</label>
                  <input
                    type="number"
                    value={config?.rag?.chunk_size ?? 500}
                    onChange={(e) => handleInputChange('rag', 'chunk_size', parseInt(e.target.value) || 500)}
                    min="100"
                    max="5000"
                  />
                </div>

                <div className="form-group">
                  <label>Chunk Overlap (Characters)</label>
                  <input
                    type="number"
                    value={config?.rag?.chunk_overlap ?? 50}
                    onChange={(e) => handleInputChange('rag', 'chunk_overlap', parseInt(e.target.value) || 50)}
                    min="0"
                    max="1000"
                  />
                </div>
              </div>

              <div className="form-group toggle-row" style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '15px 0' }}>
                <input
                  type="checkbox"
                  id="use_hybrid_search"
                  checked={config?.rag?.use_hybrid_search ?? true}
                  onChange={(e) => handleInputChange('rag', 'use_hybrid_search', e.target.checked)}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
                <label htmlFor="use_hybrid_search" style={{ cursor: 'pointer', fontWeight: 'bold' }}>Enable Hybrid Search (Dense + Sparse/BM25)</label>
              </div>

              <div className="form-group toggle-row" style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '15px 0' }}>
                <input
                  type="checkbox"
                  id="use_reranker"
                  checked={config?.rag?.use_reranker ?? true}
                  onChange={(e) => handleInputChange('rag', 'use_reranker', e.target.checked)}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
                <label htmlFor="use_reranker" style={{ cursor: 'pointer', fontWeight: 'bold' }}>Enable FlashRank Reranker</label>
              </div>

              {config?.rag?.use_reranker && (
                <div className="reranker-subsettings" style={{ borderLeft: '3px solid var(--accent-glow, #3b82f6)', paddingLeft: '15px', marginTop: '10px' }}>
                  <div className="form-group">
                    <label>Reranker Model</label>
                    <input
                      type="text"
                      value={config?.rag?.reranker_model || 'ms-marco-MiniLM-L-12-v2'}
                      onChange={(e) => handleInputChange('rag', 'reranker_model', e.target.value)}
                    />
                  </div>

                  <div className="form-group-row">
                    <div className="form-group">
                      <label>Rerank Limit (Final Top K)</label>
                      <input
                        type="number"
                        value={config?.rag?.top_k ?? 4}
                        onChange={(e) => handleInputChange('rag', 'top_k', parseInt(e.target.value) || 4)}
                        min="1"
                        max="20"
                      />
                      <span className="input-hint">Chunks passed to LLM.</span>
                    </div>

                    <div className="form-group">
                      <label>Base Retrieve Limit (Pre-Rerank K)</label>
                      <input
                        type="number"
                        value={config?.rag?.base_retrieve_k || 12}
                        onChange={(e) => handleInputChange('rag', 'base_retrieve_k', parseInt(e.target.value) || 12)}
                        min="2"
                        max="50"
                      />
                      <span className="input-hint">Chunks evaluated by reranker.</span>
                    </div>
                  </div>
                </div>
              )}

              {!config?.rag?.use_reranker && (
                <div className="form-group">
                  <label>Retrieval Limit (Top K Chunks)</label>
                  <input
                    type="number"
                    value={config?.rag?.top_k ?? 4}
                    onChange={(e) => handleInputChange('rag', 'top_k', parseInt(e.target.value) || 4)}
                    min="1"
                    max="20"
                  />
                  <span className="input-hint">Number of context chunks injected into prompt.</span>
                </div>
              )}
            </div>

            {/* Section 2: LLM Inference Settings */}
            <div className="settings-card">
              <h3>Local LLM Settings</h3>
              <p className="card-desc">Configure connections to local llama-server or other OpenAI-compatible endpoints.</p>
              
              <div className="form-group">
                <label>LLM API Server Base URL</label>
                <input
                  type="text"
                  value={config?.llm?.api_url ?? ''}
                  onChange={(e) => handleInputChange('llm', 'api_url', e.target.value)}
                />
                <span className="input-hint">Defaults to llama-server: http://localhost:8080/v1</span>
              </div>

              <div className="form-group">
                <label>LLM Model Name ID</label>
                <input
                  type="text"
                  value={config?.llm?.model_name ?? ''}
                  onChange={(e) => handleInputChange('llm', 'model_name', e.target.value)}
                />
              </div>

              <div className="form-group-row">
                <div className="form-group">
                  <label>Temperature</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1.5"
                    value={config?.llm?.temperature ?? 0.1}
                    onChange={(e) => handleInputChange('llm', 'temperature', parseFloat(e.target.value) || 0.0)}
                  />
                  <span className="input-hint">Lower = factual.</span>
                </div>
                <div className="form-group">
                  <label>Max Gen Tokens</label>
                  <input
                    type="number"
                    min="64"
                    max="4096"
                    value={config?.llm?.max_tokens ?? 1024}
                    onChange={(e) => handleInputChange('llm', 'max_tokens', parseInt(e.target.value) || 1024)}
                  />
                  <span className="input-hint">Response size limit.</span>
                </div>
              </div>
            </div>

            {/* Section 3: Embeddings & Vector DB Settings */}
            <div className="settings-card">
              <h3>Embedding & Database Settings</h3>
              <p className="card-desc">Pipeline backend models and database endpoints.</p>

              <div className="form-group">
                <label>Dense Embedding Model Name</label>
                <input
                  type="text"
                  value={config?.embedding?.model_name ?? ''}
                  onChange={(e) => handleInputChange('embedding', 'model_name', e.target.value)}
                />
                <span className="input-hint">Hugging Face identifier (e.g. all-MiniLM-L6-v2)</span>
              </div>

              <div className="form-group">
                <label>Sparse Embedding Model Name</label>
                <input
                  type="text"
                  value={config?.embedding?.sparse_model_name || 'Qdrant/bm25'}
                  onChange={(e) => handleInputChange('embedding', 'sparse_model_name', e.target.value)}
                />
                <span className="input-hint">Lexical identifier (e.g. Qdrant/bm25)</span>
              </div>

              <div className="form-group">
                <label>Embedding Device</label>
                <select
                  value={config?.embedding?.device ?? 'cpu'}
                  onChange={(e) => handleInputChange('embedding', 'device', e.target.value)}
                >
                  <option value="cpu">CPU</option>
                  <option value="cuda">CUDA (NVIDIA GPU)</option>
                  <option value="mps">MPS (Apple Silicon)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Qdrant Collection Name</label>
                <input
                  type="text"
                  value={config?.qdrant?.collection_name ?? ''}
                  onChange={(e) => handleInputChange('qdrant', 'collection_name', e.target.value)}
                />
              </div>
              
              <div className="form-group-row">
                <div className="form-group">
                  <label>Local Path</label>
                  <input
                    type="text"
                    placeholder="e.g. qdrant_db"
                    value={config?.qdrant?.path || ''}
                    onChange={(e) => handleInputChange('qdrant', 'path', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Remote Server URL (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. http://localhost:6333"
                    value={config?.qdrant?.url || ''}
                    onChange={(e) => handleInputChange('qdrant', 'url', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Section 4: Prompt Template Settings */}
            <div className="settings-card full-width">
              <h3>System Instruction Template</h3>
              <p className="card-desc">Customize how retrieved context blocks are styled and formatted for the LLM. You must include <code>{"{context}"}</code> and <code>{"{question}"}</code> variables.</p>
              
              <div className="form-group">
                <textarea
                  value={config?.llm?.system_prompt ?? ''}
                  onChange={(e) => handleInputChange('llm', 'system_prompt', e.target.value)}
                  rows={10}
                  className="prompt-textarea"
                />
              </div>
            </div>

          </div>

          {saveStatus && (
            <div className={`save-status-banner ${saveStatus.state}`}>
              <span>{saveStatus.state === 'saving' ? '⚙️' : saveStatus.state === 'success' ? '✅' : '❌'} {saveStatus.message}</span>
            </div>
          )}

          <div className="submit-section">
            <button type="submit" disabled={saveStatus?.state === 'saving'} className="save-settings-btn">
              {saveStatus?.state === 'saving' ? 'Reloading...' : 'Save Configuration'}
            </button>
          </div>
        </form>
      </div>
    );
  } catch (error) {
    console.error("Settings rendering exception:", error);
    return (
      <div className="settings-error-state" style={{ padding: '40px', color: '#ff4d4d', background: '#111', border: '1px solid #333', borderRadius: '12px', maxWidth: '600px', margin: '40px auto' }}>
        <h3>⚠️ React Rendering Error</h3>
        <p style={{ fontSize: '13px', color: '#aaa', margin: '15px 0' }}>An unexpected error occurred while rendering the settings page:</p>
        <code style={{ display: 'block', background: '#000', padding: '10px', borderRadius: '6px', overflowX: 'auto', color: '#ff8080' }}>{error.message}</code>
        <button onClick={fetchConfig} className="retry-btn" style={{ marginTop: '20px', padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Reload Configuration</button>
      </div>
    );
  }
}
