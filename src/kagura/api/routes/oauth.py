"""OAuth2 Server endpoints for ChatGPT MCP integration.

Issue #674 - OAuth2 authentication support for ChatGPT MCP integration

Provides OAuth2 authorization server endpoints:
1. GET /oauth/authorize - Authorization endpoint (user consent)
2. POST /oauth/token - Token endpoint (code exchange, refresh)
3. POST /oauth/revoke - Token revocation endpoint

Supported Grants:
- Authorization Code Grant (RFC 6749 Section 4.1)
- Refresh Token Grant (RFC 6749 Section 6)
- PKCE Extension (RFC 7636 - for public clients)

Security:
- CSRF protection via state parameter
- Authorization codes expire in 10 minutes
- Access tokens expire in 1 hour (configurable)
- Client secret validation
- PKCE support for public clients
"""

import logging
import os
import secrets
from datetime import datetime
from typing import Annotated

from authlib.oauth2 import OAuth2Request
from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from kagura.auth.models import User, get_session
from kagura.auth.oauth2_models import OAuth2Client
from kagura.auth.oauth2_server import create_authorization_server
from kagura.auth.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth2", tags=["oauth2-server"])

# Global session manager (initialized on server startup)
_session_manager: SessionManager | None = None


def initialize_oauth_routes(session_manager: SessionManager) -> None:
    """Initialize OAuth2 routes with session manager.

    Args:
        session_manager: Session manager instance for user authentication
    """
    global _session_manager
    _session_manager = session_manager


# ============================================================================
# Dependency: Get current authenticated user
# ============================================================================


async def get_current_user_from_session(request: Request) -> User:
    """Get current authenticated user from session.

    Used for authorization consent screen.

    Args:
        request: FastAPI request

    Returns:
        User object

    Raises:
        HTTPException: If user not authenticated
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized",
        )

    # Get session cookie
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login first.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate session
    session_data = _session_manager.get_session(session_id)  # Not async
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    # Get user from database
    db_session = get_session()
    try:
        # Session data has 'email' or 'sub' key, not 'user_id'
        user_identifier = session_data.get("email") or session_data.get("sub")
        if not user_identifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session data missing user identifier",
            )

        user = (
            db_session.query(User)
            .filter_by(email=user_identifier)
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
    finally:
        db_session.close()


CurrentUser = Annotated[User, Depends(get_current_user_from_session)]


# ============================================================================
# Models
# ============================================================================


class AuthorizeParams(BaseModel):
    """OAuth2 authorization request parameters."""

    client_id: str
    redirect_uri: str
    response_type: str = "code"
    scope: str | None = None
    state: str | None = None
    code_challenge: str | None = None  # PKCE
    code_challenge_method: str | None = None  # PKCE


class TokenResponse(BaseModel):
    """OAuth2 token response."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str | None = None
    scope: str | None = None


# ============================================================================
# OAuth2 Client Management Models
# ============================================================================


class OAuth2ClientResponse(BaseModel):
    """OAuth2 Client response (without secret)."""

    id: int
    client_id: str
    client_name: str
    redirect_uris: list[str]
    grant_types: list[str]
    response_types: list[str]
    scope: str
    token_endpoint_auth_method: str
    created_at: datetime

    class Config:
        from_attributes = True


class OAuth2ClientWithSecretResponse(OAuth2ClientResponse):
    """OAuth2 Client response with client secret (only on creation)."""

    client_secret: str


class OAuth2ClientCreateRequest(BaseModel):
    """OAuth2 Client creation request."""

    client_name: str = Field(..., min_length=1, max_length=100, description="Human-readable client name")
    redirect_uris: list[str] = Field(..., min_items=1, description="Allowed redirect URIs")
    grant_types: list[str] = Field(
        default=["authorization_code", "refresh_token"],
        description="Allowed grant types"
    )
    response_types: list[str] = Field(default=["code"], description="Allowed response types")
    scope: str = Field(
        default="mcp:tools mcp:memory mcp:coding",
        description="Space-separated scopes"
    )
    token_endpoint_auth_method: str = Field(
        default="client_secret_post",
        description="Client authentication method"
    )


