from fastapi import APIRouter, HTTPException, Path, Header, Depends
from fastapi.responses import JSONResponse
import bcrypt
from .auth import get_user_by_username
from mail import send_new_password_email
from utils import generate_safe_password, get_supplier_id_from_token
from database import get_pool
from dependencies import require_roles
from roles import UserRole

router = APIRouter(
    prefix="/proveedor",
    tags=["Proveedores"]
)

@router.put("/usuario/{id}/cambiar-password",
            summary="Cambiar password",
            description="Genera un nuev password y la envía por correo al usuario",
            responses={
        200: {
            "description": "Password actualizado correctamente y correo enviado.",
            "content": {
                "application/json": {
                    "example": {
                        "ejecutado": True,
                        "info": "Password actualizado y correo enviado exitosamente"
                    }
                }
            },
        },
        500: {
            "description": "Error interno o fallo en el envío de correo.",
            "content": {
                "application/json": {
                    "example": {
                        "ejecutado": True,
                        "info": "Password actualizado pero no se pudo enviar el correo: error_smtp"
                    }
                }
            },
        },
    }
    )

async def change_password(
    id: str = Path(..., example="johnDoe123"),
    current_user: dict = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.SUPPLIER_ADMIN])),
    authorization: str = Header(..., description="Bearer Token")):
    # Valido token
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o faltante")

    token = authorization

    supplier_id = get_supplier_id_from_token(token)
    user = await get_user_by_username(id)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # Bloqueo si no está activo
    if user.get("status") != "activo":
        raise HTTPException(status_code=403, detail="Usuario inhabilitado. Contacte al vendedor")

    # Bloqueo si la empresa no está activa
    if user.get("entityStatus") != "activo":
        raise HTTPException(status_code=403, detail="Empresa inhabilitada. Contacte al vendedor")

    # Genero contraseña
    try:
        password = generate_safe_password()
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar contraseña: {e}")

    # Actualizo en base de datos
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.fetchval(
                "SELECT fn_change_password($1, $2, $3)",
                hashed_password,
                id,
                supplier_id
            )
            if result != 'OK':
                return {"ejecutado": False, "info": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar contraseña: {e}")

    # Envio correo con la nueva contraseña
    try:
        send_new_password_email(
            user_email=user.get("email"),
            full_name=f"{user.get('name', '')} {user.get('lastname', '')}",
            username=user.get("externalId", id),
            generated_password=password
        )
    except Exception as e:
        # En caso de fallo al enviar email, igual se actualizó la contraseña
        return JSONResponse(
            status_code=500,
            content={
                "info": f"Contraseña actualizada pero no se pudo enviar el correo: {e}",
                "ejecutado": True
            }
        )

    return {"ejecutado": True, "info": "Contraseña actualizada y correo enviado exitosamente"}
