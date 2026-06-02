import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
TRANSLATOR_API_BASE_URL = os.getenv(
    "TRANSLATOR_API_BASE_URL",
    "https://winfredkuo-translator.theoder.workers.dev",
).strip()

app = FastAPI(title="Instant Translation")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "translator.html",
        {
            "request": request,
            "translator_api_base_url": TRANSLATOR_API_BASE_URL,
        },
    )
