import random
import string
import json
from fastapi import HTTPException
from database import get_pool
from security import decode_token

def generate_safe_password(length: int = 10) -> str:
    characters = string.ascii_letters + string.digits + "!@#$%&*?"
    password_list = [
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%&*?")
    ]
    password_list.extend(random.choice(characters) for _ in range(length - 3))
    random.shuffle(password_list)
    return "".join(password_list)


async def get_user_by_username(user: str):
    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch("SELECT * FROM fn_get_user_data($1);", user)

    if not rows or len(rows) == 0:
        return None

    user_data = rows[0][0]
    if isinstance(user_data, str):
        user_data = json.loads(user_data)
    return user_data

async def update_login_attempts(user: str, failed: bool):
    async with (await get_pool()).acquire() as conn:
        await conn.execute("SELECT fn_update_login_attempts($1, $2);", user, failed)


async def insert_log(company: int, user:int) -> dict:
    p_company = int(company)
    p_user = int(user)
    cursor_name = "log_insert_result"
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "CALL sp_insert_log($1::integer, $2::integer, $3);",
                    p_company,
                    p_user,
                    cursor_name
                )

                rows = await conn.fetch(f'FETCH ALL IN "{cursor_name}";')

        if not rows:
            raise HTTPException(status_code=500, detail="El procedimiento no devolvió datos")

        return {"info": rows[0]["info"]}

    except Exception as e:
        msg = str(e).split("\n")[0].strip()
        raise HTTPException(status_code=500, detail=f"Error al insertar log: {msg}")
    
def get_company_id_from_token(authorization: str) -> int:
    """Extrae el companyId desde el token JWT."""
    try:
        token = authorization.split(" ")[1]
    except Exception:
        raise HTTPException(status_code=401, detail="Encabezado Authorization inválido")

    payload = decode_token(token)
    company_id = payload.get("companyId")

    if not company_id:
        raise HTTPException(status_code=401, detail="Token sin companyId")

    return company_id


def get_user_id_from_token(authorization: str) -> int:
    """Extrae el userId desde el token JWT."""
    try:
        token = authorization.split(" ")[1]
    except Exception:
        raise HTTPException(status_code=401, detail="Encabezado Authorization inválido")

    payload = decode_token(token)
    user_id = payload.get("ID")

    if not user_id:
        raise HTTPException(status_code=401, detail="Token sin userId")

    return user_id

