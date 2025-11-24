from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from database import get_pool
from models import CategoryCreateRequest, CategoryUpdateRequest
from dependencies import require_roles
from roles import UserRole
import json

router = APIRouter(
    prefix="/categoria",
    tags=["Categorías"]
)


@router.post("/crear")
async def create_category(
    body: CategoryCreateRequest,
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))
):

    supplier_id = current_user.get("supplierId")
    user_id = current_user.get("ID")

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
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN]))
):

    supplier_id = current_user.get("supplierId")
    user_id = current_user.get("ID")

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


@router.get("/lista", summary="Lista todas las categorías de un proveedor")
async def get_categories(
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN, UserRole.CUSTOMER_ADMIN, UserRole.CUSTOMER_USER, UserRole.COMPANY_ADMIN, UserRole.COMPANY_USER]))
):
    # Obtengo supplierId
    supplier_id = current_user.get("supplierId")
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