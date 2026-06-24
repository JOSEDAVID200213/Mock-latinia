import React, { useState, useRef } from 'react';
import { api } from '../services/api';

const FileUpload = ({ onAnalysisComplete }) => {
  const [file, setFile] = useState(null);
  const [meetingName, setMeetingName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setError(null);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleSubmit = async () => {
    if (!meetingName) {
      setError("Por favor ingresa un nombre para la reunión.");
      return;
    }
    if (!file) {
      setError("Por favor selecciona un archivo para analizar.");
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await api.uploadFile(file, meetingName);
      onAnalysisComplete(result);
    } catch (err) {
      setError(err.message || "Error al procesar el archivo");
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full max-w-3xl animate-in fade-in zoom-in duration-500">
      {/* Header Section */}
      <div className="text-center mb-10">
        <h1 className="font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface mb-2">Sube tu transcripción</h1>
        <p className="text-on-surface-variant font-body-lg">Sube la grabación o notas de tu reunión para generar un resumen inteligente.</p>
      </div>
      
      {/* Main Glass Form Container */}
      <div className="bg-white/[0.03] backdrop-blur-[20px] border border-white/[0.08] p-8 md:p-12 rounded-3xl shadow-[0_0_30px_0_rgba(94,92,230,0.2)] space-y-8 transition-all duration-300">
        
        {/* Meeting Name Field */}
        <div className="space-y-3">
          <label className="block font-label-caps text-label-caps text-on-surface-variant uppercase" htmlFor="meeting_name">Nombre de la Reunión</label>
          <input 
            className="w-full bg-surface-container border border-white/10 rounded-2xl px-6 py-4 text-on-surface placeholder:text-on-surface-variant/40 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all duration-300" 
            id="meeting_name" 
            placeholder="Ej. Planificación Trimestral Q3" 
            required 
            type="text"
            value={meetingName}
            onChange={(e) => setMeetingName(e.target.value)}
            disabled={isUploading}
          />
        </div>

        {/* Drag and Drop Zone */}
        <div 
          className="relative group cursor-pointer" 
          onClick={() => !isUploading && fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input 
            className="hidden" 
            id="file_input" 
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            disabled={isUploading}
            accept=".txt,.md,.pdf,.docx,.rtf,.xlsx,.pptx,.csv,.html"
          />
          <div className={`border-2 border-dashed rounded-3xl p-12 flex flex-col items-center justify-center space-y-4 transition-all duration-300 cubic-bezier(0.33, 1, 0.68, 1) min-h-[300px] ${
            isDragging 
              ? 'border-primary bg-primary/10' 
              : 'border-white/10 bg-primary/5 group-hover:bg-primary/10 group-hover:border-primary/50'
          }`}>
            <div className="w-20 h-20 bg-primary-container/20 rounded-full flex items-center justify-center text-primary mb-2 group-hover:scale-110 transition-transform duration-500">
              <span className="material-symbols-outlined text-5xl">cloud_upload</span>
            </div>
            <div className="text-center">
              <p className="text-xl font-bold text-on-surface mb-1">Arrastra tu archivo aquí</p>
              <p className="text-on-surface-variant text-sm">PDF, DOCX o TXT (Máx. 25MB)</p>
            </div>
            
            {file && (
              <div className="w-full max-w-sm mt-4 p-4 rounded-2xl bg-surface-container-high border border-white/5 flex items-center justify-between animate-in fade-in zoom-in duration-300">
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-primary">description</span>
                  <span className="text-sm font-medium text-on-surface truncate max-w-[180px]">{file.name}</span>
                </div>
                <span className="text-xs text-on-surface-variant/60">{(file.size / 1024).toFixed(1)} KB</span>
              </div>
            )}
          </div>
        </div>

        {/* Error Alert Area */}
        {error && (
          <div className="animate-in fade-in slide-in-from-top-4 duration-300" id="error_container">
            <div className="bg-error-container/20 border border-error/20 rounded-2xl p-4 flex items-start gap-4">
              <span className="material-symbols-outlined text-error mt-0.5">error</span>
              <div className="space-y-1">
                <p className="text-error font-bold text-sm">Error</p>
                <p className="text-on-error-container text-xs leading-relaxed" id="error_message">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* CTA Button */}
        <div className="pt-4">
          <button 
            className="w-full py-5 px-8 bg-gradient-to-br from-[#5E5CE6] to-[#c2c1ff] text-white font-bold text-lg rounded-2xl shadow-[0_0_30px_0_rgba(94,92,230,0.2)] hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100" 
            onClick={handleSubmit}
            disabled={isUploading || !meetingName || !file}
          >
            {!isUploading ? (
              <span className="relative z-10" id="btn_text">Continuar al Análisis</span>
            ) : (
              <div className="relative z-10 flex items-center gap-3" id="loading_spinner">
                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor"></path>
                </svg>
                <span>Procesando archivo...</span>
              </div>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
