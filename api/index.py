"""Vercel Serverless Function entry point.

Wraps the FastAPI app for Vercel's Python runtime.
Vercel routes all /api/* requests to this handler.
"""
import sys
import os

# Add backend to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app  # noqa: E402
