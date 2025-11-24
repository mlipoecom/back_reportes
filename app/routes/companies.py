import json
from fastapi import APIRouter, HTTPException, Header, Query, Depends
from fastapi.responses import JSONResponse
from datetime import date
from typing import Dict, Any
from models import AssignClientRequest
from database import get_pool
from utils import get_user_id_from_token, get_company_id_from_token

from dependencies import require_roles
from roles import UserRole

router = APIRouter(
    prefix="/empresa",
    tags=["Empresas"]
)

@router.post("/asignar-cliente")
async def assign_client(body: AssignClientRequest) -> Dict[str, Any]:

    pool = await get_pool()

    async with pool.acquire() as conn:
        try:
            async with conn.transaction():
                cursor_name = "cur_assign_client"

                # Ejecutar el procedimiento almacenado
                await conn.execute(
                    """
                    CALL sp_assign_client($1, $2, $3, $4);
                    """,
                    body.userId,
                    body.customerId,
                    body.categorieId,
                    cursor_name
                )

                # Leer el contenido del cursor
                rows = await conn.fetch(f"FETCH ALL FROM {cursor_name}")

                if not rows:
                    raise HTTPException(status_code=500, detail="El procedimiento no devolvió datos.")

                row = rows[0]

                # Devolver respuesta
                return {
                    "message": row["message"],
                    "insertedCount": row["inserted_count"],
                    "insertedCategories": row["inserted_categories"],
                    "failedCategories": row["failed_categories"]
                }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
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
                                "status": "activo",
                                "companyId": 1,
                                "businessName": "Cliente 1 SA",
                            },
                            {
                                "id": 2,
                                "name": "Cliente 2",
                                "status": "activo",
                                "companyId": 1,
                                "businessName": "Cliente 2 SA",
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
    authorization: str = Header(..., description="Bearer Token", example="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."),
):
    company_id = get_company_id_from_token(authorization)
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


@router.get("/get-customers-by-company-user",
            summary="Listar clientes asignados a un usuario de la compañía.",
            description="Devuelve la lista de clientes de la compañía por usuario.",
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
                                "status": "activo",
                                "companyId": 1,
                                "businessName": "Cliente 1 SA",
                            },
                            {
                                "id": 2,
                                "name": "Cliente 2",
                                "status": "activo",
                                "companyId": 1,
                                "businessName": "Cliente 2 SA",
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
async def get_customers_by_company_user(
    authorization: str = Header(..., description="Bearer Token", example="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."),
):
    company_user_id = get_user_id_from_token(authorization)
    try:
        print("company_user_id: ", company_user_id)
        async with (await get_pool()).acquire() as conn:
            rows = await conn.fetch("SELECT fn_get_customers_by_company_user($1);", company_user_id)
            customers = [json.loads(row["fn_get_customers_by_company_user"]) for row in rows]
            return JSONResponse(
                content={
                    "info": "Clientes listados exitosamente",
                    "customers": customers,
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-categories-by-customer-and-company-user",
        summary="Listar categorías de informes que contrató un cliente.",
        description="Devuelve la lista de categorías de informes que contrató un cliente para un usuario de la compañía.",
        responses={
        200: {
            "description": "Ejecución exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "info": "Categorías listadas exitosamente",
                        "categories": [
                            {
                                "id": 1,
                                "name": "DDOS",
                                "description": "DDOS de la compañía",
                            },
                            {
                                "id": 2,
                                "name": "Pentesting",
                                "description": "Pentesting de la compañía",
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
                        "categories": []
                    }
                }
            },
        },
    }
)
async def get_categories_by_customer_and_company_user(
    authorization: str = Header(..., description="Bearer Token", example="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."),
    customerId: int = Query(..., description="ID del cliente", example=1),
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN, UserRole.COMPANY_USER]))
):
    company_user_id = get_user_id_from_token(authorization)
    try:
        async with (await get_pool()).acquire() as conn:
            rows = await conn.fetch("SELECT fn_get_categories_by_customer_and_company_user($1, $2);", company_user_id, customerId)
            categories = [json.loads(row["fn_get_categories_by_customer_and_company_user"]) for row in rows]
            print("categories: ", categories)
            return JSONResponse(
                content={
                    "info": "Categorías listadas exitosamente",
                    "categories": categories,
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



async def get_customer_by_id(customer_id: int):
    try:
        async with (await get_pool()).acquire() as conn:
            rows = await conn.fetch("SELECT fn_get_customer_by_id($1);", customer_id)

            if not rows or not rows[0]["fn_get_customer_by_id"]:
                raise HTTPException(status_code=404, detail=f"Cliente {customer_id} no encontrado")

            customer = json.loads(rows[0]["fn_get_customer_by_id"])
            return customer

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))