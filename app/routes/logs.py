import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from database import get_pool
from dependencies import require_roles
from roles import UserRole

router = APIRouter(
    prefix="/app",
    tags=["App"]
)

@router.get("/logs",
            summary="Obtener logs",
            description="Devuelve lista de logs filtrados por empresa, usuario y fechas",
            responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": [
                            {
                                "hora": "12:32:58",
                                "fecha": "2025-10-29",
                                "usuario": 71
                            },
                            {
                                "hora": "12:25:53",
                                "fecha": "2025-10-29",
                                "usuario": 22
                            },
                            {
                                "hora": "12:09:11",
                                "fecha": "2025-10-29",
                                "usuario": 4
                            },
                            {
                                "hora": "12:08:15",
                                "fecha": "2025-10-29",
                                "usuario": 71
                            }
                    ]
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
async def get_logs(
    empresa: int = Query(..., description="ID de la compañía", example=1),
    usuario: Optional[int] = Query(None, description="ID del usuario (opcional)", example=10),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)", example="2025-01-01"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)", example="2025-31-12"),
    limit: Optional[int] = Query(10, description="Límite de registros"),
    offset: Optional[int] = Query(0, description="Desplazamiento de registros"),
    authorization: str = Header(..., description="Bearer Token"),
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))
):
    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    try:
        date_from = datetime.strptime(fecha_desde, "%Y-%m-%d").date() if fecha_desde else None
        date_to = datetime.strptime(fecha_hasta, "%Y-%m-%d").date() if fecha_hasta else None

        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM fn_get_logs($1, $2, $3, $4, $5, $6);
                """,
                empresa,
                usuario,
                date_from,
                date_to,
                limit,
                offset
            )

            result = [json.loads(r["fn_get_logs"]) for r in rows]

            return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
