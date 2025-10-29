from fastapi import APIRouter, HTTPException
import bcrypt
from ..security import create_access_token, create_refresh_token
from ..utils import get_user_by_username, update_login_attempts, insert_log
from ..mail import update_sent_mail
from ..models import LoginRequest, TokenResponse

router = APIRouter(
    prefix="/api",
    tags=["Api"]
)

@router.post("/login",
             response_model=TokenResponse,
             summary="Login",
             description="Acceso al portal",
             responses={
                    200: {
                        "description": "Ejecución exitosa",
                        "content": {
                            "application/json": {
                                "example": {
                                    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9............",
                                    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9............"
                                }
                            }
                        },
                    },
                    401: {
                        "description": "Ejecución fallida",
                        "content": {
                            "application/json": {
                                "example": {
                                    "detail": "Usuario o contraseña incorrectos"
                                }
                            }
                        },
                    },
                    500: {
                        "description": "Error interno del servidor",
                        "content": {
                            "application/json": {
                                "example": {
                                    "info": "Error en la BD: conexión fallida"
                                }
                            }
                        },
                    },
                }
             )

async def login(request: LoginRequest):
    user = await get_user_by_username(request.usuario)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    #  Bloqueo si usuario no está activo
    if user.get("status") != "activo":
        raise HTTPException(status_code=403, detail="Usuario inhabilitado. Contacte al vendedor")
    
    #  Bloqueo si la empresa no está activa
    if user.get("companyStatus") != "activo":
        raise HTTPException(status_code=403, detail="Empresa inhabilitada. Contacte al vendedor")

    stored_hash = user.get("hashPassword")
    if not stored_hash or not bcrypt.checkpw(request.contraseña.encode("utf-8"), stored_hash.encode("utf-8")):
        # incremento de intentos fallidos
        await update_login_attempts(request.usuario, True)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # login exitoso 
    # → reseteo de intentos fallidos
    await update_login_attempts(request.usuario, False)
    # → reseteo de envío de mails
    await update_sent_mail(request.usuario, False)

    jwt_payload = {k: v for k, v in user.items() if k != "hashPassword"}
    access_token = create_access_token(jwt_payload)
    refresh_token = create_refresh_token(jwt_payload)

    await insert_log(user.get("companyId"), user.get("ID"))
    return TokenResponse(accessToken=access_token, refreshToken=refresh_token)
