import React, { useState } from 'react';
import { api } from '../services/api';

const CostPreview = ({ uploadData, onProcessComplete, onCancel }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const { meeting_id, extraction, text_preview } = uploadData;

  const handleConfirm = async () => {
    setIsProcessing(true);
    setError(null);
    try {
      await api.processMeeting(meeting_id);
      
      // Polling para revisar el estado en background
      const pollInterval = setInterval(async () => {
        try {
          const statusResult = await api.getMeeting(meeting_id);
          if (statusResult.status === 'completed') {
            clearInterval(pollInterval);
            onProcessComplete(statusResult);
          } else if (statusResult.status === 'failed') {
            clearInterval(pollInterval);
            setError('Hubo un error al procesar el archivo en el servidor.');
            setIsProcessing(false);
          }
          // Si es 'processing', sigue esperando
        } catch (pollErr) {
          console.error("Error en polling:", pollErr);
        }
      }, 3000); // Preguntar cada 3 segundos

    } catch (err) {
      setError(err.message || 'Error al iniciar el procesamiento');
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto w-full animate-in fade-in zoom-in duration-500">
      {/* Page Header */}
      <div className="mb-12 text-center md:text-left">
        <h1 className="font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface mb-4">Confirmar Transcripción</h1>
        <p className="font-body-lg text-on-surface-variant max-w-2xl">Por favor confirma que este es el archivo correcto antes de generar el resumen con IA.</p>
      </div>
      
      {error && (
          <div className="mb-8 animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="bg-error-container/20 border border-error/20 rounded-2xl p-4 flex items-start gap-4">
              <span className="material-symbols-outlined text-error mt-0.5">error</span>
              <div className="space-y-1">
                <p className="text-error font-bold text-sm">Error</p>
                <p className="text-on-error-container text-xs leading-relaxed">{error}</p>
              </div>
            </div>
          </div>
      )}

      {/* Metrics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white/[0.03] backdrop-blur-[20px] border border-white/[0.08] rounded-3xl p-6 flex items-center justify-between hover:border-primary/30 hover:bg-white/[0.05] transition-all duration-300">
          <div>
            <p className="text-label-caps text-on-surface-variant mb-1 font-label-caps">PALABRAS EXTRAÍDAS</p>
            <h3 className="font-headline-md text-on-surface text-2xl">{extraction?.word_count?.toLocaleString() || 0}</h3>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary">format_list_numbered</span>
          </div>
        </div>
        
        <div className="bg-white/[0.03] backdrop-blur-[20px] border border-white/[0.08] rounded-3xl p-6 flex items-center justify-between hover:border-primary/30 hover:bg-white/[0.05] transition-all duration-300">
          <div>
            <p className="text-label-caps text-on-surface-variant mb-1 font-label-caps">CALIDAD OCR</p>
            <div className="flex items-center gap-2">
               <h3 className="font-headline-md text-on-surface text-2xl">{(extraction?.quality_score * 100).toFixed(0)}%</h3>
               {extraction?.quality_score >= 0.8 ? (
                 <span className="px-2 py-1 text-[10px] rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">ÓPTIMA</span>
               ) : (
                 <span className="px-2 py-1 text-[10px] rounded-full bg-warning/20 text-warning border border-warning/30">MEDIA/BAJA</span>
               )}
            </div>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
            <span className="material-symbols-outlined text-emerald-400">check_circle</span>
          </div>
        </div>
      </div>

      {/* Editor / Console Block */}
      <div className="bg-white/[0.06] backdrop-blur-[40px] border border-white/[0.15] rounded-3xl overflow-hidden mb-12 flex flex-col shadow-2xl">
        {/* Console Header */}
        <div className="bg-white/5 px-6 py-3 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-white/10"></div>
            <div className="w-3 h-3 rounded-full bg-white/10"></div>
            <div className="w-3 h-3 rounded-full bg-white/10"></div>
            <span className="ml-4 font-label-caps text-on-surface-variant text-[10px] opacity-40">TRANSCRIPT_PREVIEW_V1.TXT</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="font-label-caps text-on-surface-variant text-[10px] opacity-40">UTF-8</span>
            <span className="material-symbols-outlined text-on-surface-variant text-sm">terminal</span>
          </div>
        </div>

        {/* Console Content */}
        <div className="bg-surface-container-lowest h-[300px] overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-white/5 [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full font-code-preview p-6 text-on-surface-variant leading-relaxed relative">
          <div className="flex gap-6">
            <div className="space-y-4 text-sm md:text-base font-mono whitespace-pre-wrap">
              {text_preview || "No preview available."}
            </div>
          </div>
        </div>

        {/* Console Footer */}
        <div className="bg-white/5 px-6 py-2 border-t border-white/10 flex justify-between items-center">
          <p className="font-label-caps text-[10px] text-on-surface-variant opacity-40">PREVIEW PRE-PROCESAMIENTO</p>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
            <p className="font-label-caps text-[10px] text-emerald-500">READY TO PROCESS</p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <button 
          className="w-full md:w-auto px-8 py-4 rounded-2xl border border-white/10 text-on-surface-variant font-bold hover:bg-white/5 transition-all duration-300 flex items-center justify-center gap-2 group disabled:opacity-50"
          onClick={onCancel}
          disabled={isProcessing}
        >
          <span className="material-symbols-outlined text-xl transition-transform group-hover:-translate-x-1">arrow_back</span>
          Cancelar y subir otro
        </button>
        
        <button 
          className="w-full md:w-auto px-10 py-4 bg-gradient-to-br from-[#5E5CE6] to-[#c2c1ff] text-white font-bold rounded-2xl shadow-[0_0_30px_0_rgba(94,92,230,0.2)] transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-3 relative overflow-hidden disabled:opacity-80 disabled:cursor-wait disabled:hover:scale-100"
          onClick={handleConfirm}
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <div className="relative z-10 flex items-center justify-center h-5 w-5">
                <div className="absolute w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
              </div>
              <span className="relative z-10 opacity-90">Procesando...</span>
            </>
          ) : (
             <>
               <span className="relative z-10">Generar Resumen</span>
               <span className="material-symbols-outlined relative z-10">auto_awesome</span>
             </>
          )}
        </button>
      </div>
    </div>
  );
};

export default CostPreview;
