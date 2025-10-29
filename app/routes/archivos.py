from fastapi import APIRouter, Query, HTTPException, Header
from typing import Optional, List, Dict, Any
from datetime import date
from dateutil import parser as date_parser
import json
from security import decode_token
from database import get_pool
from files import drive_direct_download_url, transform_dropbox_link

router = APIRouter(
    prefix="/api",
    tags=["Api"]
)

def get_company_id_from_token(authorization: str) -> int:
    try:
        token = authorization.split(" ")[1]
    except Exception:
        raise HTTPException(status_code=401, detail="Encabezado Authorization inválido")

    payload = decode_token(token)
    company_id = payload.get("companyId")

    if not company_id:
        raise HTTPException(status_code=401, detail="Token sin companyId")

    return company_id


async def call_fn_get_archivos(
    p_id_cliente: int,
    p_id_nombre: Optional[str] = None,
    p_nombre_categoria: Optional[str] = None,
    p_fecha_desde: Optional[date] = None,
    p_fecha_hasta: Optional[date] = None,
    p_limit: Optional[int] = 10,
    p_offset: Optional[int] = 0
) -> List[Dict[str, Any]]:

    params = (
        p_id_cliente,
        p_id_nombre or "",
        p_nombre_categoria or "",
        p_fecha_desde,
        p_fecha_hasta,
        p_limit,
        p_offset
    )

    try:
        async with (await get_pool()).acquire() as conn:
            rows = await conn.fetch(
                "SELECT fn_get_files($1,$2,$3,$4,$5,$6,$7);",
                *params
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en BD: {e}")

    archivos = []
    for record in rows:
        json_data = record[0]
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except:
                pass
        if isinstance(json_data, dict) and "ruta" in json_data:
            ruta = json_data["ruta"]
            # detectar tipo de URL y aplicar función correspondiente
            if "drive.google.com" in ruta:
                json_data["ruta"] = drive_direct_download_url(ruta)
            elif "dropbox.com" in ruta:
                json_data["ruta"] = transform_dropbox_link(ruta)
            archivos.append(json_data)
    return archivos

@router.get("/archivos",
            summary="Obtener archivos",
            description="Devuelve los archivos pertenecientes al cliente filtrados por categorías, fechas y nombres para descarga directa",
            responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "ruta": "https://drive.google.com/........",
                            "nombre": "acme_ddos_reporte_08_2025",
                            "categoría": "DDOS",
                            "fechaReporte": "2025-08-22"
                        },
                        {
                            "ruta": "https://www.dropbox.com/scl/fi/........",
                            "nombre": "acme_pentesting_reporte_07_2025",
                            "categoría": "Pentesting",
                            "fechaReporte": "2025-07-16"
                        },
                        {
                            "ruta": "s3ssl://amzn-s3-demo-bucket/........",
                            "nombre": "acme_treathounting_reporte_06_2025",
                            "categoría": "Treathounting",
                            "fechaReporte": "2025-06-09"
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
async def get_archivos(
    authorization: str = Header(..., description="Bearer Token", example="eyJhbGciOiJIUzI1NCI6NzEIkpXVCJ9........"),
    nombre: Optional[str] = Query(None, example="acme_treathounting_reporte_06_2025"),
    categoria: Optional[str] = Query(None, example="DDOS"),
    fecha_desde_str: Optional[str] = Query(None, alias="fecha_desde", example="2025-01-01"),
    fecha_hasta_str: Optional[str] = Query(None, alias="fecha_hasta", example="2025-31-12"),
    limit: Optional[int] = Query(10, ge=1),
    offset: Optional[int] = Query(0, ge=0)
) -> List[Dict[str, Any]]:

    company_id = get_company_id_from_token(authorization)

    fecha_desde = None
    fecha_hasta = None

    if fecha_desde_str:
        try:
            fecha_desde = date_parser.parse(fecha_desde_str).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Fecha inválida en fecha_desde")

    if fecha_hasta_str:
        try:
            fecha_hasta = date_parser.parse(fecha_hasta_str).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Fecha inválida en fecha_hasta")

    return await call_fn_get_archivos(
        p_id_cliente=company_id,
        p_id_nombre=nombre,
        p_nombre_categoria=categoria,
        p_fecha_desde=fecha_desde,
        p_fecha_hasta=fecha_hasta,
        p_limit=limit,
        p_offset=offset
    )
