import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from src.services.spin_api import SpinBot

router = APIRouter(prefix="/auth", tags=["auth"])


class UserCredentials(BaseModel):
    email: EmailStr
    password: str


def _login_response_payload(bot: SpinBot) -> Dict[str, Any]:
    """Return a safe JSON body without leaking tokens."""
    payload: Dict[str, Any] = {
        "status": "success",
        "authenticated": True,
    }
    if bot.token_data:
        expires_in = bot.token_data.get("expires_in")
        token_type = bot.token_data.get("token_type")
        if expires_in is not None:
            payload["expires_in"] = expires_in
        if token_type is not None:
            payload["token_type"] = token_type
    return payload


@router.post("/login")
async def login(credentials: UserCredentials):
    bot = SpinBot(credentials.email, credentials.password)
    loop = asyncio.get_running_loop()
    ok = await loop.run_in_executor(None, bot.authenticate)
    if ok:
        return _login_response_payload(bot)
    detail: Optional[str] = bot.last_error or "Login failed"
    raise HTTPException(status_code=401, detail=detail)
