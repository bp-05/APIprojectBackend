/**
 * Ejemplo de integración del sistema de exportaciones desde el frontend
 * 
 * MANEJO DE DATOS FALTANTES:
 * - El sistema SIEMPRE genera un Excel válido, incluso con información parcial
 * - Los headers HTTP indican si hay datos faltantes:
 *   - X-Export-Status: 'complete' | 'partial'
 *   - X-Missing-Data-Count: número de campos faltantes
 */

// ============================================
// REACT / NEXT.JS EXAMPLE CON MANEJO DE DATOS FALTANTES
// ============================================

import { useState } from 'react';

export function ExportFichaAPIButton({ subjectId }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState(null);

  const handleExport = async () => {
    setLoading(true);
    setError(null);
    setWarning(null);

    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/exports/subjects/${subjectId}/ficha-api/`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al exportar');
      }

      // Verificar si hay datos faltantes
      const exportStatus = response.headers.get('X-Export-Status');
      const missingDataCount = response.headers.get('X-Missing-Data-Count');
      
      if (exportStatus === 'partial' && missingDataCount) {
        setWarning(
          `Nota: El archivo fue generado con información parcial. ` +
          `Faltan ${missingDataCount} campos por completar.`
        );
      }

      // Obtener el blob (archivo)
      const blob = await response.blob();
      
      // Crear URL temporal y descargar
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1].replace(/"/g, '')
        : `ficha_api_${subjectId}.xlsx`;
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (err) {
      setError(err.message);
      console.error('Error exportando:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button 
        onClick={handleExport} 
        disabled={loading}
        className="btn btn-primary"
      >
        {loading ? 'Exportando...' : 'Exportar Ficha API'}
      </button>
      {error && (
        <div className="alert alert-danger mt-2">{error}</div>
      )}
      {warning && (
        <div className="alert alert-warning mt-2">
          <strong>⚠️ Información parcial:</strong> {warning}
        </div>
      )}
    </div>
  );
}

// ============================================
// VANILLA JAVASCRIPT EXAMPLE
// ============================================

function exportFichaAPI(subjectId) {
  const token = localStorage.getItem('access_token');
  
  fetch(`http://localhost:8000/api/exports/subjects/${subjectId}/ficha-api/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })
  .then(response => {
    if (!response.ok) {
      return response.json().then(err => {
        throw new Error(err.detail || 'Error al exportar');
      });
    }
    return response.blob();
  })
  .then(blob => {
    // Crear enlace de descarga
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ficha_api_${subjectId}.xlsx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error al exportar: ' + error.message);
  });
}

// Uso:
// <button onclick="exportFichaAPI(1)">Exportar Ficha API</button>

// ============================================
// AXIOS EXAMPLE
// ============================================

import axios from 'axios';

async function exportFichaAPIWithAxios(subjectId) {
  try {
    const response = await axios.get(
      `/api/exports/subjects/${subjectId}/ficha-api/`,
      {
        responseType: 'blob', // Importante para archivos binarios
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      }
    );

    // Crear enlace de descarga
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    
    // Obtener nombre del archivo del header
    const contentDisposition = response.headers['content-disposition'];
    const filename = contentDisposition
      ? contentDisposition.split('filename=')[1].replace(/"/g, '')
      : `ficha_api_${subjectId}.xlsx`;
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    
    // Limpiar
    link.remove();
    window.URL.revokeObjectURL(url);
    
  } catch (error) {
    console.error('Error exportando:', error);
    throw error;
  }
}

// ============================================
// FETCH WITH PROGRESS (OPCIONAL)
// ============================================

async function exportWithProgress(subjectId, onProgress) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `http://localhost:8000/api/exports/subjects/${subjectId}/ficha-api/`,
    {
      headers: { 'Authorization': `Bearer ${token}` },
    }
  );

  if (!response.ok) {
    throw new Error('Error al exportar');
  }

  // Leer stream con progreso
  const contentLength = response.headers.get('content-length');
  const total = parseInt(contentLength, 10);
  let loaded = 0;

  const reader = response.body.getReader();
  const chunks = [];

  while (true) {
    const { done, value } = await reader.read();
    
    if (done) break;
    
    chunks.push(value);
    loaded += value.length;
    
    if (onProgress && total) {
      onProgress((loaded / total) * 100);
    }
  }

  // Combinar chunks
  const blob = new Blob(chunks);
  
  // Descargar
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ficha_api_${subjectId}.xlsx`;
  a.click();
  window.URL.revokeObjectURL(url);
}

// Uso:
// exportWithProgress(1, (progress) => {
//   console.log(`Descargando: ${progress.toFixed(2)}%`);
// });

// ============================================
// ERROR HANDLING MEJORADO
// ============================================

class ExportService {
  constructor(baseURL, getToken) {
    this.baseURL = baseURL;
    this.getToken = getToken;
  }

  async exportFichaAPI(subjectId) {
    try {
      const token = this.getToken();
      
      if (!token) {
        throw new Error('No estás autenticado');
      }

      const response = await fetch(
        `${this.baseURL}/api/exports/subjects/${subjectId}/ficha-api/`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.status === 403) {
        throw new Error('No tienes permisos para exportar esta asignatura');
      }

      if (response.status === 404) {
        throw new Error('Asignatura no encontrada');
      }

      if (response.status === 500) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error del servidor');
      }

      if (!response.ok) {
        throw new Error('Error desconocido al exportar');
      }

      const blob = await response.blob();
      
      // Verificar que sea un archivo Excel válido
      if (blob.type !== 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
        console.warn('Tipo de archivo inesperado:', blob.type);
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Ficha_API_${subjectId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      
      // Limpiar después de un pequeño delay
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);

      return { success: true };

    } catch (error) {
      console.error('Error en exportación:', error);
      return { 
        success: false, 
        error: error.message 
      };
    }
  }
}

// Uso:
// const exportService = new ExportService(
//   'http://localhost:8000',
//   () => localStorage.getItem('access_token')
// );
// 
// const result = await exportService.exportFichaAPI(1);
// if (!result.success) {
//   alert(result.error);
// }
