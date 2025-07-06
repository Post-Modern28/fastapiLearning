from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / "front"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)
