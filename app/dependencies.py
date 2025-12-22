import httpx
from fastapi import Request, HTTPException, status

from app.auth.clerk import is_signed_in

async def require_signed_in_user(request: Request):
    httpx_request = httpx.Request(
        method=request.method,
        url=str(request.url),
        headers=request.headers,
    )

    if not is_signed_in(httpx_request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="UNAUTHORIZED",
        )
