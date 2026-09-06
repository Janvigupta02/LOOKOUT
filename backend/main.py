from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

from database import init_db
from api import router
from auth.routes import router as auth_router
from utils import seed_database

# Load environment variables
load_dotenv()

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print("Initializing database...")
    init_db()
    
    # Seed database if needed
    try:
        seed_database()
    except Exception as e:
        print(f"Seeding info: {e}")
    
    yield
    
    # Shutdown (if needed in future)
    print("Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="MarketPulse API",
    description="Smart Market Watchlist - Know what changed. Know what matters.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth_router, prefix="/api")
app.include_router(router, prefix="/api")

def serve_template(template_name: str):
    """Serve HTML template"""
    template_path = os.path.join(os.path.dirname(__file__), 'templates', template_name)
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Template not found</h1>"

@app.get("/", response_class=HTMLResponse)
def root():
    """Serve combined auth page"""
    return serve_template('auth.html')

@app.get("/login", response_class=HTMLResponse)
def login_page():
    """Redirect to main auth page"""
    return '<script>window.location.href="/"</script>'

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    """Redirect to main auth page"""
    return '<script>window.location.href="/"</script>'

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    """Serve dashboard page"""
    return serve_template('dashboard.html')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)