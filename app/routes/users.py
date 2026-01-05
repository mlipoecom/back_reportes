import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import date
import bcrypt
from typing import Dict, Any, List
from mail import send_user_password_email
from models import UserGenerate, UserGenerateResponse, AssignClientRequest, UserUpdate
from utils import generate_safe_password
from database import get_pool
from models import AssignRolesRequest
from dependencies import require_roles
from roles import UserRole
import pyotp
import secrets
import string

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

async def call_sp_update_user(
    user_id: int,
    p_id: int,
    p_name: str = None,
    p_last_name: str = None,
    p_external_id: str = None,
    p_supplier: int = None,
    p_company: int = None,
    p_customer: int = None,
    p_email: str = None,
) -> Dict[str, Any]:

    async with (await get_pool()).acquire() as conn:
        try:
            raw_result = await conn.fetchval(
                "SELECT fn_update_user($1,$2,$3,$4,$5,$6,$7,$8,$9);",
                user_id,
                p_id,
                p_name,
                p_last_name,
                p_external_id,
                p_supplier,
                p_company,
                p_customer,
                p_email
            )
        except Exception as e:
            msg = str(e).split('\n')[0].strip()
            raise HTTPException(status_code=500, detail=f"Error en la BD: {msg}")

    if raw_result is None:
        raise HTTPException(status_code=500, detail="La función no devolvió datos")

    result = json.loads(raw_result)
    return result

async def call_sp_delete_user(
    action_user_id: int,
    user_id: int
) -> Dict[str, Any]:
    async with (await get_pool()).acquire() as conn:
        raw_result = await conn.fetchval(
            "SELECT fn_delete_user($1, $2);",
            action_user_id,
            user_id
        )

    if raw_result is None:
        raise HTTPException(status_code=500, detail="La función no devolvió datos")

    return json.loads(raw_result)

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

def recovery_keys_generate(cantidad=8, longitud=10):
    claves = []
    caracteres = string.ascii_uppercase + string.digits
    for _ in range(cantidad):
        clave = ''.join(secrets.choice(caracteres) for _ in range(longitud))
        claves.append(clave)
    return claves

def hash_keys(claves_plano):
    hashes = []
    for clave in claves_plano:
        clave_normalizada = clave.strip().upper()
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(clave_normalizada.encode('utf-8'), salt)
        hashes.append(hashed.decode('utf-8'))
    return hashes

