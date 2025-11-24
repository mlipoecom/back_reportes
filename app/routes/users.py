from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from datetime import date
import bcrypt
from typing import Dict, Any
from mail import send_user_password_email
from models import UserGenerate, UserGenerateResponse, AssignClientRequest
from utils import generate_safe_password, get_user_id_from_token
from database import get_pool
from models import AssignRolesRequest


router = APIRouter(
    prefix="/proveedor",
    tags=["Proveedores"]
)


async def call_sp_insert_user(
    p_name: str,
    p_last_name: str,
    p_external_id: str,
    p_hashed_password: str,
    p_status: str,
    p_supplier: str,
    p_company: int = None,
    p_customer: int = None,
    p_email: str = "",
    p_created_by = int
) -> Dict[str, Any]:
    p_creation_date = date.today()
    cursor_name = "user_insert_result"

    if p_company is None and p_customer is None and p_supplier is None:
        raise HTTPException(status_code=400, detail="Debe enviarse supplierId, companyId o customerId")

    db_supplier = p_supplier if p_supplier is not None else None
    db_company = p_company if p_company is not None else None
    db_customer = p_customer if p_customer is not None else None

    params = (
        p_name, p_last_name, p_external_id, p_hashed_password,
        p_creation_date, p_status, db_supplier, db_company, db_customer, p_email, p_created_by, cursor_name
    )

    try:
        async with (await get_pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "CALL sp_insert_user($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12);",
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
    "/usuario/crear",
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

async def generate_and_create_user(
    user_data: UserGenerate,
    authorization: str = Header(..., description="Bearer Token")):

    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    token = authorization
    user_id = get_user_id_from_token(token)

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
        p_supplier=user_data.supplierId if user_data.supplierId else None,
        p_company=user_data.companyId if user_data.companyId else None,
        p_customer=user_data.customerId if user_data.customerId else None,
        p_email=user_data.email,
        p_created_by=user_id
    )

    if db_response["id"] == 0 or (db_response["info"] and "error" in db_response["info"].lower()):
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

@router.post(
    "/asignar-roles",
    summary="Asignar roles",
    description="Asigna roles a un usuario o empresa",
    responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Roles asignados exitosamente",
                    }
                }
            },
        },
        400: {
            "description": "Ejecución fallida",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Error al asignar roles",
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
                    }
                }
            },
        },
    }
)  # Type: id: id del usuario  role_id: id del rol
async def assign_roles(
    payload: AssignRolesRequest,
    authorization: str = Header(..., description="Bearer Token")) -> str:

    pool = await get_pool()
    cursor_name = "assign_role_result"
    params = (payload.user_id, payload.role_id, cursor_name)
    
    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")
    
    async with pool.acquire() as conn:
        try:
            message = ""
            async with conn.transaction():
                await conn.execute("CALL sp_assign_role($1, $2, $3);", *params)

                rows = await conn.fetch(f'FETCH ALL IN "{cursor_name}";')

                if not rows:
                    raise HTTPException(status_code=500, detail="Error en la BD: SP no devolvió datos")

                message = rows[0].get("message")
                if not message:
                    raise HTTPException(status_code=500, detail="Error en la BD: respuesta inválida del SP")

                # Detectar errores según el texto del mensaje
                if any(word in message.lower() for word in ["error"]):
                    raise HTTPException(status_code=400, detail=message)

            return JSONResponse(status_code=200, content={"info": message})

        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
