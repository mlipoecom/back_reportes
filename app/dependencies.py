from typing import List, Callable
from fastapi import Header, HTTPException, Depends
from security import decode_token
from utils import get_token_from_header


def get_current_user(authorization: str = Header(..., description="Bearer Token")) -> dict:
    token = get_token_from_header(authorization)
    payload = decode_token(token)
    return payload


def require_roles(allowed_roles: List[int]) -> Callable:
    def role_checker(user_data: dict = Depends(get_current_user)) -> dict:
        user_role = user_data.get("role")

        if user_role is None:
            raise HTTPException(
                status_code=403,
                detail="No se pudo determinar el rol del usuario"
            )

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para acceder a este recurso"
            )

        return user_data

    return role_checker

