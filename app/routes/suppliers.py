from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import date
from typing import Dict, Any
from models import SupplierGenerate, SupplierGenerateResponse
from database import get_pool
from dependencies import require_roles
from roles import UserRole

router = APIRouter(
    prefix="/administrativa",
    tags=["Administrativas"]
)

async def call_sp_insert_supplier(
    p_name: str,
    p_business_name: str,
    p_external_id: str,
    p_description: str,
    p_status: str,
    p_email: str
) -> Dict[str, Any]:
    p_creation_date = date.today()
    cursor_name = "supplier_insert_result"

    params = (
        p_name, p_business_name, p_external_id, p_description,
        p_creation_date, p_status, p_email, cursor_name
    )
    try:
        async with (await get_pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "CALL sp_insert_supplier($1,$2,$3,$4,$5,$6,$7,$8);",
                    *params
                )
                rows = await conn.fetch(f'FETCH ALL IN "{cursor_name}";')
    except Exception as e:
        msg = str(e).split('\n')[0].strip()
        raise HTTPException(status_code=500, detail=f"Error en la BD: {msg}")

    if rows:
        return {"info": rows[0].get("info"), "id": rows[0].get("id")}
    raise HTTPException(status_code=500, detail="SP no devolvió datos")

@router.post("/crear-proveedor",
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
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN]))
):
    try:
        db_response = await call_sp_insert_supplier(
        supplier_data.name, supplier_data.businessName, supplier_data.externalId,
        supplier_data.description, supplier_data.status, supplier_data.email
    )
        if db_response["id"] == 0 or (
            db_response["info"] and "error" in db_response["info"].lower()
        ):
            return JSONResponse(status_code=400, content=db_response)

        return SupplierGenerateResponse(**db_response)
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear proveedor: {e}")