from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import date
from typing import Dict, Any
from ..models import CompanyGenerate, CompanyGenerateResponse
from ..database import get_pool

router = APIRouter(
    prefix="/administrativa",
    tags=["Administrativas"]
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
    "/crear-empresa",
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
async def generate_and_create_company(company_data: CompanyGenerate):
    try:
        db_response = await call_sp_insert_company(
            company_data.name,
            company_data.businessName,
            company_data.externalId,
            company_data.description,
            company_data.status,
            company_data.supplierId,
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