class OAuth2ClientUpdateRequest(BaseModel):
    """OAuth2 Client update request."""

    client_name: str | None = Field(None, min_length=1, max_length=100)
    redirect_uris: list[str] | None = Field(None, min_items=1)
    scope: str | None = None


class OAuth2ProviderResponse(BaseModel):
    """OAuth2 Provider response."""

    name: str
    display_name: str
    client_id: str | None
    authorization_url: str
    token_url: str
    scopes: list[str]
    enabled: bool


# ============================================================================
# OAuth2 Endpoints
# ============================================================================


@router.get("/authorize", response_class=HTMLResponse)
async def authorize(
    request: Request,
    client_id: str = Query(..., description="OAuth2 client ID"),
    redirect_uri: str = Query(..., description="Callback URL"),
    response_type: str = Query("code", description="Must be 'code'"),
    scope: str | None = Query(None, description="Requested scope"),
    state: str | None = Query(None, description="CSRF state token"),
    code_challenge: str | None = Query(None, description="PKCE code challenge"),
    code_challenge_method: str | None = Query(None, description="PKCE method (S256/plain)"),
    user: CurrentUser = None,
) -> HTMLResponse:
    """OAuth2 authorization endpoint (user consent screen).

    Flow:
        1. Client (ChatGPT) redirects user here
        2. User sees consent screen (client name, requested permissions)
        3. User approves → authorization code issued
        4. User denies → error returned to redirect_uri

    Args:
        request: FastAPI request
        client_id: OAuth2 client identifier
        redirect_uri: Callback URL
        response_type: Must be "code" (authorization code grant)
        scope: Requested permissions (space-separated)
        state: CSRF protection token (recommended)
        code_challenge: PKCE code challenge (for public clients)
        code_challenge_method: PKCE method ("S256" or "plain")
        user: Current authenticated user (from session)

    Returns:
        HTML consent screen or redirect with authorization code

    Example:
        GET /oauth/authorize?client_id=chatgpt&redirect_uri=https://...&state=xyz
        → Shows consent screen
        → User approves
        → Redirects to: https://...?code=ABC123&state=xyz
    """
    db_session = get_session()
    try:
        # Create OAuth2 server
        server = create_authorization_server(db_session)

        # Convert FastAPI request to OAuth2Request
        oauth_request = OAuth2Request(
            request.method,
            str(request.url),
            dict(request.query_params),  # Use positional argument instead of 'data='
            dict(request.headers),
        )

        # Validate authorization request (Authlib v1.3+: renamed from validate_consent_request)
        try:
            grant = server.get_consent_grant(request=oauth_request)
        except Exception as e:
            import traceback
            logger.error(f"Authorization request validation failed: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid authorization request: {str(e)}",
            )

        # Get client info
        client = grant.client

        # Render consent screen (simplified HTML for MVP)
        # TODO: Replace with proper template in Phase 3
        consent_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorize {client.client_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; }}
                .client-name {{ font-weight: bold; color: #0066cc; }}
                .permissions {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 4px; }}
                .buttons {{ margin-top: 30px; display: flex; gap: 10px; }}
                button {{ padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
                .approve {{ background: #0066cc; color: white; }}
                .deny {{ background: #ccc; color: #333; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Authorize Access</h1>
                <p><span class="client-name">{client.client_name}</span> wants to access your Kagura AI Memory.</p>

                <div class="permissions">
                    <strong>Requested Permissions:</strong>
                    <ul>
                        {"".join(f"<li>{s}</li>" for s in (scope or client.scope).split())}
                    </ul>
                </div>

                <p><strong>User:</strong> {user.email}</p>

                <div class="buttons">
                    <form method="POST" action="/api/v1/oauth/authorize" style="display: inline;">
                        <input type="hidden" name="client_id" value="{client_id}">
                        <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                        <input type="hidden" name="response_type" value="{response_type}">
                        <input type="hidden" name="scope" value="{scope or ''}">
                        <input type="hidden" name="state" value="{state or ''}">
                        <input type="hidden" name="code_challenge" value="{code_challenge or ''}">
                        <input type="hidden" name="code_challenge_method" value="{code_challenge_method or ''}">
                        <input type="hidden" name="confirm" value="yes">
                        <button type="submit" class="approve">Approve</button>
                    </form>
                    <form method="POST" action="/api/v1/oauth/authorize" style="display: inline;">
                        <input type="hidden" name="client_id" value="{client_id}">
                        <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                        <input type="hidden" name="state" value="{state or ''}">
                        <input type="hidden" name="confirm" value="no">
                        <button type="submit" class="deny">Deny</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=consent_html)

    finally:
        db_session.close()


@router.post("/authorize")
async def authorize_post(
    request: Request,
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form("code"),
    scope: str | None = Form(None),
    state: str | None = Form(None),
    code_challenge: str | None = Form(None),
    code_challenge_method: str | None = Form(None),
    confirm: str = Form(...),
    user: CurrentUser = None,
) -> RedirectResponse:
    """Process authorization consent (approve/deny).

    Args:
        request: FastAPI request
        client_id: OAuth2 client ID
        redirect_uri: Callback URL
        response_type: Must be "code"
        scope: Requested scope
        state: CSRF state token
        code_challenge: PKCE challenge
        code_challenge_method: PKCE method
        confirm: "yes" (approve) or "no" (deny)
        user: Current authenticated user

    Returns:
        Redirect to redirect_uri with code (approved) or error (denied)
    """
    db_session = get_session()
    try:
        # User denied
        if confirm != "yes":
            error_url = f"{redirect_uri}?error=access_denied"
            if state:
                error_url += f"&state={state}"
            logger.info(f"User {user.email} denied authorization for client {client_id}")
            return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)

        # Create OAuth2 server
        server = create_authorization_server(db_session)

        # Convert FastAPI request to OAuth2Request
        form_data = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "scope": scope or "",
            "state": state or "",
            "code_challenge": code_challenge or "",
            "code_challenge_method": code_challenge_method or "",
        }

        oauth_request = OAuth2Request(
            "POST",
            str(request.url),
            form_data,  # Use positional argument instead of 'data='
            dict(request.headers),
        )

        # Generate authorization code
        try:
            response_data = server.create_authorization_response(oauth_request, grant_user=user)

            # Extract redirect URL from response
            if hasattr(response_data, "location"):
                redirect_url = response_data.location
            else:
                # Fallback: manual construction
                code = secrets.token_urlsafe(32)
                redirect_url = f"{redirect_uri}?code={code}"
                if state:
                    redirect_url += f"&state={state}"

            logger.info(
                f"Authorization approved: user={user.email}, client={client_id}, "
                f"scope={scope or 'default'}"
            )

            return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

        except Exception as e:
            logger.error(f"Authorization failed: {e}")
            error_url = f"{redirect_uri}?error=server_error&error_description={str(e)}"
            if state:
                error_url += f"&state={state}"
            return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)

    finally:
        db_session.close()


@router.post("/token", response_model=TokenResponse)
async def token(
    request: Request,
    grant_type: str = Form(..., description="authorization_code or refresh_token"),
    code: str | None = Form(None, description="Authorization code (for authorization_code grant)"),
    redirect_uri: str | None = Form(None, description="Redirect URI (must match authorization)"),
    client_id: str = Form(..., description="OAuth2 client ID"),
    client_secret: str | None = Form(None, description="Client secret (for confidential clients)"),
    refresh_token: str | None = Form(None, description="Refresh token (for refresh_token grant)"),
    code_verifier: str | None = Form(None, description="PKCE code verifier"),
) -> TokenResponse:
    """OAuth2 token endpoint (code exchange, token refresh).

    Supported Grants:
        1. authorization_code: Exchange code for access token
        2. refresh_token: Refresh access token using refresh token

    Args:
        request: FastAPI request
        grant_type: Grant type ("authorization_code" or "refresh_token")
        code: Authorization code (required for authorization_code grant)
        redirect_uri: Redirect URI (must match authorization request)
        client_id: OAuth2 client ID
        client_secret: Client secret (required for confidential clients)
        refresh_token: Refresh token (required for refresh_token grant)
        code_verifier: PKCE code verifier (required if PKCE used)

    Returns:
        Token response with access_token, refresh_token, expires_in

    Example (Authorization Code):
        POST /oauth/token
        grant_type=authorization_code&code=ABC123&redirect_uri=...&client_id=...&client_secret=...

        Response: {
            "access_token": "...",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "...",
            "scope": "mcp:tools mcp:memory"
        }

    Example (Refresh Token):
        POST /oauth/token
        grant_type=refresh_token&refresh_token=...&client_id=...&client_secret=...

        Response: {
            "access_token": "...",  # New access token
            "token_type": "Bearer",
            "expires_in": 3600
        }
    """
    db_session = get_session()
    try:
        # Create OAuth2 server
        server = create_authorization_server(db_session)

        # Prepare form data
        form_data = {
            "grant_type": grant_type,
            "client_id": client_id,
        }

        # Authorization code grant
        if grant_type == "authorization_code":
            if not code or not redirect_uri:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="code and redirect_uri required for authorization_code grant",
                )
            form_data["code"] = code
            form_data["redirect_uri"] = redirect_uri
            if code_verifier:  # PKCE
                form_data["code_verifier"] = code_verifier

        # Refresh token grant
        elif grant_type == "refresh_token":
            if not refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="refresh_token required for refresh_token grant",
                )
            form_data["refresh_token"] = refresh_token

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported grant_type: {grant_type}",
            )

        # Client authentication
        if client_secret:
            form_data["client_secret"] = client_secret

        # Convert to OAuth2Request
        oauth_request = OAuth2Request(
            "POST",
            str(request.url),
            form_data,  # Use positional argument instead of 'data='
            dict(request.headers),
        )

        # Issue token
        try:
            response_data = server.create_token_response(oauth_request)

            # Extract token data
            if hasattr(response_data, "body"):
                import json
                token_data = json.loads(response_data.body)
            else:
                # Fallback (should not happen)
                raise ValueError("Invalid token response format")

            logger.info(
                f"Token issued: grant_type={grant_type}, client={client_id}, "
                f"expires_in={token_data.get('expires_in')}s"
            )

            return TokenResponse(**token_data)

        except Exception as e:
            logger.error(f"Token issuance failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token request failed: {str(e)}",
            )

    finally:
        db_session.close()


