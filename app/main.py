from __future__ import annotations

import mimetypes
import shutil
import tempfile
from pathlib import Path
from typing import List, Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, HttpUrl

from .scdl_wrapper import cleanup_directory, run_scdl
import os


app = FastAPI(title="SoundCloud Downloader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BatchRequest(BaseModel):
    urls: List[HttpUrl]
    format: Literal["mp3", "opus", "original"] = "mp3"


@app.get("/")
def root() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/download")
def download_single(
    background_tasks: BackgroundTasks,
    url: HttpUrl = Query(..., description="SoundCloud track/playlist/user URL"),
    format: Literal["mp3", "opus", "original"] = Query(
        "mp3", description="Preferred audio format"
    ),
):
    tmp_root = Path(tempfile.mkdtemp(prefix="scdl_api_"))
    try:
        only_mp3 = format == "mp3"
        prefer_opus = format == "opus"
        # If format is original, we do not constrain scdl; requires auth token
        auth_token = os.getenv("SCDL_AUTH_TOKEN")
        files = run_scdl(
            str(url),
            output_parent_dir=tmp_root,
            only_mp3=only_mp3,
            prefer_opus=prefer_opus,
            auth_token=auth_token,
        )

        # Pick most recent audio file
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        audio_path = files[0]

        # Schedule cleanup after the response is sent
        background_tasks.add_task(cleanup_directory, tmp_root)

        mime, _ = mimetypes.guess_type(audio_path.name)
        return FileResponse(
            path=str(audio_path),
            media_type=mime or "application/octet-stream",
            filename=audio_path.name,
        )
    except Exception as exc:  # noqa: BLE001
        cleanup_directory(tmp_root)
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/download/batch")
def download_batch(background_tasks: BackgroundTasks, req: BatchRequest):
    if not req.urls:
        raise HTTPException(status_code=422, detail="'urls' cannot be empty")

    tmp_root = Path(tempfile.mkdtemp(prefix="scdl_api_batch_"))
    download_dir = tmp_root / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)

    try:
        for url in req.urls:
            subdir = download_dir / ("item_" + str(abs(hash(str(url)))))
            subdir.mkdir(parents=True, exist_ok=True)

            only_mp3 = req.format == "mp3"
            prefer_opus = req.format == "opus"

            run_scdl(
                str(url),
                output_parent_dir=subdir,
                only_mp3=only_mp3,
                prefer_opus=prefer_opus,
                auth_token=os.getenv("SCDL_AUTH_TOKEN"),
            )

        archive_base = tmp_root / "tracks_bundle"
        archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=download_dir)

        background_tasks.add_task(cleanup_directory, tmp_root)
        return FileResponse(
            path=archive_path,
            media_type="application/zip",
            filename="tracks_bundle.zip",
        )
    except Exception as exc:  # noqa: BLE001
        cleanup_directory(tmp_root)
        raise HTTPException(status_code=400, detail=str(exc))


