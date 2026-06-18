# Análisis Detallado del Proyecto: Meeting Summary AI

El proyecto **Meeting Summary AI** es una aplicación cliente-servidor orientada a la estandarización y resumen inteligente de actas y transcripciones de reuniones corporativas o equipos de trabajo, utilizando modelos de Inteligencia Artificial (LLMs), específicamente Google Gemini.

A continuación, se presenta un desglose detallado de su arquitectura, tecnologías y funcionalidades.

---

## 1. Arquitectura General y Tecnologías

La aplicación está dividida en dos componentes principales: el Backend (API) y el Frontend (Interfaz de Usuario).

### Backend
Desarrollado en **Python**, provee los servicios API que consumen y procesan la información de los archivos de reuniones.
* **Framework Web:** [FastAPI](https://fastapi.tiangolo.com/), ideal por su rapidez y manejo automático de documentación (Swagger en `/docs`).
* **Servidor ASGI:** Uvicorn.
* **Procesamiento de Archivos:** Utiliza múltiples librerías para soportar diferentes formatos:
  * `PyMuPDF` para extraer texto de PDFs.
  * `python-docx` para documentos de Word (.docx).
  * `striprtf` para formatos de texto enriquecido (.rtf).
* **Inteligencia Artificial:** Utiliza el SDK `google-generativeai` para interactuar con el modelo **Gemini 2.0 Flash**.
* **Estructuración de Datos:** Usa `pydantic` para validación de esquemas y tipos en las peticiones.
* **Almacenamiento:** Orientado a guardar datos e historial en un directorio de almacenamiento local (`/storage`), preparado conceptualmente para integrarse con Google Drive.

### Frontend
Aplicación Single Page Application (SPA) desarrollada en **JavaScript/React**.
* **Empaquetador y Entorno:** [Vite](https://vitejs.dev/), garantizando arranques ultra rápidos en desarrollo.
* **Framework de UI:** React 18.
* **Iconografía:** `lucide-react`.

---

## 2. Flujo de Trabajo y Funcionalidades (Qué cumple el proyecto)

La plataforma permite a los usuarios transformar notas desordenadas o transcripciones en crudo de reuniones, en actas altamente estructuradas. Este flujo se divide en 3 fases visibles en la interfaz y gestionadas por el backend:

### Fase 1: Carga y Pre-análisis (`FileUpload.jsx` ➡️ `/upload`)
1. **Soporte Multi-formato:** El usuario puede subir archivos `.txt`, `.md`, `.docx`, `.pdf` o `.rtf` (hasta 25MB).
2. **Extracción Automática:** El sistema procesa el archivo, extrae el texto puro y evalúa su calidad o formato.
3. **Estimación de Costos y Tokens:** Antes de consultar la IA, el sistema calcula la cantidad de "tokens" que consumirá la transcripción (input/output) basándose en las tarifas de Gemini.

### Fase 2: Vista Previa de Costos (`CostPreview.jsx` ➡️ `/process/{id}`)
1. **Transparencia Financiera:** El usuario visualiza una estimación del costo (en USD) y la cantidad de tokens, así como un pequeño fragmento del texto extraído para confirmar que la extracción fue correcta.
2. **Confirmación:** Una vez el usuario aprueba la ejecución, la aplicación procede a procesar el texto con el LLM.

### Fase 3: Resumen y Estructuración Inteligente (`SummaryView.jsx`)
1. **Prompt Engineering Adaptativo:** El backend construye un contexto ("prompt") adaptándose a si el texto origen es una transcripción textual, notas sueltas u otro formato.
2. **Generación con Gemini:** El LLM analiza el texto y extrae forzosamente una estructura JSON con los siguientes campos:
   * Nombre y fecha de la reunión.
   * Participantes.
   * Objetivo principal.
   * Resumen Ejecutivo.
   * Temas discutidos.
   * Decisiones tomadas.
   * **Tareas pendientes** (con responsable y plazo).
   * Riesgos o bloqueos mencionados.
   * Próximos pasos.
3. **Persistencia y Exportación:**
   * El resumen se guarda en formato `.json`.
   * El backend cuenta con un generador automático que renderiza el resumen en un documento HTML muy pulido y profesional, listo para descargar o compartir por correo.

---

## 3. Estructura de Directorios Clave

### Backend (`/backend/app/`)
* **`main.py` & `config.py`:** Punto de entrada de FastAPI y manejo central de variables de entorno (API Keys, Cors, Límites).
* **`/routes/`:** 
  * `health.py`: Endpoints de salud del servidor.
  * `meetings.py`: Lógica de los endpoints de negocio (subir, procesar, listar, descargar resúmenes).
* **`/services/`:** Capa de lógica de negocio pura:
  * `llm_service.py`: Conexión con Gemini y parseo tolerante a fallos de respuestas JSON generadas por la IA.
  * `file_extractor.py`: Extracción de contenido de los PDFs, DOCX, etc.
  * `cost_estimator.py`: Lógica matemática para predecir costos de API.
  * `prompt_builder.py`: Constructor de los textos y directrices que se le envían a Gemini.
  * `storage_service.py`: Manejo del sistema de archivos donde se guarda el histórico.
* **`/models/`:** Modelos Pydantic que definen contratos y validan los datos.

### Frontend (`/frontend/src/`)
* **`App.jsx`:** Componente orquestador que mantiene el estado global (`upload` ➡️ `preview` ➡️ `result`).
* **`/components/`:** Los tres componentes visuales principales del flujo de negocio descritos en la sección 2.
* **`/services/`:** Probablemente contenga los clientes Axios o Fetch para hablar con el backend FastAPI.
* **`/styles/`:** Hojas de estilo CSS vainilla para darle apariencia moderna a la UI.

---

## 4. Conclusión y Valor Aportado

Este proyecto cumple la función de ser un **asistente ofimático inteligente**. Soluciona el problema de perder tiempo valioso estructurando minutas de reuniones:
1. **Estandariza** la salida (todas las reuniones terminan teniendo la misma estructura limpia).
2. **Previene omisiones** extrayendo inteligentemente quién debe hacer qué tarea y qué se decidió.
3. **Es consciente del costo** al transparentar el uso de tokens antes de incurrir en gastos de API de IA.
4. Posee un backend **robusto** y bien segmentado, capaz de escalar para soportar guardado en nube como Google Drive en un futuro.
