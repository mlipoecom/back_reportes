"""
Tests para los endpoints de autenticación.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
import bcrypt
import pyotp
from app.routes.auth import login, verify_mfa, new_mfa_device
from app.models import LoginRequest, MfaVerifyRequest


@pytest.mark.asyncio
async def test_login_success_super_admin(mock_user_data, mock_db_pool):
    """Test de login exitoso para SUPER_ADMIN."""
    pool, conn = mock_db_pool
    
    # Mock de usuario con rol SUPER_ADMIN
    user_data = mock_user_data.copy()
    user_data["role"] = 1  # SUPER_ADMIN
    
    # Mock de contraseña hasheada
    password = "test_password"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_data["hashPassword"] = hashed
    
    # Mock de respuestas de la BD
    conn.fetchval = AsyncMock(return_value=None)
    conn.execute = AsyncMock()
    
    # Hacer patch donde se usa (en el módulo que importa)
    # Cuando se hace "from utils import get_user_by_username", la función está en app.routes.auth
    # get_pool no está importado en auth.py, pero las funciones de utils lo usan internamente
    # Por lo tanto, hacemos patch en utils donde se define
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.get_user_by_username", return_value=user_data):
            with patch("app.routes.auth.get_user_data_by_id", return_value=user_data):
                with patch("app.routes.auth.insert_log", return_value={"info": "OK"}):
                    with patch("app.routes.auth.update_login_attempts", return_value=None):
                        with patch("app.routes.auth.update_sent_mail", return_value=None):
                            with patch("app.routes.auth.create_access_token", return_value="access_token"):
                                with patch("app.routes.auth.create_refresh_token", return_value="refresh_token"):
                                        login_request = LoginRequest(usuario="test_user", contraseña=password)
                                        result = await login(login_request)
                                        
                                        assert result.accessToken == "access_token"
                                        assert result.refreshToken == "refresh_token"


@pytest.mark.asyncio
async def test_login_user_not_found(mock_db_pool):
    """Test de login con usuario no encontrado."""
    pool, conn = mock_db_pool
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.get_user_by_username", return_value=None):
            login_request = LoginRequest(usuario="nonexistent", contraseña="password")
            
            with pytest.raises(HTTPException) as exc_info:
                await login(login_request)
            
            assert exc_info.value.status_code == 401
            assert "incorrectos" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_login_invalid_password(mock_user_data, mock_db_pool):
    """Test de login con contraseña incorrecta."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    password = "correct_password"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_data["hashPassword"] = hashed
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.get_user_by_username", return_value=user_data):
            with patch("app.routes.auth.update_login_attempts", return_value=None):
                login_request = LoginRequest(usuario="test_user", contraseña="wrong_password")
                
                with pytest.raises(HTTPException) as exc_info:
                    await login(login_request)
                
                assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_user_inactive(mock_user_data, mock_db_pool):
    """Test de login con usuario inactivo."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    user_data["status"] = "inactivo"
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.get_user_by_username", return_value=user_data):
            login_request = LoginRequest(usuario="test_user", contraseña="password")
            
            with pytest.raises(HTTPException) as exc_info:
                await login(login_request)
            
            assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_login_entity_inactive(mock_user_data, mock_db_pool):
    """Test de login con entidad inactiva."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    user_data["entityStatus"] = "inactivo"
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.get_user_by_username", return_value=user_data):
            login_request = LoginRequest(usuario="test_user", contraseña="password")
            
            with pytest.raises(HTTPException) as exc_info:
                await login(login_request)
            
            assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_login_mfa_required(mock_user_data, mock_mfa_data, mock_db_pool):
    """Test de login que requiere MFA."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    user_data["role"] = 2  # SUPPLIER_ADMIN
    
    password = "test_password"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_data["hashPassword"] = hashed
    
    mfa_data = mock_mfa_data.copy()
    mfa_data["isEnabled"] = True
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.get_user_by_username", return_value=user_data):
            with patch("app.routes.auth.get_user_data_by_id", return_value=user_data):
                with patch("app.routes.auth.get_mfa_data_by_user_id", return_value=mfa_data):
                    with patch("app.routes.auth.update_login_attempts", return_value=None):
                        with patch("app.routes.auth.update_sent_mail", return_value=None):
                            with patch("app.routes.auth.create_access_token", return_value="mfa_token"):
                                with patch("app.config.DEV_CONFIG", {"DEBUG": False}):
                                    login_request = LoginRequest(usuario="test_user", contraseña=password)
                                    result = await login(login_request)
                                    
                                    assert result.requiresMfa is True
                                    assert result.mfaStatus == "enabled"
                                    assert result.mfaToken == "mfa_token"


@pytest.mark.asyncio
async def test_verify_mfa_success(mock_user_data, mock_mfa_data, mock_db_pool):
    """Test de verificación MFA exitosa."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    mfa_data = mock_mfa_data.copy()
    mfa_data["isEnabled"] = False
    
    # Generar código TOTP válido
    secret = mfa_data["mfaSecret"]
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    # Mock del payload del token MFA
    mfa_payload = {"userId": 1, "pendingMfa": True}
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.decode_token", return_value=mfa_payload):
            with patch("app.routes.auth.get_mfa_data_by_user_id", return_value=mfa_data):
                with patch("app.routes.auth.get_user_data_by_id", return_value=user_data):
                    with patch("app.routes.auth.activate_mfa_in_db", return_value=None):
                        with patch("app.routes.auth.insert_log", return_value={"info": "OK"}):
                            with patch("app.routes.auth.create_access_token", return_value="access_token"):
                                with patch("app.routes.auth.create_refresh_token", return_value="refresh_token"):
                                        mfa_request = MfaVerifyRequest(code=code, mfaToken="mfa_token")
                                        result = await verify_mfa(mfa_request)
                                        
                                        assert result.accessToken == "access_token"
                                        assert result.refreshToken == "refresh_token"


