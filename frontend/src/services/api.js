const API_BASE_URL = '/api/meetings';

export const api = {
  /**
   * Sube un archivo y recibe análisis de costos y extracción
   */
  async uploadFile(file, meetingName) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('meeting_name', meetingName);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al subir el archivo');
    }
    
    return response.json();
  },

  /**
   * Confirma el procesamiento usando Gemini
   */
  async processMeeting(meetingId) {
    const response = await fetch(`${API_BASE_URL}/process/${meetingId}`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error en el procesamiento');
    }
    
    return response.json();
  },

  /**
   * Obtiene la lista de reuniones procesadas
   */
  async getMeetings() {
    const response = await fetch(API_BASE_URL);
    if (!response.ok) throw new Error('Error al obtener historial');
    return response.json();
  },

  /**
   * Obtiene detalle de una reunión
   */
  async getMeeting(meetingId) {
    const response = await fetch(`${API_BASE_URL}/${meetingId}`);
    if (!response.ok) throw new Error('Error al obtener detalle de la reunión');
    return response.json();
  },

  /**
   * Descarga un resumen
   */
  async downloadSummary(meetingId, format) {
    const response = await fetch(`${API_BASE_URL}/${meetingId}/download/${format}`);
    if (!response.ok) throw new Error(`Error al descargar formato ${format}`);
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    const disposition = response.headers.get('content-disposition');
    let filename = `resumen.${format}`;
    if (disposition && disposition.indexOf('filename=') !== -1) {
      filename = disposition.split('filename=')[1].replace(/"/g, '');
    }
    
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
  }
};
