from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
from models import CustomerUpdate
from database import get_pool
from dependencies import require_roles
from roles import UserRole

router = APIRouter(
    prefix="/proveedor",
    tags=["Proveedores"]
)

async def call_fn_delete_customer(
    p_customer_id: int
) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            async with conn.transaction():
                result = await conn.fetchval(
                    "SELECT fn_delete_customer($1);",
                    p_customer_id
                )
                return result
        except Exception as e:
            msg = str(e).split('\n')[0].strip()
            raise HTTPException(
                status_code=500,
                detail=f"Error en la BD: {msg}"
            )

async def call_fn_update_customer(
    p_id: int,
    p_name: str = None,
    p_business_name: str = None,
    p_email: str = None
) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            async with conn.transaction():
                result = await conn.fetchval(
                    "SELECT fn_update_customer($1, $2, $3, $4);",
                    p_id, p_name, p_business_name, p_email
                )
                return {"message": result}
        except Exception as e:
            msg = str(e).split('\n')[0].strip()
            raise HTTPException(status_code=500, detail=f"Error en la BD: {msg}")

@router.put(
    "/cliente/{cliente_id}/editar",
    summary="Editar cliente",
    description="Actualiza la información de un cliente existente",
    responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Cliente actualizado exitosamente."
                    }
                }
            },
        },
        400: {
            "description": "Ejecución fallida",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Cliente no encontrado."
                    }
                }
            },
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Error en la BD: conexión fallida"
                    }
                }
            },
        },
    }
)
async def update_customer(
    customer_data: CustomerUpdate,
    cliente_id: int,
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))
) -> Dict[str, Any]:
    db_response = await call_fn_update_customer(
        cliente_id,
        customer_data.name,
        customer_data.businessName,
        customer_data.email
    )

    return db_response

@router.delete(
    "/cliente/{cliente_id}/eliminar",
    summary="Eliminar cliente",
    description="Elimina un cliente existente",
    responses={
        200: {
            "description": "Cliente eliminado correctamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Cliente eliminado exitosamente",
                        "affectedRows": 1
                    }
                }
            },
        },
        404: {
            "description": "Cliente no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No se encontró el cliente"
                    }
                }
            },
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error en la BD: ..."
                    }
                }
            },
        },
    }
)
async def delete_customer(
    cliente_id: int,
    current_user: dict = Depends(
        require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN])
    )
) -> Dict[str, Any]:
    db_response = await call_fn_delete_customer(cliente_id)
    return db_response