async def call_sp_insert_user_mfa(
    p_id: int,
    p_secret: str,
    p_recovery_codes: List[str]
) -> Dict[str, Any]:
    
    pool = await get_pool()
    cursor_name = "user_mfa_insert_result"
    
    params = (p_id, p_secret, p_recovery_codes, cursor_name)
    
    async with pool.acquire() as conn:
        try:
            async with conn.transaction():
                await conn.execute("CALL sp_insert_user_mfa($1, $2, $3, $4)", *params)
                
                rows = await conn.fetch(f'FETCH ALL IN "{cursor_name}";')

            if not rows:
                raise HTTPException(status_code=500, detail="Error en la BD: SP no devolvió datos")
            res_dict = dict(rows[0]) 
            message = res_dict.get("message")

            if message is None:
                message = rows[0][0]
            
            if not message:
                raise HTTPException(status_code=500, detail="Error en la BD: respuesta inválida del SP")
            
            return dict(rows[0])

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
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))
):
    role_name_to_id = {
        "super_admin": UserRole.SUPER_ADMIN,
        "supplier_admin": UserRole.SUPPLIER_ADMIN,
        "customer_admin": UserRole.CUSTOMER_ADMIN,
        "customer_user": UserRole.CUSTOMER_USER,
        "company_admin": UserRole.COMPANY_ADMIN,
        "company_user": UserRole.COMPANY_USER,
    }
    admin_id = current_user.get("ID")

    # Generación de credenciales base
    try:
        password = generate_safe_password()
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"info": f"Error al generar contraseña: {e}", "id": 0}
        )

    # Inserción del usuario
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
        p_created_by=admin_id
    )

    if db_response["id"] == 0 or (db_response["info"] and "error" in db_response["info"].lower()):
        return JSONResponse(
            status_code=400,
            content={"info": db_response["info"], "id": 0}
        )
    
    new_user_id = db_response["id"]

    # Asignación de Roles
    if user_data.role is not None:
        role_id = role_name_to_id.get(user_data.role.lower())
        if role_id is None:
            raise HTTPException(status_code=400, detail=f"Rol '{user_data.role}' no válido")
        await assign_role_to_user(new_user_id, role_id)

    # Configuración de MFA
    try:
        mfa_secret = pyotp.random_base32()
        recovery_keys_raw = recovery_keys_generate()
        recovery_keys_hashed = hash_keys(recovery_keys_raw)
        
        # Guardar configuración y capturar respuesta
        mfa_db_res = await call_sp_insert_user_mfa(
            p_id=new_user_id,
            p_secret=mfa_secret,
            p_recovery_codes=recovery_keys_hashed
        )

        if "error" in mfa_db_res.get("message", "").lower():
             raise HTTPException(
                status_code=500, 
                detail=f"La base de datos rechazó la configuración MFA: {mfa_db_res.get('message')}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al configurar MFA para el usuario: {str(e)}")

    # Envío de mail
    try:
        recovery_text = "\n".join(recovery_keys_raw)
        
        send_user_password_email(
            user_email=user_data.email,
            full_name=f"{user_data.name} {user_data.lastName}",
            username=f"{user_data.externalId}",
            generated_password=password,
            recovery_codes=recovery_text 
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "info": f"Usuario creado y MFA configurado, pero no se pudo enviar el correo: {e}",
                "id": new_user_id
            }
        )

    # Respuesta exitosa
    return UserGenerateResponse(
        info=db_response["info"],
        id=new_user_id
    )

@router.put(
    "/usuario/{userEdit_id}/editar",
    summary="Editar usuario",
    description="Editar un usuario de una empresa",
    responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Usuario modificado exitosamente.",
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
                        "info": "No existe un usuario con el ID",
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

async def edit_user(
    user_data: UserUpdate,
    userEdit_id:int,
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))):
    role_name_to_id = {
        "super_admin": UserRole.SUPER_ADMIN,
        "supplier_admin": UserRole.SUPPLIER_ADMIN,
        "customer_admin": UserRole.CUSTOMER_ADMIN,
        "customer_user": UserRole.CUSTOMER_USER,
        "company_admin": UserRole.COMPANY_ADMIN,
        "company_user": UserRole.COMPANY_USER,
    }
    user_id = current_user.get("ID")

    db_response = await call_sp_update_user(
        user_id,
        userEdit_id,
        user_data.name,
        user_data.lastName,
        user_data.externalId,
        p_supplier=user_data.supplierId if user_data.supplierId else None,
        p_company=user_data.companyId if user_data.companyId else None,
        p_customer=user_data.customerId if user_data.customerId else None,
        p_email=user_data.email,
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

    return UserGenerateResponse(
        info=db_response["info"],
        id=db_response["id"]
    )


@router.delete(
    "/usuario/{user_id}/eliminar",
    summary="Eliminar usuario",
    description="Elimina un usuario por ID",
    responses={
        200: {
            "description": "Usuario eliminado correctamente"
        },
        400: {
            "description": "Error de validación"
        },
        401: {
            "description": "No autorizado"
        },
        500: {
            "description": "Error interno"
        },
    }
)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(
        require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN])
    )
):
    action_user_id = current_user.get("ID")
    if action_user_id is None:
        raise HTTPException(status_code=401, detail="No se pudo obtener el usuario del token")

    db_response = await call_sp_delete_user(
        action_user_id=action_user_id,
        user_id=user_id
    )

    if db_response.get("affectedRows", 0) == 0:
        return JSONResponse(
            status_code=400,
            content=db_response
        )

    return JSONResponse(
    status_code=200,
    content=db_response
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