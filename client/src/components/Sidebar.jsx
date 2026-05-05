import { useState, useRef } from 'react';
import { uploadDocument, deleteDocument } from '../services/api';

export default function Sidebar({ documents, onDocumentsChange }) {
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [toast, setToast] = useState(null);
  const fileInputRef = useRef(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleUpload = async (file) => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showToast('Only PDF files are supported.', 'error');
      return;
    }

    if (file.size > 100 * 1024 * 1024) {
      showToast('File exceeds 100 MB limit.', 'error');
      return;
    }

    setUploading(true);
    try {
      await uploadDocument(file);
      showToast(`"${file.name}" uploaded successfully!`);
      onDocumentsChange();
    } catch (err) {
      showToast(err.message || 'Upload failed.', 'error');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id, filename) => {
    if (!confirm(`Remove "${filename}" from the knowledge base?`)) return;

    try {
      await deleteDocument(id);
      showToast(`"${filename}" removed.`);
      onDocumentsChange();
    } catch (err) {
      showToast(err.message || 'Delete failed.', 'error');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer?.files?.[0];
    if (file) handleUpload(file);
  };

  const formatSize = (bytes) => {
    if (!bytes) return '';
    const mb = bytes / (1024 * 1024);
    return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Knowledge Base</h2>
        <div
          className={`upload-area ${dragging ? 'dragging' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={(e) => handleUpload(e.target.files?.[0])}
          />
          <div className="upload-icon">📄</div>
          <div className="upload-text">Drop a PDF or click to upload</div>
          <div className="upload-hint">Max 100 MB</div>
        </div>

        {uploading && (
          <div className="upload-progress">
            <div className="spinner" />
            Processing document...
          </div>
        )}
      </div>

      <div className="doc-list">
        {documents.length === 0 ? (
          <div className="doc-list-empty">
            No documents yet.
            <br />
            Upload a PDF to get started.
          </div>
        ) : (
          documents.map((doc) => (
            <div key={doc.id} className="doc-item">
              <span className="doc-icon">📑</span>
              <div className="doc-info">
                <div className="doc-name" title={doc.filename}>
                  {doc.filename}
                </div>
                <div className="doc-meta">
                  {doc.chunks_count} chunks · {formatSize(doc.file_size)} · {formatDate(doc.uploaded_at)}
                </div>
              </div>
              <button
                className="doc-delete"
                onClick={() => handleDelete(doc.id, doc.filename)}
                title="Remove document"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>

      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </aside>
  );
}
