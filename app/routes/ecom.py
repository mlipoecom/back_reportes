import json
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from datetime import date
from typing import Dict, Any, Optional
from models import SupplierGenerate, SupplierGenerateResponse, UserGenerate, AssignRolesRequest
from database import get_pool
from utils import get_user_id_from_token
from .users import generate_and_create_user, assign_roles
router = APIRouter(
    prefix="/ecom",
    tags=["Ecom"]
)

async def call_sp_insert_supplier(
    p_name: str,
    p_business_name: str,
    p_external_id: str,
    p_description: str,
    p_status: str,
    p_email: str,
    p_created_by: int
) -> Dict[str, Any]:
    p_creation_date = date.today()
    cursor_name = "supplier_insert_result"

    params = (
        p_name, p_business_name, p_external_id, p_description,
        p_creation_date, p_status, p_email, p_created_by, cursor_name
    )
    try:
        async with (await get_pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "CALL sp_insert_supplier($1,$2,$3,$4,$5,$6,$7,$8,$9);",
                    *params
                )
                rows = await conn.fetch(f'FETCH ALL IN "{cursor_name}";')
    except Exception as e:
        msg = str(e).split('\n')[0].strip()
        raise HTTPException(status_code=500, detail=f"Error en la BD: {msg}")

    if rows:
        return {"info": rows[0].get("info"), "id": rows[0].get("id")}
    raise HTTPException(status_code=500, detail="SP no devolvió datos")

# -------------------------------
# SUPPLIER CREATE
# -------------------------------

@router.post("/proveedores/crear",
            summary= "Crear proveedor",
            description="Registrar un nuevo proveedor",
            response_model=SupplierGenerateResponse,
            responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Proveedor creado exitosamente.",
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
                        "info": "Ya existe un proveedor con el mismo ID externo",
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
    })

async def generate_and_create_supplier(
    supplier_data: SupplierGenerate,
    authorization: str = Header(..., description="Bearer Token")):

    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    token = authorization
    user_id = get_user_id_from_token(token)
    
    try:
        db_response = await call_sp_insert_supplier(
        supplier_data.name, supplier_data.businessName, supplier_data.externalId,
        supplier_data.description, supplier_data.status, supplier_data.email, user_id
    )
        response = SupplierGenerateResponse(**db_response)
        supplier_id = response.id
        print(supplier_id)
        if db_response["id"] == 0 or (
            db_response["info"] and "error" in db_response["info"].lower()
        ):
            return JSONResponse(status_code=400, content=db_response)
        supplier_admin_data: Dict[str, UserGenerate]  = {
            "admin_user": UserGenerate(
                name=f"Administrador",
                lastName=supplier_data.name,
                email=supplier_data.email,
                externalId=f"admin_{supplier_data.name}",
                supplierId=supplier_id,
                companyId=None,
                customerId=None,
                status="activo"
            )
        }

        result_user = await generate_and_create_user(
            supplier_admin_data["admin_user"],
            authorization)

        supplier_admin_id = result_user.id
        role_data: Dict[str, AssignRolesRequest] = {
            "assignRole": AssignRolesRequest(
                user_id=supplier_admin_id,
                role_id=2
            )
        }

        await assign_roles(role_data["assignRole"], authorization)

        return response
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear proveedor: {e}")
    
    
    
# -------------------------------
# SUPPLIER LIST
# -------------------------------

@router.get(
    "/proveedores/listar",
    summary="Listar proveedores",
    description="Devuelve la lista de proveedores filtrados por diferentes criterios.",
    responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Proveedores listados exitosamente",
                        "suppliers": [
                            {
                            "id": 1,
                            "name": "Ecom",
                            "email": "info@ecom.com.uy",
                            "status": "activo",
                            "createdAt": "2025-10-29",
                            "createdBy": "provAdmin",
                            "externalId": "Ecom",
                            "description": "Desc",
                            "businessName": "Ecom Center SRL"
                        }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Error interno",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Error en la BD",
                        "suppliers": []
                    }
                }
            },
        },
    }
)
async def get_suppliers(
    id: Optional[int] = Query(None, description="Filtrar por ID del proveedor."),
    name: Optional[str] = Query(None, description="Filtrar por nombre del proveedor."),
    businessName: Optional[str] = Query(None, description="Filtrar por razón social."),
    externalId: Optional[str] = Query(None, description="Filtrar por ID externo."),
    limit: Optional[int] = Query(10, description="Cantidad máxima de registros a devolver."),
    offset: Optional[int] = Query(0, description="Cantidad de registros a omitir antes de comenzar la lista."),
    authorization: str = Header(..., description="Bearer Token")
):
    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")
    
    try:
        async with (await get_pool()).acquire() as conn:

            rows = await conn.fetch(
                "SELECT fn_get_supplier($1,$2,$3,$4,$5,$6);",
                id,
                name,
                businessName,
                externalId,
                limit,
                offset
            )

            # Convertir jsonb a dict
            suppliers = [json.loads(record["fn_get_supplier"]) for record in rows]

            return {
                "info": "Proveedores listados exitosamente",
                "proveedores": suppliers
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -------------------------------
# SUPPLIER DELETE
# -------------------------------

@router.delete(
    "/proveedores/{supplierId}/eliminar",
    summary="Eliminar o inactivar proveedor",
    description=(
        "Elimina físicamente un proveedor si no tiene compañías asociadas. "
        "Si tiene compañías, lo marca como inactivo. "
        "Solo permite eliminar proveedores creados por el usuario que ejecuta."
    ),
    responses={
        200: {
            "description": "Resultado de la operación",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Proveedor eliminado correctamente",
                        "affectedRows": 1
                    }
                }
            },
        },
        404: {
            "description": "Proveedor no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "message": "El proveedor no existe",
                        "affectedRows": 0
                    }
                }
            },
        },
        500: {
            "description": "Error interno",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Error en la BD",
                        "affectedRows": 0
                    }
                }
            },
        },
    }
)
async def delete_supplier(
    supplierId: int,
    authorization: str = Header(..., description="Bearer Token")
):
    # Validar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    user_id = get_user_id_from_token(authorization) 

    if user_id is None:
        raise HTTPException(status_code=401, detail="No se pudo obtener userId del token")

    try:
        async with (await get_pool()).acquire() as conn:
            row = await conn.fetchrow(
                "SELECT fn_delete_supplier($1, $2);",
                user_id,
                supplierId
            )

            if row is None:
                raise HTTPException(status_code=500, detail="La función no devolvió datos")

            result = json.loads(row["fn_delete_supplier"])

            # Si el SP devuelve "El proveedor no existe", lo trato como 404
            if result.get("affectedRows") == 0:
                return JSONResponse(status_code=404, content=result)

            return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )