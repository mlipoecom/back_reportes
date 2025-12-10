from fastapi import UploadFile, Form, HTTPException, APIRouter, Depends
import boto3
import os
from typing import Dict, Any
from config import S3_CONFIG
from database import get_pool
from datetime import date, datetime
from routes.categories import get_category_by_id
from routes.companies import get_customer_by_id
from dependencies import require_roles
from roles import UserRole

router = APIRouter(
    prefix="/app/archivos",
    tags=["Archivos"]
)

# Configuración S3 - usar valores por defecto si no están definidos
S3_ENDPOINT = S3_CONFIG.get("S3_ENDPOINT", "http://127.0.0.1:4566")
S3_BUCKET = S3_CONFIG.get("S3_BUCKET", "portal-informes-dev")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

def ensure_bucket():
    """Crear bucket si no existe. Se ejecuta lazy (cuando se necesita)."""
    try:
        buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
        if S3_BUCKET not in buckets:
            s3.create_bucket(Bucket=S3_BUCKET)
    except Exception as e:
        # Si LocalStack no está disponible, intentar en el primer endpoint que lo necesite
        print(f"Warning: No se pudo verificar/crear el bucket S3: {e}")

async def call_sp_insert_file(
    p_name: str,
    p_path: str,
    p_upload: str,
    p_report: str,
    p_category_id: int,
    p_customer_id: int,
    p_company_user_id: int
) -> Dict[str, Any]:
    p_return = "file_insert_result"

    try:
        async with (await get_pool()).acquire() as conn:
            async with conn.transaction():
                # Paso 1: ejecutar el SP (no fetch)
                await conn.execute(
                    "CALL sp_insert_file($1,$2,$3,$4,$5,$6,$7,$8);",
                    p_name,
                    p_path,
                    p_upload,
                    p_report,
                    p_category_id,
                    p_customer_id,
                    p_company_user_id,
                    p_return
                )

                # Paso 2: obtener los resultados del cursor
                rows = await conn.fetch(f'FETCH ALL FROM "{p_return}";')

    except Exception as e:
        msg = str(e).split("\n")[0].strip()
        raise HTTPException(status_code=500, detail=f"Error en la BD: {msg}")

    if not rows:
        raise HTTPException(status_code=500, detail="SP no devolvió datos")

    return {
        "info": rows[0]["info"],
        "id": rows[0]["id"]
    }

@router.post("/upload")
async def upload_file(
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.COMPANY_USER, UserRole.COMPANY_ADMIN])),
    customer_id: int = Form(...),
    category_id: int = Form(...),
    report_date: str = Form(...),
    file: UploadFile = None
):
    if not file:
        raise HTTPException(status_code=400, detail="Debe incluir un archivo")

    # Asegurar que el bucket existe antes de subir archivo
    ensure_bucket()

    category = await get_category_by_id(category_id)

    customer = await get_customer_by_id(customer_id)

    company_user_id = current_user.get("ID")

    fecha_reporte_dt = datetime.strptime(report_date, "%Y-%m-%d")
    year = fecha_reporte_dt.year
    month = fecha_reporte_dt.month
    day = fecha_reporte_dt.day
    _, ext = os.path.splitext(file.filename)
    file_name = f"{customer['name']}_{category['name']}_{month}_{year}{ext}"
    key = f"{customer['name']}/{category['name']}/{file_name}"

    s3.upload_fileobj(file.file, S3_BUCKET, key)

    print("Nombre:", file_name)
    print("Path:", f"{customer['name']}/{category['name']}")
    print("Upload:", str(date.today()))
    print("Report:", f"{year}-{month}-{day}")
    print("Category:", category['name'])
    print("Company User:", company_user_id)
    print("Customer:", customer['name'])

    db_response = await call_sp_insert_file(
        file_name,  
        f"{customer['name']}/{category['name']}", # path
        str(date.today()), # upload date
        f"{year}-{month}-{day}", # report date
        category_id, 
        customer_id,
        company_user_id
    )

    return {
        "info": db_response["info"],
        "id": db_response["id"],
        "bucket": S3_BUCKET,
        "directorio": f"{customer['name']}/{category['name']}",
        "nombre_archivo": file_name,
        "ruta_s3": key
    }
