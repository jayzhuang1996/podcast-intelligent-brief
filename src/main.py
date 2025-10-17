"""
FastAPI application entry point.

Run with: uvicorn src.main:app --reload
API docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.db.database import init_db
from src.api import summarize
from loguru import logger
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger.remove()  # Remove default handler
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level: <8} | {message}")

# Create FastAPI app
app = FastAPI(
    title="AI Podcast Monitor API",
    description="On-demand podcast summarization with personalization",
    version="1.0.0"
)

# CORS middleware (allow frontend to access backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize database on startup.

    Why here? Ensures tables exist before any requests.
    """
    logger.info("🚀 Starting AI Podcast Monitor API...")
    init_db()
    logger.info("✅ Database initialized")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "AI Podcast Monitor API is running"}


# Include routers
app.include_router(summarize.router, prefix="/api", tags=["Summarize"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "AI Podcast Monitor API - Intelligent Briefing System",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "summarize": "POST /api/summarize (with context)",
            "search": "GET /api/search",
            "history": "GET /api/history",
        }
    }
