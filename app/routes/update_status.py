from fastapi import APIRouter, HTTPException, Query, Header, Depends
from typing import Literal
from database import get_pool
from models import UpdateStatusResponse
from dependencies import require_roles
from roles import UserRole

router = APIRouter(
    prefix="/app",
    tags=["App"]
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
    p_entity: Literal["company", "user", "supplier", "customer"] = Query(
        ..., description="Nombre de la entidad", example="user"
    ),
    p_status: Literal["activo", "suspendido", "inactivo"] = Query(
        ..., description="Nuevo estado", example="activo"
    ),
    authorization: str = Header(..., description="Bearer Token"),
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))
    ):

    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.fetchval(
                "SELECT fn_update_status($1, $2, $3)",
                p_id,
                p_entity,
                p_status
            )
            if result != 'OK':
                return {"ejecutado": False, "info": result}
            return {"ejecutado": True, "info": "Actualización exitosa"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
