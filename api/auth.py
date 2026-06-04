from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings

_bearer = HTTPBearer(auto_error=False)


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> None:
    """
    Dependency that enforces bearer token authentication.
    Attach to any router or individual endpoint via Depends(require_auth).
    Returns 401 if the token is missing or incorrect.
    """
    if not settings.api_secret_key:
        # No key configured — fail closed, don't silently allow everything
        raise HTTPException(status_code=500, detail="API_SECRET_KEY is not configured.")

    if credentials is None or credentials.credentials != settings.api_secret_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
