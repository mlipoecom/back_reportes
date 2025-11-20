from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from database import get_pool
import json
from utils import get_company_id_from_token, get_user_id_from_token

router = APIRouter(
    prefix="/api",
    tags=["Api"]
)


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