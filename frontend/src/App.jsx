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
    <div className="app-container">
      <header className="header animate-fade-in">
        <h1>Meeting Summary AI</h1>
        <p>Estandarización de actas empresariales impulsada por LLMs</p>
      </header>

      <main style={{ position: 'relative' }}>
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
      </main>
      
      <footer style={{ textAlign: 'center', marginTop: 'auto', paddingTop: '3rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
        Desarrollado para evaluación técnica
      </footer>
    </div>
  );
};

export default App;
