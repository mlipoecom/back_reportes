from fastapi import APIRouter, HTTPException, Query, Header
from typing import Literal
from database import get_pool
from models import UpdateStatusResponse

router = APIRouter(
    prefix="/administrativa",
    tags=["Administrativas"]
)

@router.put(
    "/cambiar-estado",
    response_model=UpdateStatusResponse,
    responses={
        200: {
            "description": "Resultado de la actualización",
            "content": {
                "application/json": {
                    "example": {
                        "ejecutado": True,
                        "info": "Actualización exitosa"
                    }
                }
            },
        },
        400: {
            "description": "Error en los parámetros",
            "content": {
                "application/json": {
                    "example": {
                        "ejecutado": False,
                        "info": "Categoría inválida: xyz"
                    }
                }
            },
        },
    }
)
async def update_status(
    p_id: int = Query(..., description="ID del registro a actualizar", example=1),
    p_category: Literal["company", "user", "supplier"] = Query(
        ..., description="Categoría de la entidad", example="user"
    ),
    p_status: Literal["activo", "suspendido", "inactivo"] = Query(
        ..., description="Nuevo estado", example="activo"
    ),
    authorization: str = Header(..., description="Bearer Token")):

    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.fetchval(
                "SELECT fn_update_status($1, $2, $3)",
                p_id,
                p_category,
                p_status
            )
            if result != 'OK':
                return {"ejecutado": False, "info": result}
            return {"ejecutado": True, "info": "Actualización exitosa"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
