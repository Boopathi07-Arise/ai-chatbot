from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

try:
    from fastapi.staticfiles import StaticFiles
except ImportError:
    StaticFiles = None  # type: ignore

from .database import engine, Base
from .routes.chat import router as chat_router

# Load environment variables — use explicit path to backend/.env
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(_env_path)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="AI Chatbot", version="1.0.0")

# CORS — allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes (must be registered BEFORE static file mount) ────
app.include_router(chat_router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# ── Serve Frontend Static Files (must come LAST) ─────────────────
# This catch-all mount must always be registered after all API routes
frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
)
if os.path.exists(frontend_dir) and os.listdir(frontend_dir):
    if StaticFiles:
        try:
            app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
        except RuntimeError as e:
            print(f"[WARNING] Could not mount static files: {e}. Ensure index.html exists in {frontend_dir}.")
    else:
        print("[WARNING] 'aiofiles' is not installed. Static files will NOT be served.")