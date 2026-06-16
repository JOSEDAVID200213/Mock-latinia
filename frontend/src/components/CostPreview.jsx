import React, { useState } from 'react';
import { Play, FileText, AlertCircle, Coins } from 'lucide-react';
import { api } from '../services/api';

const CostPreview = ({ uploadData, onProcessComplete, onCancel }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const { meeting_id, extraction, cost_estimate, text_preview } = uploadData;

  const handleConfirm = async () => {
    setIsProcessing(true);
    setError(null);
    try {
      const result = await api.processMeeting(meeting_id);
      onProcessComplete(result);
    } catch (err) {
      setError(err.message);
      setIsProcessing(false);
    }
  };

  const getQualityBadge = (score) => {
    if (score >= 0.8) return <span className="badge badge-success">Óptima</span>;
    if (score >= 0.5) return <span className="badge badge-warning">Media</span>;
    return <span className="badge badge-error">Baja</span>;
  };

  return (
    <div className="card animate-fade-in">
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <FileText color="var(--accent-primary)" />
        Pre-Análisis Completado
      </h2>

      {error && (
        <div className="badge badge-error" style={{ marginBottom: '1rem', width: '100%', padding: '1rem', justifyContent: 'center' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ background: 'var(--bg-surface-elevated)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Texto Extraído</p>
          <p style={{ fontSize: '1.2rem', fontWeight: '600' }}>{extraction.word_count.toLocaleString()} palabras</p>
          <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Calidad OCR:</span>
            {getQualityBadge(extraction.quality_score)}
          </div>
        </div>

        <div style={{ background: 'var(--bg-surface-elevated)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <Coins size={14} /> Tokens Estimados
          </p>
          <p style={{ fontSize: '1.2rem', fontWeight: '600' }}>{cost_estimate.total_estimated_tokens.toLocaleString()}</p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--success)' }}>
            ✓ Free Tier (Costo: ${cost_estimate.estimated_cost_usd.toFixed(4)})
          </p>
        </div>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>Preview del texto (Primeros 500 caractéres)</p>
        <div style={{ 
          background: 'var(--bg-main)', 
          padding: '1rem', 
          borderRadius: 'var(--radius-md)',
          fontSize: '0.9rem',
          color: 'var(--text-muted)',
          fontFamily: 'monospace',
          maxHeight: '150px',
          overflowY: 'auto'
        }}>
          {text_preview}
        </div>
      </div>
      
      {extraction.extraction_warnings.length > 0 && (
        <div style={{ background: 'var(--warning-bg)', color: 'var(--warning)', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '2rem', display: 'flex', gap: '0.5rem', fontSize: '0.9rem' }}>
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <div>
            <strong>Avisos de extracción:</strong>
            <ul style={{ marginLeft: '1.5rem', marginTop: '0.25rem' }}>
              {extraction.extraction_warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '1rem' }}>
        <button 
          className="btn btn-secondary" 
          onClick={onCancel}
          disabled={isProcessing}
          style={{ flex: 1 }}
        >
          Cancelar
        </button>
        <button 
          className="btn btn-primary" 
          onClick={handleConfirm}
          disabled={isProcessing}
          style={{ flex: 2 }}
        >
          {isProcessing ? (
             <><span className="animate-spin">🤖</span> Procesando con IA...</>
          ) : (
             <><Play size={18} /> Procesar Resumen</>
          )}
        </button>
      </div>
    </div>
  );
};

export default CostPreview;
