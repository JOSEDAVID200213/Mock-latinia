import React from 'react';
import { CheckCircle2, ExternalLink, FileText } from 'lucide-react';

const SummaryView = ({ result, onNewMeeting }) => {
  const { meeting_name, summary, processing } = result;

  return (
    <div className="animate-fade-in" style={{ 
      maxWidth: '600px', 
      margin: '2rem auto', 
      display: 'flex', 
      flexDirection: 'column', 
      gap: '2rem',
      textAlign: 'center'
    }}>
      <div className="card" style={{ 
        padding: '3rem 2rem', 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        gap: '1.5rem',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        boxShadow: 'var(--shadow-glow)'
      }}>
        <div style={{ 
          background: 'var(--success-bg)', 
          color: 'var(--success)', 
          borderRadius: '50%', 
          padding: '1rem',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(16, 185, 129, 0.2)'
        }}>
          <CheckCircle2 size={48} />
        </div>

        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: '700', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
            ¡Procesamiento Completado!
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            El acta y el resumen han sido generados y guardados en Google Drive.
          </p>
        </div>

        <div style={{ 
          width: '100%', 
          background: 'var(--bg-surface-elevated)', 
          padding: '1.25rem', 
          borderRadius: 'var(--radius-md)',
          textAlign: 'left',
          border: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Reunión:</span>
            <span style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.95rem' }}>{meeting_name}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Tiempo de procesamiento:</span>
            <span style={{ fontWeight: '600', color: 'var(--accent-primary)', fontSize: '0.95rem' }}>{processing?.processing_time_seconds || '0'}s</span>
          </div>
        </div>

        {summary?.doc_url ? (
          <a 
            href={summary.doc_url} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="btn btn-primary" 
            style={{ 
              width: '100%', 
              justifyContent: 'center', 
              padding: '0.85rem 1.5rem',
              fontSize: '1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              textDecoration: 'none',
              borderRadius: 'var(--radius-md)'
            }}
          >
            <FileText size={18} />
            Abrir acta en Google Docs
            <ExternalLink size={14} />
          </a>
        ) : (
          <p style={{ color: 'var(--error)' }}>
            Error: No se pudo recuperar el enlace del documento de Google Docs.
          </p>
        )}
      </div>

      <div>
        <button className="btn btn-secondary" onClick={onNewMeeting} style={{ padding: '0.75rem 2rem' }}>
          Procesar otra reunión
        </button>
      </div>
    </div>
  );
};

export default SummaryView;
