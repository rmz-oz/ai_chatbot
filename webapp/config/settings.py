from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-secret-key")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

WSGI_APPLICATION = "config.wsgi.application"

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# LightRAG / Ollama
OLLAMA_URL  = config("OLLAMA_URL",  default="http://localhost:11434")
LLM_MODEL   = config("LLM_MODEL",   default="gemma4:e4b")
EMBED_MODEL = config("EMBED_MODEL", default="nomic-embed-text")

GEMINI_API_KEY = config("GEMINI_API_KEY", default="")

LIGHTRAG_STORAGE_DIR = str(BASE_DIR / "lightrag_storage")