@pytest.mark.asyncio
async def test_verify_mfa_invalid_code(mock_mfa_data, mock_db_pool):
    """Test de verificación MFA con código inválido."""
    pool, conn = mock_db_pool
    
    mfa_data = mock_mfa_data.copy()
    mfa_payload = {"userId": 1, "pendingMfa": True}
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.decode_token", return_value=mfa_payload):
            with patch("app.routes.auth.get_mfa_data_by_user_id", return_value=mfa_data):
                mfa_request = MfaVerifyRequest(code="000000", mfaToken="mfa_token")
                
                with pytest.raises(HTTPException) as exc_info:
                    await verify_mfa(mfa_request)
                
                assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_mfa_invalid_token(mock_db_pool):
    """Test de verificación MFA con token inválido."""
    pool, conn = mock_db_pool
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.decode_token", side_effect=HTTPException(status_code=401, detail="Token inválido")):
            mfa_request = MfaVerifyRequest(code="123456", mfaToken="invalid_token")
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_mfa(mfa_request)
            
            assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_new_mfa_device_success(mock_db_pool):
    """Test de generación de nuevo dispositivo MFA."""
    pool, conn = mock_db_pool
    
    mfa_payload = {"userId": 1, "pendingMfa": True}
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.decode_token", return_value=mfa_payload):
            with patch("app.routes.auth.update_mfa_device_in_db", return_value=True):
                mfa_request = MfaVerifyRequest(code="123456", mfaToken="mfa_token")
                result = await new_mfa_device(mfa_request)
                
                assert result["status"] == "success"
                assert "mfaSecret" in result


@pytest.mark.asyncio
async def test_new_mfa_device_invalid_token(mock_db_pool):
    """Test de nuevo dispositivo MFA con token inválido."""
    pool, conn = mock_db_pool
    
    with patch("app.utils.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.auth.decode_token", side_effect=HTTPException(status_code=401, detail="Token inválido")):
            mfa_request = MfaVerifyRequest(code="123456", mfaToken="invalid_token")
            
            with pytest.raises(HTTPException) as exc_info:
                await new_mfa_device(mfa_request)
            
            assert exc_info.value.status_code == 401

