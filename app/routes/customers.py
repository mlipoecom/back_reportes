from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from database import get_pool
import json
from dependencies import require_roles
from roles import UserRole

router = APIRouter(
    prefix="/api",
    tags=["Api"]
)


@router.get("/get-customers",
            summary="Listar clientes",
            description="Devuelve la lista de clientes de la compañía.",
            responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Clientes listados exitosamente",
                        "customers": [
                            {
                                "id": 1,
                                "name": "Cliente 1",
                                "email": "cliente1@example.com",
                                "phone": "1234567890",
                                "address": "Calle 123, Ciudad, País"
                            },
                            {
                                "id": 2,
                                "name": "Cliente 2",
                                "email": "cliente2@example.com",
                                "phone": "0987654321",
                                "address": "Avenida 456, Ciudad, País"
                            }
                        ]
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
                        "customers": []
                    }
                }
            },
        },
    }
)
async def get_customers(
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))
):
    company_id = current_user.get("companyId")
    try:
        async with (await get_pool()).acquire() as conn:
            rows = await conn.fetch("SELECT fn_get_customers($1);", company_id)
            customers = [json.loads(row["fn_get_customers"]) for row in rows]
            return JSONResponse(
                content={
                    "info": "Clientes listados exitosamente",
                    "customers": customers,
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))