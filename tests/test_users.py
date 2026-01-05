"""
Tests para los endpoints de usuarios.
"""
import pytest
import json
import bcrypt
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.users import (
    generate_and_create_user, edit_user, delete_user,
    assign_roles
)
from app.routes.companies import assign_client
from app.models import UserGenerate, UserUpdate, AssignRolesRequest, AssignClientRequest


@pytest.mark.asyncio
async def test_create_user_success(mock_supplier_admin_user, mock_db_pool):
    """Test de creación de usuario exitosa."""
    pool, conn = mock_db_pool
    
    from tests.conftest import create_mock_record
    user_result = {
        "info": "Usuario creado exitosamente.",
        "id": 1
    }
    
    mock_row = create_mock_record(user_result)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    mfa_result = {"message": "MFA configurado exitosamente"}
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.users.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.users.assign_role_to_user", new_callable=AsyncMock, return_value=None):
            with patch("app.routes.users.call_sp_insert_user_mfa", new_callable=AsyncMock, return_value=mfa_result):
                with patch("app.routes.users.send_user_password_email", return_value=None):
                    with patch("app.routes.users.generate_safe_password", return_value="TestPassword123!"):
                        with patch("app.routes.users.bcrypt.gensalt", return_value=b"$2b$12$test"):
                            with patch("app.routes.users.bcrypt.hashpw", return_value=b"$2b$12$hashed"):
                                with patch("app.routes.users.pyotp.random_base32", return_value="TESTBASE32"):
                                    recovery_keys = ["key1", "key2", "key3", "key4"]
                                    with patch("app.routes.users.recovery_keys_generate", return_value=recovery_keys):
                                        with patch("app.routes.users.hash_keys", return_value=["hashed1", "hashed2"]):
                                            user_data = UserGenerate(
                                                name="John",
                                                lastName="Doe",
                                                email="john@example.com",
                                                externalId="johnDoe123",
                                                supplierId=1,
                                                companyId=None,
                                                customerId=None,
                                                status="activo",
                                                role="supplier_admin"
                                            )
                                            result = await generate_and_create_user(user_data, mock_supplier_admin_user)
                                            
                                            assert result.id == 1
                                            assert "exitosamente" in result.info.lower()


@pytest.mark.asyncio
async def test_create_user_duplicate_external_id(mock_supplier_admin_user, mock_db_pool):
    """Test de creación de usuario con ID externo duplicado."""
    pool, conn = mock_db_pool
    
    from tests.conftest import create_mock_record
    user_result = {
        "info": "Ya existe un usuario con el mismo ID externo.",
        "id": 0
    }
    
    mock_row = create_mock_record(user_result)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.users.get_pool", new_callable=AsyncMock, return_value=pool):
        user_data = UserGenerate(
            name="John",
            lastName="Doe",
            email="john@example.com",
            externalId="duplicate_id",
            supplierId=1,
            companyId=None,
            customerId=None,
            status="activo",
            role=None
        )
        from fastapi.responses import JSONResponse
        result = await generate_and_create_user(user_data, mock_supplier_admin_user)
        
        assert result.status_code == 400


@pytest.mark.asyncio
async def test_edit_user_success(mock_supplier_admin_user, mock_db_pool):
    """Test de edición de usuario exitosa."""
    pool, conn = mock_db_pool
    
    user_result = {
        "info": "Usuario modificado exitosamente.",
        "id": 1
    }
    
    conn.fetchval = AsyncMock(return_value=json.dumps(user_result))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.users.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.users.assign_role_to_user", return_value=None):
            user_data = UserUpdate(
                name="John Updated",
                lastName="Doe",
                email="john.updated@example.com",
                externalId="johnDoe123",
                supplierId=1,
                companyId=None,
                customerId=None,
                status="activo",
                role="supplier_admin"
            )
            result = await edit_user(user_data, 1, mock_supplier_admin_user)
            
            assert result.id == 1
            assert "exitosamente" in result.info.lower()


@pytest.mark.asyncio
async def test_delete_user_success(mock_supplier_admin_user, mock_db_pool):
    """Test de eliminación de usuario exitosa."""
    pool, conn = mock_db_pool
    
    result_data = {
        "message": "Usuario eliminado exitosamente",
        "affectedRows": 1
    }
    
    conn.fetchval = AsyncMock(return_value=json.dumps(result_data))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.users.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await delete_user(1, mock_supplier_admin_user)
        
        assert result.status_code == 200
        data = json.loads(result.body)
        assert data["affectedRows"] == 1


@pytest.mark.asyncio
async def test_delete_user_not_found(mock_supplier_admin_user, mock_db_pool):
    """Test de eliminación de usuario no encontrado."""
    pool, conn = mock_db_pool
    
    result_data = {
        "message": "Usuario no encontrado",
        "affectedRows": 0
    }
    
    conn.fetchval = AsyncMock(return_value=json.dumps(result_data))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.users.get_pool", new_callable=AsyncMock, return_value=pool):
        from fastapi.responses import JSONResponse
        result = await delete_user(999, mock_supplier_admin_user)
        
        assert result.status_code == 400


@pytest.mark.asyncio
async def test_assign_roles_success(mock_supplier_admin_user, mock_db_pool):
    """Test de asignación de roles exitosa."""
    pool, conn = mock_db_pool
    
    cursor_result = {"message": "Rol asignado exitosamente"}
    mock_row = MagicMock()
    mock_row.get.side_effect = lambda key: cursor_result.get(key)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.users.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.users.assign_role_to_user", return_value=None):
            payload = AssignRolesRequest(user_id=1, role_id=2)
            from fastapi.responses import JSONResponse
            result = await assign_roles(payload, mock_supplier_admin_user)
            
            assert result.status_code == 200
            data = json.loads(result.body)
            assert "exitosamente" in data["info"].lower()


@pytest.mark.asyncio
async def test_assign_client_success(mock_supplier_admin_user, mock_db_pool):
    """Test de asignación de cliente exitosa."""
    pool, conn = mock_db_pool
    
    from tests.conftest import create_mock_record
    result_data = {
        "message": "Cliente asignado exitosamente",
        "inserted_count": 2,
        "inserted_categories": [1, 2],
        "failed_categories": []
    }
    
    mock_row = create_mock_record(result_data)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.companies.get_pool", new_callable=AsyncMock, return_value=pool):
        body = AssignClientRequest(userId=1, customerId=1, categoryIds=[1, 2])
        result = await assign_client(body, mock_supplier_admin_user)
        
        assert result["message"] == "Cliente asignado exitosamente"
        assert result["insertedCount"] == 2


@pytest.mark.asyncio
async def test_assign_client_no_data(mock_supplier_admin_user, mock_db_pool):
    """Test de asignación de cliente sin datos devueltos."""
    pool, conn = mock_db_pool
    
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.companies.get_pool", new_callable=AsyncMock, return_value=pool):
        body = AssignClientRequest(userId=1, customerId=1, categoryIds=[1, 2])
        
        with pytest.raises(HTTPException) as exc_info:
            await assign_client(body, mock_supplier_admin_user)
        
        assert exc_info.value.status_code == 500