@router.post("/revoke")
async def revoke(
    request: Request,
    token: str = Form(..., description="Token to revoke (access_token or refresh_token)"),
    token_type_hint: str | None = Form(None, description="Token type hint (access_token/refresh_token)"),
    client_id: str = Form(..., description="OAuth2 client ID"),
    client_secret: str | None = Form(None, description="Client secret"),
) -> JSONResponse:
    """OAuth2 token revocation endpoint (RFC 7009).

    Revokes access tokens or refresh tokens.

    Args:
        request: FastAPI request
        token: Token to revoke
        token_type_hint: Token type ("access_token" or "refresh_token")
        client_id: OAuth2 client ID
        client_secret: Client secret (for confidential clients)

    Returns:
        Empty response (200 OK)

    Example:
        POST /oauth/revoke
        token=...&token_type_hint=access_token&client_id=...&client_secret=...

        Response: 200 OK (empty)
    """
    db_session = get_session()
    try:
        from kagura.auth.oauth2_models import OAuth2Client, OAuth2Token

        # Validate client
        client = db_session.query(OAuth2Client).filter_by(client_id=client_id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client_id",
            )

        # Validate client secret (if provided)
        if client.has_client_secret():
            if not client_secret or not client.check_client_secret(client_secret):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid client_secret",
                )

        # Find token
        oauth_token = None
        if token_type_hint == "refresh_token":
            oauth_token = (
                db_session.query(OAuth2Token)
                .filter_by(refresh_token=token, client_id=client_id)
                .first()
            )
        else:
            # Try access_token first, then refresh_token
            oauth_token = (
                db_session.query(OAuth2Token)
                .filter_by(access_token=token, client_id=client_id)
                .first()
            )
            if not oauth_token:
                oauth_token = (
                    db_session.query(OAuth2Token)
                    .filter_by(refresh_token=token, client_id=client_id)
                    .first()
                )

        # Revoke token if found
        if oauth_token:
            if token_type_hint == "refresh_token" or oauth_token.refresh_token == token:
                oauth_token.refresh_token_revoked_at = datetime.utcnow()
            else:
                oauth_token.access_token_revoked_at = datetime.utcnow()

            oauth_token.revoked = True
            db_session.commit()

            logger.info(
                f"Token revoked: client={client_id}, "
                f"type={token_type_hint or 'unknown'}"
            )
        else:
            # RFC 7009: Return 200 even if token not found (don't leak info)
            logger.warning(f"Token not found for revocation: client={client_id}")

        return JSONResponse(content={}, status_code=status.HTTP_200_OK)

    finally:
        db_session.close()


