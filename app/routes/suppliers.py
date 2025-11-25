import json
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from datetime import date
from typing import Dict, Any, Optional
from models import CompanyGenerate, CustomerGenerate, CompanyGenerateResponse, CustomerGenerateResponse
from database import get_pool
from utils import get_supplier_id_from_token

router = APIRouter(
    prefix="/proveedor",
    tags=["Proveedores"]
)

async def call_sp_insert_company(
    p_name: str,
    p_business_name: str,
    p_external_id: str,
    p_description: str,
    p_status: str,
    p_supplier_id: int,
    p_email: str
) -> Dict[str, Any]:
    p_creation_date = date.today()
    cursor_name = "company_insert_result"

    params = (
        p_name, p_business_name, p_external_id, p_description,
        p_creation_date, p_status, p_supplier_id, p_email, cursor_name
    )
    try:
        async with (await get_pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "CALL sp_insert_company($1,$2,$3,$4,$5,$6,$7,$8,$9);",
                    *params
                )
                rows = await conn.fetch(f'FETCH ALL IN "{cursor_name}";')
    except Exception as e:
        msg = str(e).split('\n')[0].strip()
        raise HTTPException(status_code=500, detail=f"Error en la BD: {msg}")

    if not rows:
        raise HTTPException(status_code=500, detail="SP no devolvió datos")

    info = rows[0].get("info")
    id_val = rows[0].get("id", 0)

    return {"info": info, "id": id_val}


@router.post(
    "/empresa/crear",
    summary= "Crear empresa",
    description="Registrar una nueva empresa",
    response_model=CompanyGenerateResponse,
    responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Compañía creada exitosamente.",
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
                        "info": "Ya existe una compañía con el mismo ID externo.",
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
    }
)
async def generate_and_create_company(
    company_data: CompanyGenerate,
    authorization: str = Header(..., description="Bearer Token")):
    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    token = authorization

    # Obtengo supplierId
    supplier_id = get_supplier_id_from_token(token)
    if supplier_id is None:
        raise HTTPException(status_code=401, detail="No se pudo obtener supplierId del token")
    try:
        db_response = await call_sp_insert_company(
            company_data.name,
            company_data.businessName,
            company_data.externalId,
            company_data.description,
            company_data.status,
            supplier_id,
            company_data.email
        )

        if db_response["id"] == 0 or (
            db_response["info"] and "error" in db_response["info"].lower()
        ):
            return JSONResponse(status_code=400, content=db_response)

        return CompanyGenerateResponse(**db_response)

    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"info": f"Error al crear empresa: {e}", "id": 0}
        )

async def call_sp_insert_customer(
    p_name: str,
    p_business_name: str,
    p_external_id: str,
    p_description: str,
    p_status: str,
    p_company_id: int,
    p_email: str
) -> Dict[str, Any]:

    cursor_name = "customer_insert_result"

    params = (
        p_name, p_business_name, p_external_id, p_description,
        p_status, p_company_id, p_email, cursor_name
    )
    try:
        async with (await get_pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "CALL sp_insert_customer($1,$2,$3,$4,$5,$6,$7,$8);",
                    *params
                )
                rows = await conn.fetch(f'FETCH ALL IN "{cursor_name}";')
    except Exception as e:
        msg = str(e).split('\n')[0].strip()
        raise HTTPException(status_code=500, detail=f"Error en la BD: {msg}")

    if not rows:
        raise HTTPException(status_code=500, detail="SP no devolvió datos")

    info = rows[0].get("info")
    id_val = rows[0].get("id", 0)

    return {"info": info, "id": id_val}


@router.post(
    "/cliente/crear",
    summary= "Crear cliente",
    description="Registrar un nuevo cliente",
    response_model=CustomerGenerateResponse,
    responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Cliente creado exitosamente.",
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
                        "info": "Ya existe un cliente con el mismo ID externo.",
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
    }
)
async def generate_and_create_customer(
    customer_data: CustomerGenerate,
    authorization: str = Header(..., description="Bearer Token")):
    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    try:
        db_response = await call_sp_insert_customer(
            customer_data.name,
            customer_data.businessName,
            customer_data.externalId,
            customer_data.description,
            customer_data.status,
            customer_data.companyId,
            customer_data.email
        )

        if db_response["id"] == 0 or (
            db_response["info"] and "error" in db_response["info"].lower()
        ):
            return JSONResponse(status_code=400, content=db_response)

        return CustomerGenerateResponse(**db_response)

    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"info": f"Error al crear empresa: {e}", "id": 0}
        )
    
@router.get("/empresa/listar",
        summary="Listar compañías.",
        description="Devuelve la lista de compañías pertenecientes a un proveedor.",
        responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Compañías listadas exitosamente",
                        "companies": [
                            
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
                        "categories": []
                    }
                }
            },
        },
    }
)
async def get_companies(
    name: Optional[str] = Query(None, description="Nombre de la compañía"),
    businessName: Optional[str] = Query(None, description="Nombre comercial"),
    externalId: Optional[str] = Query(None, description="Descripción"),
    companyId: Optional[str] = Query(None, description="ID de la compañía", example="1"),
    status: Optional[str] = Query(None, description="Status", example="activo"),
    limit: Optional[int] = Query(10, description="Límite de registros.", example=10),
    offset: Optional[int] = Query(0, description="Desplazamiento de registros", example=0),
    authorization: str = Header(description="Bearer Token", example="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
):
    supplier_id = get_supplier_id_from_token(authorization)

    # Validación companyId
    if companyId is not None and companyId.strip() != "":
        if not companyId.isdigit():
            raise HTTPException(
                status_code=400,
                detail="companyId debe ser un número entero"
            )
        companyId_int = int(companyId)
    else:
        companyId_int = None

    try:
        async with (await get_pool()).acquire() as conn:
            rows = await conn.fetch(
                "SELECT fn_get_companies($1,$2,$3,$4,$5,$6,$7,$8);",
                supplier_id, name, businessName, companyId_int,
                externalId, status, offset, limit
            )

            companies = [json.loads(row["fn_get_companies"]) for row in rows]

            return {
                "info": "Compañías listadas exitosamente",
                "companies": companies
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
