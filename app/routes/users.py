from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import date
import bcrypt
from typing import Dict, Any
from mail import send_user_password_email
from models import UserGenerate, UserGenerateResponse, AssignClientRequest
from utils import generate_safe_password
from database import get_pool
from models import AssignRolesRequest
from dependencies import require_roles
from roles import UserRole


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


async def assign_role_to_user(user_id: int, role_id: int) -> None:
    print(f"assign_role_to_user called with user_id: {user_id}, role_id: {role_id}")
    pool = await get_pool()
    cursor_name = "assign_role_result"
    params = (user_id, role_id, cursor_name)

    async with pool.acquire() as conn:
        try:
            message = ""
            async with conn.transaction():
                await conn.execute("CALL sp_assign_role($1, $2, $3);", *params)

                rows = await conn.fetch(f'FETCH ALL IN "{cursor_name}";')

                if not rows:
                    raise HTTPException(status_code=500, detail="Error en la BD: SP no devolvió datos")

                message = rows[0].get("message")
                print(f"SP message: {message}")
                if not message:
                    raise HTTPException(status_code=500, detail="Error en la BD: respuesta inválida del SP")

                # Detectar errores según el texto del mensaje
                if any(word in message.lower() for word in ["error"]):
                    raise HTTPException(status_code=400, detail=message)

        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


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
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))):
    print(f"user_data: {user_data}")
    role_name_to_id = {
        "super_admin": UserRole.SUPER_ADMIN,
        "supplier_admin": UserRole.SUPPLIER_ADMIN,
        "customer_admin": UserRole.CUSTOMER_ADMIN,
        "customer_user": UserRole.CUSTOMER_USER,
        "company_admin": UserRole.COMPANY_ADMIN,
        "company_user": UserRole.COMPANY_USER,
    }
    user_id = current_user.get("ID")

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
    
    # Assign role if provided
    if user_data.role is not None:
        print(f"roleName: {user_data.role}")
        role_id = role_name_to_id.get(user_data.role.lower())
        print(f"role_id: {role_id}")
        if role_id is None:
            raise HTTPException(status_code=400, detail=f"Rol '{user_data.role}' no válido")
        await assign_role_to_user(db_response["id"], role_id)

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
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))
) -> str:
    print('payload:', payload)
    await assign_role_to_user(payload.user_id, payload.role_id)

    return JSONResponse(status_code=200, content={"info": "Rol asignado exitosamente"})


@router.post("/asignar-cliente")
async def assign_client(
    body: AssignClientRequest,
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))
) -> Dict[str, Any]:

    pool = await get_pool()

    async with pool.acquire() as conn:
        try:
            async with conn.transaction():
                cursor_name = "cur_assign_client"

                # Ejecutar el procedimiento almacenado
                await conn.execute(
                    """
                    CALL sp_assign_client($1, $2, $3, $4);
                    """,
                    body.userId,
                    body.customerId,
                    body.categorieId,
                    cursor_name
                )

                # Leer el contenido del cursor
                rows = await conn.fetch(f"FETCH ALL FROM {cursor_name}")

                if not rows:
                    raise HTTPException(status_code=500, detail="El procedimiento no devolvió datos.")

                row = rows[0]

                # Devolver respuesta
                return {
                    "message": row["message"],
                    "insertedCount": row["inserted_count"],
                    "insertedCategories": row["inserted_categories"],
                    "failedCategories": row["failed_categories"]
                }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))