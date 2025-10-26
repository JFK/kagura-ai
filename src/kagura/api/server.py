"""Kagura Memory API Server.

FastAPI-based REST API for Universal AI Memory Management.

v4.0.0+ - MCP-First Architecture
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kagura.api import models
from kagura.api.routes import memory, search, system

# FastAPI app
app = FastAPI(
    title="Kagura Memory API",
    description="Universal AI Memory & Context Platform (MCP-native)",
    version="4.0.0a0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])


# Root endpoint
@app.get("/", response_model=models.RootResponse)
async def root() -> dict[str, Any]:
    """Root endpoint - API information."""
    return {
        "name": "Kagura Memory API",
        "version": "4.0.0a0",
        "status": "active",
        "docs": "/docs",
        "description": "Universal AI Memory & Context Platform (MCP-native)",
    }


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Any, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )
