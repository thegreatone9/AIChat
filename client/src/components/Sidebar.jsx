import { useState, useRef } from 'react';
import { uploadDocument, deleteDocument, ingestUrl } from '../services/api';

const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx', '.csv'];

export default function Sidebar({ documents, onDocumentsChange }) {
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [toast, setToast] = useState(null);
  const [urlInput, setUrlInput] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const fileInputRef = useRef(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const isAllowedFile = (filename) => {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return ALLOWED_EXTENSIONS.includes(ext);
  };

  const handleUpload = async (file) => {
    if (!file) return;

    if (!isAllowedFile(file.name)) {
      showToast(`Unsupported file type. Supported: ${ALLOWED_EXTENSIONS.join(', ')}`, 'error');
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

  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    const url = urlInput.trim();

    if (!url) return;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      showToast('URL must start with http:// or https://', 'error');
      return;
    }

    setUploading(true);
    try {
      await ingestUrl(url);
      showToast('Web page ingested successfully!');
      setUrlInput('');
      setShowUrlInput(false);
      onDocumentsChange();
    } catch (err) {
      showToast(err.message || 'URL ingestion failed.', 'error');
    } finally {
      setUploading(false);
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

  const getDocIcon = (filename) => {
    if (!filename) return '📄';
    const ext = filename.split('.').pop()?.toLowerCase();
    const icons = { pdf: '📕', txt: '📝', md: '📋', docx: '📘', csv: '📊' };
    return icons[ext] || '🌐';
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
            accept={ALLOWED_EXTENSIONS.join(',')}
            onChange={(e) => handleUpload(e.target.files?.[0])}
          />
          <div className="upload-icon">📄</div>
          <div className="upload-text">Drop a file or click to upload</div>
          <div className="upload-hint">PDF · TXT · MD · DOCX · CSV · Max 100 MB</div>
        </div>

        <button
          className="url-toggle-btn"
          onClick={() => setShowUrlInput(!showUrlInput)}
        >
          🌐 {showUrlInput ? 'Hide URL input' : 'Add web page'}
        </button>

        {showUrlInput && (
          <form className="url-input-form" onSubmit={handleUrlSubmit}>
            <input
              type="url"
              className="url-input"
              placeholder="https://example.com/article"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              disabled={uploading}
            />
            <button type="submit" className="url-submit-btn" disabled={uploading || !urlInput.trim()}>
              Add
            </button>
          </form>
        )}

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
            Upload a file or add a web page to get started.
          </div>
        ) : (
          documents.map((doc) => (
            <div key={doc.id} className="doc-item">
              <span className="doc-icon">{getDocIcon(doc.filename)}</span>
              <div className="doc-info">
                <div className="doc-name" title={doc.filename}>
                  {doc.filename}
                </div>
                <div className="doc-meta">
                  {doc.chunks_count} chunks
                  {doc.file_size ? ` · ${formatSize(doc.file_size)}` : ''}
                  {' · '}{formatDate(doc.uploaded_at)}
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
