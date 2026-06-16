import React from 'react';
import { Download, Users, Target, CheckSquare, AlertTriangle, ArrowRight } from 'lucide-react';
import { api } from '../services/api';

const SummaryView = ({ result, onNewMeeting }) => {
  const { meeting_id, meeting_name, summary, processing } = result;

  const handleDownload = (format) => {
    api.downloadSummary(meeting_id, format);
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Info */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>{meeting_name}</h2>
          <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            <span>📅 {summary.date_detected || 'Fecha no detectada'}</span>
            <span>⏱️ {processing.processing_time_seconds}s</span>
            <span>🤖 {processing.model}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" onClick={() => handleDownload('json')}>
            <Download size={16} /> JSON
          </button>
          <button className="btn btn-primary" onClick={() => handleDownload('html')}>
            <Download size={16} /> HTML
          </button>
        </div>
      </div>

      {/* Grid Layout para el Resumen */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '1.5rem' }}>
        
        {/* Columna Principal */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {summary.executive_summary && (
            <div className="card" style={{ borderLeft: '4px solid var(--warning)' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--warning)' }}>
                Resumen Ejecutivo
              </h3>
              <p style={{ color: 'var(--text-secondary)' }}>{summary.executive_summary}</p>
            </div>
          )}

          {summary.topics_discussed.length > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: '1rem' }}>💬 Temas Discutidos</h3>
              <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-secondary)' }}>
                {summary.topics_discussed.map((topic, i) => <li key={i} style={{ marginBottom: '0.5rem' }}>{topic}</li>)}
              </ul>
            </div>
          )}

          {summary.decisions_made.length > 0 && (
            <div className="card" style={{ borderLeft: '4px solid var(--success)' }}>
              <h3 style={{ marginBottom: '1rem', color: 'var(--success)' }}>✅ Decisiones Tomadas</h3>
              <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-secondary)' }}>
                {summary.decisions_made.map((decision, i) => <li key={i} style={{ marginBottom: '0.5rem' }}>{decision}</li>)}
              </ul>
            </div>
          )}
        </div>

        {/* Columna Lateral */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {summary.participants.length > 0 && (
            <div className="card" style={{ padding: '1.5rem' }}>
              <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Users size={18} /> Participantes ({summary.participants.length})
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {summary.participants.map((p, i) => (
                  <span key={i} style={{ background: 'var(--bg-surface-elevated)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.85rem' }}>
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          {summary.pending_tasks.length > 0 && (
            <div className="card" style={{ padding: '1.5rem' }}>
              <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
                <CheckSquare size={18} /> Tareas Pendientes
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {summary.pending_tasks.map((task, i) => (
                  <div key={i} style={{ background: 'var(--bg-surface-elevated)', padding: '0.75rem', borderRadius: '8px' }}>
                    <p style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}>{task.task}</p>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>👤 {task.responsible || 'Sin asignar'}</span>
                      {task.deadline && <span>⏱️ {task.deadline}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {summary.risks_and_blockers.length > 0 && (
            <div className="card" style={{ padding: '1.5rem', borderLeft: '4px solid var(--error)' }}>
              <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--error)' }}>
                <AlertTriangle size={18} /> Riesgos
              </h4>
              <ul style={{ paddingLeft: '1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                {summary.risks_and_blockers.map((risk, i) => <li key={i}>{risk}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <button className="btn btn-secondary" onClick={onNewMeeting}>
          Procesar otra reunión
        </button>
      </div>
    </div>
  );
};

export default SummaryView;
