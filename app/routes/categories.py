from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from database import get_pool
from models import CategoryCreateRequest, CategoryUpdateRequest
from utils import get_supplier_id_from_token, get_user_id_from_token
import json

router = APIRouter(
    prefix="/categoria",
    tags=["Categorías"]
)

# -------------------------------
# CREATE CATEGORY
# -------------------------------
@router.post("/crear")
async def create_category(
    body: CategoryCreateRequest,
    authorization: str = Header(..., description="Bearer Token")
):

    supplier_id = get_supplier_id_from_token(authorization)
    user_id = get_user_id_from_token(authorization)

    mode = "CREATE"

    pool = await get_pool()

    async with pool.acquire() as conn:
        try:
            async with conn.transaction():

                cursor_name = "cur_inup_categories"

                await conn.execute(
                    """
                    CALL sp_inup_categories($1, $2, $3, $4, $5, $6, $7);
                    """,
                    mode,
                    0,
                    body.name,
                    body.description,
                    supplier_id,
                    user_id,
                    cursor_name
                )

                rows = await conn.fetch(f"FETCH ALL FROM {cursor_name}")

                if not rows:
                    raise HTTPException(500, "El procedimiento no devolvió datos.")

                row = rows[0]

                response = {k: row[k] for k in row.keys()}
                return JSONResponse(content=response)

        except Exception as e:
            raise HTTPException(500, str(e))


# -------------------------------
# UPDATE CATEGORY
# -------------------------------
@router.put("/editar/{category_id}")
async def update_category(
    category_id: int,
    body: CategoryUpdateRequest,
    authorization: str = Header(..., description="Bearer Token")
):

    supplier_id = get_supplier_id_from_token(authorization)
    user_id = get_user_id_from_token(authorization)

    mode = "EDIT"

    name = body.newName if body.newName is not None else None
    description = body.newDescription if body.newDescription is not None else None

    pool = await get_pool()

    async with pool.acquire() as conn:
        try:
            async with conn.transaction():

                cursor_name = "cur_inup_categories"

                await conn.execute(
                    """
                    CALL sp_inup_categories($1, $2, $3, $4, $5, $6, $7);
                    """,
                    mode,
                    category_id,
                    name,
                    description,
                    supplier_id,
                    user_id,
                    cursor_name
                )

                rows = await conn.fetch(f"FETCH ALL FROM {cursor_name}")

                if not rows:
                    raise HTTPException(500, "El procedimiento no devolvió datos.")

                row = rows[0]

                return JSONResponse(
                    content={k: row[k] for k in row.keys()}
                )

        except Exception as e:
            raise HTTPException(500, str(e))

# -------------------------------
# DELETE CATEGORY
# -------------------------------

@router.delete("/eliminar/{category_id}", summary="Elimina o inactiva una categoría")
async def delete_category(
    category_id: int,
    authorization: str = Header(..., description="Bearer Token")
):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")
    
    supplier_id = get_supplier_id_from_token(authorization)

    pool = await get_pool()

    async with pool.acquire() as conn:
        try:
            result = await conn.fetchval(
                "SELECT fn_delete_category($1,$2);",
                category_id,
                supplier_id
            )

            if result is None:
                raise HTTPException(500, "La función no devolvió datos")

            # <-- ESTA LÍNEA SOLUCIONA EL PROBLEMA
            parsed = json.loads(result)

            return JSONResponse(content=parsed)

        except Exception as e:
            raise HTTPException(500, str(e))

# -------------------------------
# LIST CATEGORIES
# -------------------------------
@router.get("/listar", summary="Lista todas las categorías de un proveedor")
async def get_categories(authorization: str = Header(..., description="Bearer Token")):
    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    token = authorization

    # Obtengo supplierId
    supplier_id = get_supplier_id_from_token(token)
    if supplier_id is None:
        raise HTTPException(status_code=401, detail="No se pudo obtener supplierId del token")

    pool = await get_pool()

    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM fn_get_categories($1)
                """,
                supplier_id
            )

            # Conversión
            categories = [json.loads(row[0]) for row in rows]

            return {"categories": categories}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))