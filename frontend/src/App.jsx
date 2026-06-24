import React, { useState, useEffect } from 'react';
import FileUpload from './components/FileUpload';
import CostPreview from './components/CostPreview';
import SummaryView from './components/SummaryView';

const App = () => {
  // view: 'upload' | 'preview' | 'result'
  const [view, setView] = useState('upload');
  
  // Datos del pre-análisis
  const [uploadData, setUploadData] = useState(null);
  
  // Datos del resumen final
  const [resultData, setResultData] = useState(null);

  const handleAnalysisComplete = (data) => {
    setUploadData(data);
    setView('preview');
  };

  const handleProcessComplete = (data) => {
    setResultData(data);
    setView('result');
  };

  const resetFlow = () => {
    setUploadData(null);
    setResultData(null);
    setView('upload');
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Navigation Shell */}
      <header className="bg-surface/30 backdrop-blur-xl border-b border-white/10 sticky top-0 z-50">
        <div className="flex justify-between items-center px-4 md:px-16 py-4 max-w-[1440px] mx-auto">
          <div className="font-display-lg text-headline-md font-bold text-on-surface tracking-tight">Meeting Summary AI</div>
        </div>
      </header>

      <main className="flex flex-col md:flex-row max-w-[1440px] mx-auto w-full flex-1">
        {/* Side Navigation (Visible on Desktop) */}
        <aside className="hidden md:flex flex-col py-8 space-y-4 border-r border-white/10 w-[280px] bg-surface-container-lowest/50 backdrop-blur-2xl">
          <nav className="flex-1 flex flex-col">
            <div className="flex flex-col space-y-0 relative px-4">
              {/* Vertical Line */}
              <div className="absolute left-[31px] top-8 bottom-8 w-0.5 bg-white/10"></div>
              
              {/* Step 1: Upload */}
              <div className="relative flex items-center gap-4 py-4">
                <div className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center ${view === 'upload' ? 'bg-primary text-on-primary shadow-[0_0_15px_rgba(194,193,255,0.4)]' : 'bg-surface-container border border-white/10 text-primary'}`}>
                  {view === 'upload' ? <span className="text-xs font-bold">1</span> : <span className="material-symbols-outlined text-sm">check</span>}
                </div>
                <div className="flex flex-col">
                  <span className={`${view === 'upload' ? 'text-primary font-bold' : 'text-on-surface-variant font-medium'} text-sm`}>Upload</span>
                  <span className="text-on-surface-variant/40 text-xs">{view === 'upload' ? 'Active' : 'Completed'}</span>
                </div>
              </div>

              {/* Step 2: Confirm */}
              <div className="relative flex items-center gap-4 py-4">
                <div className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center ${view === 'preview' ? 'bg-primary text-on-primary shadow-[0_0_15px_rgba(194,193,255,0.4)]' : view === 'result' ? 'bg-surface-container border border-white/10 text-primary' : 'bg-surface-container border border-white/10 text-on-surface-variant'}`}>
                  {view === 'preview' ? <span className="text-xs font-bold">2</span> : view === 'result' ? <span className="material-symbols-outlined text-sm">check</span> : <span className="text-xs font-bold">2</span>}
                </div>
                <div className="flex flex-col">
                  <span className={`${view === 'preview' ? 'text-primary font-bold' : 'text-on-surface-variant font-medium'} text-sm`}>Confirm</span>
                  <span className="text-on-surface-variant/40 text-xs">{view === 'preview' ? 'Active' : view === 'result' ? 'Completed' : 'Pending'}</span>
                </div>
              </div>

              {/* Step 3: Result */}
              <div className="relative flex items-center gap-4 py-4">
                <div className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center ${view === 'result' ? 'bg-primary text-on-primary shadow-[0_0_15px_rgba(194,193,255,0.4)]' : 'bg-surface-container border border-white/10 text-on-surface-variant'}`}>
                  <span className="text-xs font-bold">3</span>
                </div>
                <div className="flex flex-col">
                  <span className={`${view === 'result' ? 'text-primary font-bold' : 'text-on-surface-variant font-medium'} text-sm`}>Result</span>
                  <span className="text-on-surface-variant/40 text-xs">{view === 'result' ? 'Completed' : 'Pending'}</span>
                </div>
              </div>
            </div>
          </nav>
        </aside>

        {/* Main Content Area */}
        <section className="flex-1 px-4 md:px-16 py-12 flex items-center justify-center w-full relative z-10">
          {view === 'upload' && (
            <FileUpload onAnalysisComplete={handleAnalysisComplete} />
          )}
          
          {view === 'preview' && uploadData && (
            <CostPreview 
              uploadData={uploadData} 
              onProcessComplete={handleProcessComplete}
              onCancel={resetFlow}
            />
          )}
          
          {view === 'result' && resultData && (
            <SummaryView 
              result={resultData} 
              onNewMeeting={resetFlow}
            />
          )}
        </section>
      </main>
    </div>
  );
};

export default App;