# ============================================================================
# OAuth2 Client Management Endpoints
# ============================================================================


@router.get("/clients", response_model=list[OAuth2ClientResponse])
async def list_oauth2_clients(
    request: Request,
) -> list[OAuth2ClientResponse]:
    """List all registered OAuth2 clients.

    Returns:
        List of OAuth2 clients (without secrets)

    Example:
        GET /api/v1/oauth/clients
    """
    db_session = get_session()

    try:
        clients = db_session.query(OAuth2Client).order_by(OAuth2Client.created_at.desc()).all()

        return [OAuth2ClientResponse.model_validate(client) for client in clients]

    finally:
        db_session.close()


@router.post("/clients", response_model=OAuth2ClientWithSecretResponse, status_code=status.HTTP_201_CREATED)
async def create_oauth2_client(
    request: Request,
    data: OAuth2ClientCreateRequest,
) -> OAuth2ClientWithSecretResponse:
    """Register a new OAuth2 client.

    Args:
        data: Client registration data

    Returns:
        Created client with client_secret (only shown once)

    Example:
        POST /api/v1/oauth/clients
        {
          "client_name": "My App",
          "redirect_uris": ["https://example.com/callback"]
        }
    """
    import hashlib

    db_session = get_session()

    try:
        # Generate client_id and client_secret
        client_id = f"oauth_{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32)
        client_secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

        # Create OAuth2Client
        client = OAuth2Client(
            client_id=client_id,
            client_secret_hash=client_secret_hash,
            client_name=data.client_name,
            redirect_uris=data.redirect_uris,
            grant_types=data.grant_types,
            response_types=data.response_types,
            scope=data.scope,
            token_endpoint_auth_method=data.token_endpoint_auth_method,
        )

        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)

        logger.info(f"OAuth2 client created: {client_id} ({data.client_name})")

        # Return response with client_secret (only shown once)
        response_data = OAuth2ClientResponse.model_validate(client).model_dump()
        response_data["client_secret"] = client_secret

        return OAuth2ClientWithSecretResponse(**response_data)

    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to create OAuth2 client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create OAuth2 client: {str(e)}",
        )

    finally:
        db_session.close()


