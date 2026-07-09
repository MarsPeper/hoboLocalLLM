import React, { useState, useEffect } from 'react';

export default function DocumentManager() {
  const [documents, setDocuments] = useState([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { state: 'uploading'|'success'|'error', filename: '', message: '' }
  const [isLoading, setIsLoading] = useState(false);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/documents');
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const handleFileChange = async (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const uploadFile = async (file) => {
    const allowedExtensions = /(\.pdf|\.docx|\.txt|\.md)$/i;
    if (!allowedExtensions.exec(file.name)) {
      setUploadStatus({
        state: 'error',
        filename: file.name,
        message: 'Unsupported format. Please upload PDF, DOCX, TXT, or MD.'
      });
      return;
    }

    setUploadStatus({
      state: 'uploading',
      filename: file.name,
      message: 'Uploading document to server...'
    });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Upload failed');
      }

      // Begin real-time progress polling interval
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`http://localhost:8000/api/upload/status/${encodeURIComponent(file.name)}`);
          if (!statusRes.ok) return;

          const statusData = await statusRes.json();

          if (statusData.status === 'extracting') {
            setUploadStatus({
              state: 'uploading',
              filename: file.name,
              message: '📄 Extracting text and partition splitting...'
            });
          } else if (statusData.status === 'indexing') {
            const { processed_chunks, total_chunks } = statusData;
            setUploadStatus({
              state: 'uploading',
              filename: file.name,
              message: `⚡ Generating embeddings & indexing: ${processed_chunks} / ${total_chunks} chunks...`
            });
          } else if (statusData.status === 'completed') {
            clearInterval(pollInterval);
            setUploadStatus({
              state: 'success',
              filename: file.name,
              message: `✅ Indexed successfully! Created ${statusData.total_chunks} chunks.`
            });
            fetchDocuments();
          } else if (statusData.status === 'failed') {
            clearInterval(pollInterval);
            setUploadStatus({
              state: 'error',
              filename: file.name,
              message: `❌ Ingestion failed: ${statusData.error || 'Unknown extraction error'}`
            });
          }
        } catch (pollErr) {
          console.error('Error polling status:', pollErr);
        }
      }, 1000);

    } catch (err) {
      console.error('Upload error:', err);
      setUploadStatus({
        state: 'error',
        filename: file.name,
        message: err.message || 'Connection error during ingestion.'
      });
    }
  };

  const handleDelete = async (filename) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

    try {
      const response = await fetch(`http://localhost:8000/api/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        fetchDocuments();
      }
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to completely clear the vector database? All indexed document vectors will be deleted.')) return;

    try {
      const response = await fetch('http://localhost:8000/api/reset', {
        method: 'POST',
      });
      if (response.ok) {
        setDocuments([]);
        setUploadStatus({
          state: 'success',
          filename: '',
          message: 'Vector database cleared successfully.'
        });
      }
    } catch (err) {
      console.error('Failed to reset database:', err);
    }
  };

  return (
    <div className="doc-manager-container">
      <div className="upload-section">
        <h3>Upload Documents</h3>
        <p className="section-subtitle">Ingest your local documents. They will be chunked, embedded, and stored in Qdrant.</p>
        
        <div
          className={`dropzone ${isDragOver ? 'dragover' : ''} ${uploadStatus?.state === 'uploading' ? 'loading' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-input"
            onChange={handleFileChange}
            accept=".pdf,.docx,.txt,.md"
            style={{ display: 'none' }}
          />
          <label htmlFor="file-input" className="dropzone-label">
            <span className="dropzone-icon">📥</span>
            <span className="dropzone-text">Drag & drop files here or click to browse</span>
            <span className="dropzone-subtext">Supports PDF, DOCX, TXT, and Markdown</span>
          </label>
          {uploadStatus?.state === 'uploading' && <div className="loader-shimmer"></div>}
        </div>

        {uploadStatus && (
          <div className={`upload-alert ${uploadStatus.state}`}>
            <div className="alert-header">
              <strong>{uploadStatus.filename || 'System'}</strong>
              <button onClick={() => setUploadStatus(null)} className="close-alert-btn">×</button>
            </div>
            <p className="alert-message">{uploadStatus.message}</p>
          </div>
        )}
      </div>

      <div className="docs-list-section">
        <div className="section-header">
          <h3>Indexed Document Library</h3>
          {documents.length > 0 && (
            <button onClick={handleReset} className="reset-db-btn">
              Clear Collection
            </button>
          )}
        </div>
        
        {isLoading ? (
          <div className="loading-spinner-wrapper">
            <div className="spinner"></div>
            <p>Loading document registry...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-docs-state">
            <span className="empty-icon">📁</span>
            <p>No documents indexed yet.</p>
            <p className="subtext">Drop files in the box above to build your local knowledge base.</p>
          </div>
        ) : (
          <div className="docs-table-wrapper">
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Document Name</th>
                  <th>Vector Chunks</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc, idx) => (
                  <tr key={idx}>
                    <td className="doc-name-cell">📄 {doc.file_name}</td>
                    <td>{doc.chunk_count} chunks</td>
                    <td>
                      <button
                        onClick={() => handleDelete(doc.file_name)}
                        className="delete-doc-btn"
                        title="Delete document index"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
