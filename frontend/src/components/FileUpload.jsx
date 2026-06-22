import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

const FileUpload = ({ onAnalysisComplete }) => {
  const [file, setFile] = useState(null);
  const [meetingName, setMeetingName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  };

  const handleFileChange = (e) => {
    if (e.target.files[0]) setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !meetingName) return;

    setIsUploading(true);
    setError(null);

    try {
      const result = await api.uploadFile(file, meetingName);
      onAnalysisComplete(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="card animate-fade-in">
      <h2 style={{ marginBottom: '1.5rem' }}>Subir Transcripción</h2>
      
      {error && (
        <div className="badge badge-error" style={{ marginBottom: '1rem', width: '100%', padding: '1rem', justifyContent: 'center' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label className="input-label">Nombre de la Reunión</label>
          <input 
            type="text" 
            className="input-text" 
            placeholder="Ej: Sprint Planning Q1" 
            value={meetingName}
            onChange={(e) => setMeetingName(e.target.value)}
            required 
            disabled={isUploading}
          />
        </div>

        <div 
          className="input-group" 
          onDragOver={(e) => e.preventDefault()} 
          onDrop={handleDrop}
          style={{
            border: '2px dashed var(--border-color)',
            borderRadius: 'var(--radius-lg)',
            padding: '3rem 2rem',
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: file ? 'var(--bg-surface-elevated)' : 'transparent',
            transition: 'all 0.2s'
          }}
          onClick={() => document.getElementById('file-upload').click()}
        >
          <input 
            type="file" 
            id="file-upload" 
            style={{ display: 'none' }} 
            onChange={handleFileChange}
            accept=".txt,.md,.pdf,.docx,.rtf,.xlsx,.pptx,.csv,.html"
            disabled={isUploading}
          />
          
          {file ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={48} color="var(--accent-primary)" />
              <p style={{ fontWeight: '500' }}>{file.name}</p>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <UploadCloud size={48} color="var(--text-muted)" />
              <p>Arrastra tu archivo aquí o <strong>haz clic para explorar</strong></p>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '80%', margin: '0 auto' }}>
                Soporta TXT, MD, PDF, DOCX, RTF, XLSX, PPTX, CSV, HTML (Máx 25MB)
              </p>
            </div>
          )}
        </div>

        <button 
          type="submit" 
          className="btn btn-primary" 
          style={{ width: '100%' }}
          disabled={!file || !meetingName || isUploading}
        >
          {isUploading ? (
             <><span className="animate-spin">⏳</span> Analizando archivo...</>
          ) : (
             <><CheckCircle size={18} /> Continuar al Análisis</>
          )}
        </button>
      </form>
    </div>
  );
};

export default FileUpload;