@router.get("/clients/{client_id}", response_model=OAuth2ClientResponse)
async def get_oauth2_client(
    request: Request,
    client_id: str,
) -> OAuth2ClientResponse:
    """Get OAuth2 client details.

    Args:
        client_id: OAuth2 client ID

    Returns:
        Client details (without secret)

    Example:
        GET /api/v1/oauth/clients/oauth_abc123
    """
    db_session = get_session()

    try:
        client = db_session.query(OAuth2Client).filter_by(client_id=client_id).first()

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth2 client not found: {client_id}",
            )

        return OAuth2ClientResponse.model_validate(client)

    finally:
        db_session.close()


@router.put("/clients/{client_id}", response_model=OAuth2ClientResponse)
async def update_oauth2_client(
    request: Request,
    client_id: str,
    data: OAuth2ClientUpdateRequest,
) -> OAuth2ClientResponse:
    """Update OAuth2 client.

    Args:
        client_id: OAuth2 client ID
        data: Update data

    Returns:
        Updated client

    Example:
        PUT /api/v1/oauth/clients/oauth_abc123
        {
          "client_name": "My App (Updated)",
          "redirect_uris": ["https://example.com/callback", "https://example.com/callback2"]
        }
    """
    db_session = get_session()

    try:
        client = db_session.query(OAuth2Client).filter_by(client_id=client_id).first()

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth2 client not found: {client_id}",
            )

        # Update fields
        if data.client_name is not None:
            client.client_name = data.client_name

        if data.redirect_uris is not None:
            client.redirect_uris = data.redirect_uris

        if data.scope is not None:
            client.scope = data.scope

        db_session.commit()
        db_session.refresh(client)

        logger.info(f"OAuth2 client updated: {client_id}")

        return OAuth2ClientResponse.model_validate(client)

    except HTTPException:
        db_session.rollback()
        raise

    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to update OAuth2 client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update OAuth2 client: {str(e)}",
        )

    finally:
        db_session.close()


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_oauth2_client(
    request: Request,
    client_id: str,
) -> None:
    """Delete OAuth2 client.

    Args:
        client_id: OAuth2 client ID

    Returns:
        No content

    Example:
        DELETE /api/v1/oauth/clients/oauth_abc123
    """
    db_session = get_session()

    try:
        client = db_session.query(OAuth2Client).filter_by(client_id=client_id).first()

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth2 client not found: {client_id}",
            )

        db_session.delete(client)
        db_session.commit()

        logger.info(f"OAuth2 client deleted: {client_id}")

    except HTTPException:
        db_session.rollback()
        raise

    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to delete OAuth2 client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete OAuth2 client: {str(e)}",
        )

    finally:
        db_session.close()


# ============================================================================
# OAuth2 Provider Management Endpoints
# ============================================================================


@router.get("/providers", response_model=list[OAuth2ProviderResponse])
async def list_oauth2_providers(
    request: Request,
) -> list[OAuth2ProviderResponse]:
    """List configured OAuth2 providers.

    Returns:
        List of OAuth2 providers (Google, GitHub, etc.)

    Example:
        GET /api/v1/oauth/providers
    """
    providers: list[OAuth2ProviderResponse] = []

    # Google OAuth2 Provider
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    providers.append(
        OAuth2ProviderResponse(
            name="google",
            display_name="Google",
            client_id=google_client_id if google_client_id else None,
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid", "email", "profile"],
            enabled=bool(google_client_id and google_client_secret),
        )
    )

    # GitHub OAuth2 Provider (placeholder for future support)
    github_client_id = os.getenv("GITHUB_CLIENT_ID")
    github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")

    providers.append(
        OAuth2ProviderResponse(
            name="github",
            display_name="GitHub",
            client_id=github_client_id if github_client_id else None,
            authorization_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            scopes=["read:user", "user:email"],
            enabled=bool(github_client_id and github_client_secret),
        )
    )

    return providers
