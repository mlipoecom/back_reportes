from fastapi import APIRouter, Query, HTTPException, Depends, Request
from typing import Optional, Dict, Any
from datetime import date
from dateutil import parser as date_parser
import json
from database import get_pool
from dependencies import require_roles
from roles import UserRole
from utils import generate_presigned_url, get_client_ip

router = APIRouter(
    prefix="/app/archivos",
    tags=["Archivos"]
)

async def call_fn_get_archivos(
    p_id_cliente: int,
    p_company_user_id: Optional[int] = None,
    p_id_nombre: Optional[str] = None,
    p_nombre_categoria: Optional[str] = None,
    p_fecha_desde: Optional[date] = None,
    p_fecha_hasta: Optional[date] = None,
    p_limit: Optional[int] = 10,
    p_offset: Optional[int] = 0
) -> Dict[str, Any]:
    """Llama a la función fn_get_files en PostgreSQL y devuelve el JSON procesado."""
    params = (
        p_id_cliente,
        p_company_user_id,  
        p_id_nombre or "",
        p_nombre_categoria or "",
        p_fecha_desde,
        p_fecha_hasta,
        p_limit,
        p_offset
    )

    try:
        async with (await get_pool()).acquire() as conn:
            result = await conn.fetchval(
                "SELECT fn_get_files($1,$2,$3,$4,$5,$6,$7,$8);",
                *params
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en BD: {e}")

    if not result:
        return {"companyId": p_id_cliente, "supplier": None, "totalCount": 0, "files": []}

    # Si viene como string, convertirlo a JSON
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except Exception:
            raise HTTPException(status_code=500, detail="Error al parsear respuesta JSON de la BD")

    # Procesar rutas dentro del array 'files'
    files = result.get("files", [])
    result["files"] = files
    return result


@router.get(
    "/listar",
    summary="Obtener archivos",
    description="Devuelve los archivos pertenecientes al cliente, filtrados por categorías, fechas y nombres, junto con información de la compañía.",
    responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "companyId": 123,
                        "supplier": "Ecom",
                        "totalCount": 47,
                        "files": [
                            {
                                "id": 32142134,
                                "nombre": "acme_ddos_reporte_08_2025",
                                "categoría": "DDOS",
                                "fechaReporte": "2025-08-22"
                            },
                            {
                                "id": 12312421,
                                "nombre": "acme_pentesting_reporte_07_2025",
                                "categoría": "Pentesting",
                                "fechaReporte": "2025-07-16"
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
                        "id": 0
                    }
                }
            },
        },
    }
)

async def get_archivos(
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN, UserRole.CUSTOMER_ADMIN, UserRole.CUSTOMER_USER, UserRole.COMPANY_ADMIN, UserRole.COMPANY_USER])),
    nombre: Optional[str] = Query(None, example="acme_treathounting_reporte_06_2025"),
    categoria: Optional[str] = Query(None, example="DDOS"),
    fecha_desde_str: Optional[str] = Query(None, alias="fecha_desde", example="2025-01-01"),
    fecha_hasta_str: Optional[str] = Query(None, alias="fecha_hasta", example="2025-12-31"),
    limit: Optional[int] = Query(10, ge=1),
    offset: Optional[int] = Query(0, ge=0)
) -> Dict[str, Any]:
    """Endpoint principal: obtiene los archivos de una compañía según filtros."""

    customer_id = current_user.get("customerId")

    user_role_id = current_user.get("role")

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

    result = await call_fn_get_archivos(
        p_id_cliente=customer_id,
        p_company_user_id=current_user.get("ID") if user_role_id == UserRole.COMPANY_USER else None,
        p_id_nombre=nombre,
        p_nombre_categoria=categoria,
        p_fecha_desde=fecha_desde,
        p_fecha_hasta=fecha_hasta,
        p_limit=limit,
        p_offset=offset
    )

    return result



@router.get(
    "/{file_id}/descargar",
    summary="Descargar archivo",
    description="Descarga un archivo de la compañía.",
    responses={
        200: {
            "description": "Ejecución exitosa",
        }
    }
)
async def download_file_by_id(
    file_id: int,
    request: Request,
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN, UserRole.CUSTOMER_ADMIN, UserRole.CUSTOMER_USER, UserRole.COMPANY_ADMIN, UserRole.COMPANY_USER]))
    )-> str:
    """Obtiene el archivo por id y registra la descarga."""
    user_id = current_user.get("ID")

    ip = get_client_ip(request)

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            file_data = await get_file_by_id(file_id)
            print("file_data: ", file_data)
            await log_file_download(user_id, file_id, ip, "log_file_download_result")
            presigned_url = generate_presigned_url(file_data["fn_get_file_path"])
    return presigned_url


async def get_file_by_id(file_id: int) -> Any:
    """Obtiene el archivo desde la base de datos utilizando el SP correspondiente."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.fetch("SELECT fn_get_file_path($1);", file_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en BD: {e}")

    if not result:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return result[0]


async def log_file_download(user_id: int, file_id: int, ip: str, cursor_name: str) -> None:
    """Registra en la base de datos la descarga del archivo."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute("CALL sp_insert_download($1,$2,$3,$4);", user_id, file_id, ip, cursor_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en BD: {e}")
