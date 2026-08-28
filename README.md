# Corrector Masivo de Tareas Universitarias

Aplicación local con interfaz web (Streamlit) para corregir masivamente entregas de estudiantes
(`.pdf` / `.docx`) contra una rúbrica dinámica, usando un LLM (Google Gemini o Anthropic Claude),
y generar un archivo Word (`.docx`) de feedback estructurado por cada entrega.

## Estructura del proyecto

```
revisor/
├── app.py                  # Interfaz principal en Streamlit
├── core/
│   ├── parser.py            # Extracción de texto desde .pdf y .docx
│   ├── evaluator.py          # Prompt, llamado al LLM y parsing estructurado (JSON)
│   └── docx_generator.py     # Generación del .docx de feedback
├── rubrics/                 # Rúbricas reutilizables (.md, .txt, .json)
├── requirements.txt
└── .env.example
```

## Instalación

1. Crea un entorno virtual (recomendado):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

2. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Copia `.env.example` a `.env` y agrega tu(s) API key(s):

   ```bash
   copy .env.example .env   # Windows
   cp .env.example .env     # macOS/Linux
   ```

   - `GEMINI_API_KEY`: clave gratuita desde https://aistudio.google.com/apikey
   - `ANTHROPIC_API_KEY`: clave desde https://console.anthropic.com/

   También puedes pegar la API key directamente en el panel lateral de la app sin usar `.env`.

## Ejecución

Un solo comando:

```bash
streamlit run app.py
```

Esto abrirá la aplicación en tu navegador (por defecto en `http://localhost:8501`).

## Uso

1. En el panel lateral, elige el proveedor (Gemini o Anthropic), ingresa la API key y el modelo.
2. Define la escala de notas (por defecto 1.0 a 7.0).
3. Selecciona una rúbrica desde `rubrics/` o pega/edita una rúbrica personalizada en el área de texto.
4. Sube un archivo `.zip` con las entregas de los estudiantes (`.pdf` o `.docx`).
5. Presiona **Corregir Entregas** y observa el progreso entrega por entrega.
6. Al finalizar, descarga el ZIP con todos los archivos `Feedback_[Nombre_Original].docx`.

## Notas de robustez

- Los archivos corruptos, ilegibles o de tipo no soportado se omiten y se reporta el error sin detener el resto del lote.
- Las llamadas al LLM reintentan automáticamente con backoff exponencial ante rate limits o errores transitorios.
- Las carpetas temporales de procesamiento se eliminan automáticamente al finalizar (éxito o error).
