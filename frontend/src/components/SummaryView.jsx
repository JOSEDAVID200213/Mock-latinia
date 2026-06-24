import React, { useEffect, useRef } from 'react';

const SummaryView = ({ result, onNewMeeting }) => {
  const { meeting_name, summary, processing } = result;
  const cardRef = useRef(null);

  // Parallax / Glass reflection effect
  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    cardRef.current.style.setProperty('--mouse-x', `${x}px`);
    cardRef.current.style.setProperty('--mouse-y', `${y}px`);
  };

  return (
    <div className="flex-1 flex items-center justify-center py-6 md:py-12 w-full animate-in fade-in zoom-in duration-500">
      <div 
        ref={cardRef}
        onMouseMove={handleMouseMove}
        className="w-full max-w-2xl bg-surface-container-low/40 backdrop-blur-[30px] rounded-[2rem] border border-white/10 p-8 md:p-16 text-center bg-white/[0.03] transition-all duration-300 hover:border-primary/30 relative overflow-hidden group"
      >
        {/* Glow effect on hover mapped to cursor position */}
        <div 
          className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
          style={{
            background: `radial-gradient(600px circle at var(--mouse-x, 0) var(--mouse-y, 0), rgba(94, 92, 230, 0.06), transparent 40%)`
          }}
        />

        {/* Atmospheric light leak */}
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 rounded-full blur-[80px]"></div>
        <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-[#6904c5]/10 rounded-full blur-[80px]"></div>

        {/* Centered Success State */}
        <div className="relative mb-10 inline-block animate-[float_6s_ease-in-out_infinite]">
          <div className="w-32 h-32 md:w-40 md:w-40 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
            <span 
              className="material-symbols-outlined text-7xl md:text-8xl text-primary drop-shadow-[0_0_20px_rgba(194,193,255,0.4)]" 
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              check_circle
            </span>
          </div>
        </div>

        <h2 className="font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface mb-8 leading-tight">
          ¡Procesamiento Completado!
        </h2>

        {/* Info Cards Bento-ish */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
          <div className="bg-white/[0.03] backdrop-blur-[20px] border border-white/[0.08] rounded-2xl p-6 flex items-start gap-4 text-left">
            <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-primary">label</span>
            </div>
            <div className="overflow-hidden">
              <p className="text-on-surface-variant text-label-caps font-label-caps mb-1 opacity-60">NOMBRE DE LA REUNIÓN</p>
              <p className="text-on-surface font-headline-md text-base md:text-lg truncate" title={meeting_name}>
                {meeting_name}
              </p>
            </div>
          </div>
          
          <div className="bg-white/[0.03] backdrop-blur-[20px] border border-white/[0.08] rounded-2xl p-6 flex items-start gap-4 text-left">
            <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-tertiary">timer</span>
            </div>
            <div>
              <p className="text-on-surface-variant text-label-caps font-label-caps mb-1 opacity-60">TIEMPO DE PROCESAMIENTO</p>
              <p className="text-on-surface font-headline-md text-base md:text-lg">
                {processing?.processing_time_seconds || '0'}s
                <span className="text-tertiary text-sm font-normal ml-2 opacity-80">Rápido</span>
              </p>
            </div>
          </div>
        </div>

        {/* Primary Actions */}
        <div className="space-y-4 relative z-10">
          <a 
            href={summary?.doc_url}
            target="_blank"
            rel="noreferrer"
            className="w-full md:w-auto min-w-[320px] bg-gradient-to-br from-[#5E5CE6] to-[#c2c1ff] py-5 px-8 rounded-3xl text-white font-bold inline-flex items-center justify-center gap-3 shadow-[0_0_30px_0_rgba(94,92,230,0.2)] hover:scale-[1.02] active:scale-[0.98] transition-all group"
          >
            <span className="material-symbols-outlined group-hover:translate-y-[-2px] transition-transform">folder_open</span>
            <span className="text-lg">Abrir Carpeta de la Reunión</span>
            <span className="material-symbols-outlined text-sm opacity-60 ml-2">open_in_new</span>
          </a>
          
          <div className="pt-4">
            <button 
              onClick={onNewMeeting}
              className="text-on-surface-variant hover:text-primary transition-all font-body-md inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full hover:bg-white/5 active:scale-95"
            >
              <span className="material-symbols-outlined">restart_alt</span>
              Procesar otra reunión
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryView;
