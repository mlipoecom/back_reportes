import bcrypt
import pyotp
from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta
from typing import Union, Dict, Any

from security import create_access_token, create_refresh_token, decode_token
from utils import (
    get_user_by_username, 
    update_login_attempts, 
    insert_log, 
    get_mfa_data_by_user_id,
    activate_mfa_in_db,
    get_user_data_by_id,
    consume_recovery_code,
    update_mfa_device_in_db
)
from mail import update_sent_mail
from models import LoginRequest, TokenResponse, MfaRequiredResponse, MfaVerifyRequest

router = APIRouter(
    prefix="/app",
    tags=["App"]
)

# ---  LOGIN INICIAL  ---

@router.post("/login",
             response_model=Union[TokenResponse, MfaRequiredResponse],
             summary="Login",
             description="Valida usuario y contraseña")
async def login(request: LoginRequest):
    user = await get_user_by_username(request.usuario)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # Bloqueos de seguridad
    if user.get("status") != "activo":
        raise HTTPException(status_code=403, detail="Usuario inhabilitado. Contacte soporte.")
    
    if user.get("entityStatus") != "activo":
        raise HTTPException(status_code=403, detail="Empresa inhabilitada. Contacte soporte.")
    
    role = user.get("role")
    user_id = user.get("ID")

    # Validación de Hash
    stored_hash = user.get("hashPassword")
    if not stored_hash or not bcrypt.checkpw(request.contraseña.encode("utf-8"), stored_hash.encode("utf-8")):
        await update_login_attempts(request.usuario, True)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # Reseteo de intentos
    await update_login_attempts(request.usuario, False)
    await update_sent_mail(request.usuario, False)

    if role == 1:

        user_data = await get_user_data_by_id(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        jwt_payload = {k: v for k, v in user_data.items() if k not in ["hashPassword", "recoveryCodes"]}
        
        access_token = create_access_token(jwt_payload)
        refresh_token = create_refresh_token(jwt_payload)

        # Log
        await insert_log(user_data.get("companyId"), user_id)
        
        return TokenResponse(accessToken=access_token, refreshToken=refresh_token)

    # Buscar estado MFA (Para el resto de los roles)
    mfa_data = await get_mfa_data_by_user_id(user_id)
    if not mfa_data:
        raise HTTPException(status_code=500, detail="Configuración MFA no encontrada")

    is_enabled = mfa_data.get("isEnabled")
    secret_db = mfa_data.get("mfaSecret")

    # Generar token temporal de MFA (5 minutos)
    mfa_payload = {"userId": user_id, "pendingMfa": True}
    mfa_token = create_access_token(mfa_payload, expires_delta=timedelta(seconds=300))

    # Respuesta según estado
    if is_enabled is True or str(is_enabled).lower() == 'true':
        return MfaRequiredResponse(
            requiresMfa=True,
            mfaStatus="enabled",
            mfaToken=mfa_token,
            mfaSecret=None
        )
    else:
        return MfaRequiredResponse(
            requiresMfa=True,
            mfaStatus="pending",
            mfaToken=mfa_token,
            mfaSecret=secret_db
        )

# --- VERIFICACIÓN MFA  ---

@router.post("/verify-mfa",
             response_model=TokenResponse,
             summary="Verificar MFA",
             description="Valida el código y entrega tokens finales")
async def verify_mfa(request: MfaVerifyRequest):
    # Validar el mfaToken temporal
    try:
        payload = decode_token(request.mfaToken)
        user_id = payload.get("userId")
        if not user_id or not payload.get("pendingMfa"):
            raise HTTPException(status_code=401, detail="Token MFA inválido o expirado")
    except Exception:
        raise HTTPException(status_code=401, detail="Sesión de verificación expirada")

    # Obtener el secreto de la base de datos
    mfa_data = await get_mfa_data_by_user_id(user_id)
    if not mfa_data:
        raise HTTPException(status_code=500, detail="Error al recuperar configuración MFA")

    secret = mfa_data.get("mfaSecret")
    is_already_enabled = mfa_data.get("isEnabled")
    recovery_hashes = mfa_data.get("recoveryCodes") or []
    input_code = request.code.strip().upper()

    mfa_authenticated = False
    
    # Verificación por código de recuperación
    if len(input_code) > 6:
        for h in recovery_hashes:
            if bcrypt.checkpw(input_code.encode("utf-8"), h.encode("utf-8")):
                await consume_recovery_code(user_id, h)
                mfa_authenticated = True
                break

    # Validar el código de 6 dígitos con pyotp
    if not mfa_authenticated:
        totp = pyotp.TOTP(secret)
        # valid_window=1 permite un desfase de 30s por si el reloj del celu no está exacto
        if totp.verify(request.code, valid_window=1):
            mfa_authenticated = True

    if not mfa_authenticated:
        raise HTTPException(status_code=401, detail="Código de verificación incorrecto")

    # Si era la primera vez (pending), activar en DB
    if not is_already_enabled:
        await activate_mfa_in_db(user_id)

    # Todo correcto: Generar tokens finales
    user_data = await get_user_data_by_id(user_id) 
    if not user_data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    jwt_payload = {k: v for k, v in user_data.items() if k not in ["hashPassword", "recoveryCodes"]}
    
    access_token = create_access_token(jwt_payload)
    refresh_token = create_refresh_token(jwt_payload)

    # Logs
    await insert_log(user_data.get("companyId"), user_data.get("ID"))
    
    return TokenResponse(accessToken=access_token, refreshToken=refresh_token)

# --- ASOCIAR NUEVO DISPOSITIVO ---

@router.post("/new-device",
             response_model=Dict[str, Any],
             summary="Generar nuevo secreto MFA",
             description="Genera un nuevo secreto para un nuevo dispositivo y lo actualiza en la DB")
async def new_mfa_device(request: MfaVerifyRequest): 
    try:
        payload = decode_token(request.mfaToken)
        user_id = payload.get("userId")
        if not user_id or not payload.get("pendingMfa"):
            raise HTTPException(status_code=401, detail="Token de sesión inválido")
    except Exception:
        raise HTTPException(status_code=401, detail="Sesión expirada")

    # Nuevo secreto 
    new_secret = pyotp.random_base32()

    try:
        success = await update_mfa_device_in_db(user_id, new_secret)
        
        if not success:
            raise HTTPException(status_code=500, detail="No se pudo actualizar el dispositivo")

        return {
            "status": "success",
            "message": "Nuevo secreto generado exitosamente",
            "mfaSecret": new_secret
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")