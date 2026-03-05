from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/dashboard", include_in_schema=False)
def dashboard() -> FileResponse:
    html_path = Path(__file__).resolve().parent / "dashboard.html"
    return FileResponse(html_path)


@router.get("/", include_in_schema=False)
def root_dashboard() -> FileResponse:
    html_path = Path(__file__).resolve().parent / "dashboard.html"
    return FileResponse(html_path)
