from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.supabase import get_supabase

bearer_scheme = HTTPBearer()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials

    try:
        supabase = get_supabase()
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
            )

        return response.user.id

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )