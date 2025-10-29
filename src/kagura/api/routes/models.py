"""Model management API endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/models", tags=["models"])


class RerankInstallRequest(BaseModel):
    """Request to install reranking model"""

    model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model identifier",
    )


class RerankStatusResponse(BaseModel):
    """Reranking model status"""

    installed: bool = Field(description="Whether model is cached")
    model: str = Field(description="Model identifier")
    enabled: bool = Field(description="Whether reranking is enabled")


@router.get("/reranker/status", response_model=RerankStatusResponse)
async def get_reranker_status():
    """Check reranking model installation status

    Returns:
        Status of reranker model availability
    """
    from kagura.config.memory_config import MemorySystemConfig
    from kagura.core.memory.reranker import is_reranker_available

    config = MemorySystemConfig()
    model = config.rerank.model
    installed = is_reranker_available(model)

    return RerankStatusResponse(
        installed=installed,
        model=model,
        enabled=config.rerank.enabled or installed,  # Auto-enable if cached
    )


@router.post("/reranker/install")
async def install_reranker(request: RerankInstallRequest):
    """Install semantic reranking model

    Downloads and caches the cross-encoder model. First-time download
    may take 2-5 minutes depending on connection speed.

    Args:
        request: Installation request with model identifier

    Returns:
        Installation status and message

    Raises:
        HTTPException: If installation fails
    """
    from kagura.core.memory.reranker import is_reranker_available

    # Check if already cached
    if is_reranker_available(request.model):
        return {
            "status": "already_installed",
            "model": request.model,
            "message": "Model is already cached and ready to use",
        }

    # Check sentence-transformers
    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        raise HTTPException(
            status_code=400,
            detail="sentence-transformers not installed",
        )

    # Download model
    try:
        _ = CrossEncoder(request.model)

        return {
            "status": "installed",
            "model": request.model,
            "message": "Model downloaded and cached successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download model: {str(e)}"
        )
