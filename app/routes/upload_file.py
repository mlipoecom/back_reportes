from fastapi import UploadFile, Form, HTTPException, APIRouter, Depends
import boto3
import os
from typing import Dict, Any
from config import S3_CONFIG
from database import get_pool
from datetime import date
from dependencies import require_roles
from roles import UserRole

router = APIRouter(
    prefix="/administrativa",
    tags=["Administrativas"]
)


S3_ENDPOINT = S3_CONFIG["S3_ENDPOINT"]
S3_BUCKET = S3_CONFIG["S3_BUCKET"]

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

def ensure_bucket():
    buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if S3_BUCKET not in buckets:
        s3.create_bucket(Bucket=S3_BUCKET)
ensure_bucket()

async def call_sp_insert_file(
    p_name: str,
    p_path: str,
    p_upload: str,
    p_report: str,
    p_category: str,
    p_company: int
) -> Dict[str, Any]:
    p_return = "file_insert_result"

    try:
        async with (await get_pool()).acquire() as conn:
            async with conn.transaction():
                # Paso 1: ejecutar el SP (no fetch)
                await conn.execute(
                    "CALL sp_insert_file($1,$2,$3,$4,$5,$6,$7);",
                    p_name,
                    p_path,
                    p_upload,
                    p_report,
                    p_category,
                    p_company,
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
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN])),
    empresa: int = Form(...),
    categoria: str = Form(...),
    dia: str = Form(...),
    mes: int = Form(...),
    anio: int = Form(...),
    file: UploadFile = None
):
    if not file:
        raise HTTPException(status_code=400, detail="Debe incluir un archivo")

    _, ext = os.path.splitext(file.filename)
    nuevo_nombre = f"{empresa}_{categoria}_{mes}_{anio}{ext}"
    key = f"{empresa}/{categoria}/{nuevo_nombre}"

    s3.upload_fileobj(file.file, S3_BUCKET, key)

    company_id = current_user.get("companyId")

    print("Nombre:", nuevo_nombre)
    print("Path:", f"{empresa}/{categoria}")
    print("Upload:", str(date.today()))
    print("Report:", f"{anio}-{mes}-{dia}")
    print("Category:", categoria)
    print("Company:", company_id)


    db_response = await call_sp_insert_file(
        nuevo_nombre,
        f"{empresa}/{categoria}",
        str(date.today()),
        f"{anio}-{mes}-{dia}",
        categoria,
        company_id
    )

    return {
        "mensaje": db_response["info"],
        "id": db_response["id"],
        "bucket": S3_BUCKET,
        "directorio": f"{empresa}/{categoria}",
        "nombre_archivo": nuevo_nombre,
        "ruta_s3": key
    }
