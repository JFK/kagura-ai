"""Kagura Memory API Server.

FastAPI-based REST API for Universal AI Memory Management.

v4.0.0+ - MCP-First Architecture
Issue #650: OAuth2, API Key Management, Config UI
Issue #653: PostgreSQL roles and audit logs
"""

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kagura.api import models
from kagura.api.routes import coding, graph, memory, search, system
from kagura.api.routes import models as models_routes
from kagura.api.routes.mcp_transport import mcp_asgi_app

logger = logging.getLogger(__name__)

# Issue #650: OAuth2 and Config Management
# Issue #653: Audit logs
# Issue #655: API Keys management
# Issue #674: OAuth2 Server for ChatGPT integration
try:
    from kagura.api.routes import api_keys, audit, auth, config, oauth
    from kagura.api.middleware.session import SessionMiddleware
    from kagura.auth.session import SessionManager
    from kagura.auth.roles import initialize_role_manager
    from kagura.config.env_manager import get_env_manager

    AUTH_AVAILABLE = True
except ImportError as e:
    AUTH_AVAILABLE = False
    print(f"Warning: Auth routes not available: {e}")

# FastAPI app
app = FastAPI(
    title="Kagura Memory API",
    description="Universal AI Memory Platform (MCP + ChatGPT)",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MCP (ChatGPT, Claude, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug middleware to log all requests
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f">>> Incoming request: {request.method} {request.url.path}")
        logger.info(f">>> Headers: {dict(request.headers)}")
        try:
            response = await call_next(request)
            logger.info(f"<<< Response status: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"<<< Request failed: {e}", exc_info=True)
            raise

app.add_middleware(RequestLoggingMiddleware)

# Issue #650: Session middleware for OAuth2 authentication
# Issue #653: Auto-run migrations on startup
if AUTH_AVAILABLE:
    redis_url = os.getenv("REDIS_URL")  # None if not explicitly set
    db_url = os.getenv("DATABASE_URL")

    try:
        # Run database migrations (Issue #653)
        if db_url:
            try:
                from kagura.auth.migrations.run_migrations import run_migrations

                logger.info("Running database migrations...")
                run_migrations(db_url)
                logger.info("Database migrations completed")
            except Exception as e:
                logger.warning(f"Migration failed (may already be applied): {e}")

        # Initialize session manager (requires Redis)
        if not redis_url:
            logger.warning("REDIS_URL not set - OAuth2 authentication disabled")
            raise ValueError("REDIS_URL required for OAuth2 authentication")

        session_manager = SessionManager(redis_url=redis_url)
        app.add_middleware(SessionMiddleware, session_manager=session_manager)

        # Initialize role manager with PostgreSQL
        if db_url:
            initialize_role_manager(db_url)

        # Initialize auth routes
        from kagura.api.routes.auth import initialize_auth_routes
        from kagura.api.routes.oauth import initialize_oauth_routes
        from kagura.auth.oauth2 import OAuth2Manager

        oauth2_manager = OAuth2Manager()
        initialize_auth_routes(oauth2_manager, session_manager)
        initialize_oauth_routes(session_manager)  # Issue #674

    except Exception as e:
        print(f"Warning: Auth initialization failed: {e}")

# Include routers
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(coding.router, prefix="/api/v1/coding", tags=["coding"])  # Issue #664
app.include_router(graph.router, prefix="/api/v1/graph", tags=["graph"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])
app.include_router(models_routes.router, prefix="/api/v1", tags=["models"])

# Issue #650: OAuth2 and Config management routes
# Issue #653: Audit logs
# Issue #655: API Keys management
# Issue #674: OAuth2 Server for ChatGPT MCP integration
if AUTH_AVAILABLE:
    app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
    app.include_router(oauth.router, prefix="/api/v1", tags=["oauth2-server"])  # Issue #674
    app.include_router(config.router, prefix="/api/v1", tags=["configuration"])
    app.include_router(audit.router, prefix="/api/v1", tags=["audit"])
    app.include_router(api_keys.router, prefix="/api/v1", tags=["api-keys"])

# MCP over HTTP/SSE (Phase C - ChatGPT Connector)
# Use Starlette Mount to avoid trailing slash redirect (Issue #668)
from starlette.routing import Mount
app.routes.append(Mount("/mcp", app=mcp_asgi_app, name="mcp"))


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
