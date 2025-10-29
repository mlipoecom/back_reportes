from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import date
import bcrypt
from typing import Dict, Any
from ..mail import send_user_password_email
from ..models import UserGenerate, UserGenerateResponse
from ..utils import generate_safe_password
from ..database import get_pool


router = APIRouter(
    prefix="/administrativa",
    tags=["Administrativas"]
)


async def call_sp_insert_user(
    p_name: str,
    p_last_name: str,
    p_external_id: str,
    p_hashed_password: str,
    p_status: str,
    p_company: int,
    p_email: str
) -> Dict[str, Any]:
    p_creation_date = date.today()
    cursor_name = "user_insert_result"

    params = (
        p_name, p_last_name, p_external_id, p_hashed_password,
        p_creation_date, p_status, p_company, p_email, cursor_name
    )

    try:
        async with (await get_pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "CALL sp_insert_user($1,$2,$3,$4,$5,$6,$7,$8,$9);",
                    *params
                )
                rows = await conn.fetch(f'FETCH ALL IN "{cursor_name}";')
    except Exception as e:
        msg = str(e).split('\n')[0].strip()
        raise HTTPException(status_code=500, detail=f"Error en la BD: {msg}")

    if not rows:
        raise HTTPException(status_code=500, detail="SP no devolvió datos")

    return {
        "info": rows[0].get("info"),
        "id": rows[0].get("id", 0)
    }


@router.post(
    "/crear-usuario",
    summary="Crear usuario",
    description="Registrar un nuevo usuario de una empresa",
    response_model=UserGenerateResponse,
    responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Usuario creado exitosamente.",
                        "id": 1
                    }
                }
            },
        },
        400: {
            "description": "Ejecución fallida",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Ya existe un usuario con el mismo ID externo.",
                        "id": 0
                    }
                }
            },
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Error en la BD: conexión fallida",
                        "id": 0
                    }
                }
            },
        },
    }
)

async def generate_and_create_user(user_data: UserGenerate):
    try:
        password = generate_safe_password()
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"info": f"Error al generar contraseña: {e}", "password": "", "id": 0}
        )

    db_response = await call_sp_insert_user(
        user_data.name,
        user_data.lastName,
        user_data.externalId,
        hashed_password,
        user_data.status,
        user_data.companyId,
        user_data.email
    )

    if db_response["id"] == 0 or (
        db_response["info"] and "error" in db_response["info"].lower()
    ):
        return JSONResponse(
            status_code=400,
            content={
                "info": db_response["info"],
                "password": "",
                "id": 0
            }
        )

    try:
        send_user_password_email(
            user_email=user_data.email,
            full_name=f"{user_data.name} {user_data.lastName}",
            username=f"{user_data.externalId}",
            generated_password=password
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "info": f"Usuario creado pero no se pudo enviar el correo: {e}",
                "password": "",
                "id": db_response["id"]
            }
        )

    return UserGenerateResponse(
        info=db_response["info"],
        id=db_response["id"]
    )
