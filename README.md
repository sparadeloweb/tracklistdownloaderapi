## SoundCloud Downloader API

Backend simple con FastAPI que envuelve `scdl` para descargar canciones de SoundCloud (individual o listado) y devolver el archivo al frontend.

Basado en `scdl` [scdl-org/scdl](https://github.com/scdl-org/scdl).

### Requisitos

- Python 3.10+
- ffmpeg instalado y en el PATH (necesario para conversiones)
  - Windows: `winget install Gyan.FFmpeg` o `choco install ffmpeg`

### Instalación y ejecución

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Endpoints

- POST `/download?url=...&format=mp3|opus|original` → devuelve el archivo de audio.
- POST `/download/batch` con body

```json
{
  "urls": ["https://soundcloud.com/...", "https://soundcloud.com/..."],
  "format": "mp3"
}
```

Devuelve un `tracks_bundle.zip` con todos los audios.

### Notas

- CORS está habilitado (permitiendo todos los orígenes) para facilitar el desarrollo.
- Si `scdl` necesita convertir formatos, asegura que `ffmpeg` esté correctamente instalado.


