"""
Tests para los endpoints de empresas.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.companies import (
    assign_client, get_customers, get_users, 
    get_customers_by_company_user, get_categories_by_customer_and_company_user
)
from app.models import AssignClientRequest


@pytest.mark.asyncio
async def test_assign_client_success(mock_company_admin_user, mock_db_pool):
    """Test de asignación de cliente exitosa."""
    pool, conn = mock_db_pool
    
    result_data = {
        "message": "Cliente asignado exitosamente",
        "inserted_count": 2,
        "inserted_categories": [1, 2],
        "failed_categories": []
    }
    
    # Crear mock_row usando el helper de conftest
    from tests.conftest import create_mock_record
    mock_row = create_mock_record(result_data)
    
    # Usar funciones async simples en lugar de AsyncMock para evitar el error
    # "another operation is in progress"
    async def mock_execute(*args, **kwargs):
        return None
    
    async def mock_fetch(*args, **kwargs):
        return [mock_row]
    
    conn.execute = mock_execute
    conn.fetch = mock_fetch
    
    # Patch get_pool en el módulo donde se usa
    with patch("app.routes.companies.get_pool", new_callable=AsyncMock, return_value=pool):
        body = AssignClientRequest(userId=1, customerId=1, categoryIds=[1, 2])
        result = await assign_client(body, current_user=mock_company_admin_user)
        
        assert result["message"] == "Cliente asignado exitosamente"
        assert result["insertedCount"] == 2


@pytest.mark.asyncio
async def test_assign_client_no_data(mock_company_admin_user, mock_db_pool):
    """Test de asignación de cliente sin datos devueltos."""
    pool, conn = mock_db_pool
    
    # Usar funciones async simples en lugar de AsyncMock
    async def mock_execute(*args, **kwargs):
        return None
    
    async def mock_fetch(*args, **kwargs):
        return []
    
    conn.execute = mock_execute
    conn.fetch = mock_fetch
    
    # Patch get_pool en el módulo donde se usa
    with patch("app.routes.companies.get_pool", new_callable=AsyncMock, return_value=pool):
        body = AssignClientRequest(userId=1, customerId=1, categoryIds=[1, 2])
        
        with pytest.raises(HTTPException) as exc_info:
            await assign_client(body, current_user=mock_company_admin_user)
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_customers_success(mock_company_admin_user, mock_db_pool):
    """Test de listado de clientes exitoso."""
    pool, conn = mock_db_pool
    
    customers_data = [
        {"id": 1, "name": "Cliente 1", "status": "activo"},
        {"id": 2, "name": "Cliente 2", "status": "activo"}
    ]
    
    # Crear mock_rows usando el helper de conftest
    from tests.conftest import create_mock_record
    mock_rows = [create_mock_record({"fn_get_customers": json.dumps(cat)}) for cat in customers_data]
    
    # Usar función async simple en lugar de AsyncMock
    async def mock_fetch(*args, **kwargs):
        return mock_rows
    
    conn.fetch = mock_fetch
    
    # Patch get_pool en el módulo donde se usa
    with patch("app.routes.companies.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_customers(current_user=mock_company_admin_user)
        
        assert result.status_code == 200
        data = json.loads(result.body.decode('utf-8'))
        assert len(data["customers"]) == 2


@pytest.mark.asyncio
async def test_get_users_success(mock_company_admin_user, mock_db_pool):
    """Test de listado de usuarios exitoso."""
    pool, conn = mock_db_pool
    
    users_data = {
        "totalCount": 10,
        "users": [
            {"id": 1, "name": "Usuario 1", "status": "activo"},
            {"id": 2, "name": "Usuario 2", "status": "activo"}
        ]
    }
    
    # Usar función async simple en lugar de AsyncMock
    async def mock_fetchval(*args, **kwargs):
        return json.dumps(users_data)
    
    conn.fetchval = mock_fetchval
    
    # Patch get_pool en el módulo donde se usa
    with patch("app.routes.companies.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_users(
            name=None,
            last_name=None,
            user_id=None,
            user_name=None,
            status=None,
            role=None,
            page=1,
            page_size=20,
            current_user=mock_company_admin_user
        )
        
        assert result.status_code == 200
        data = json.loads(result.body.decode('utf-8'))
        assert data["totalCount"] == 10
        assert len(data["users"]) == 2


@pytest.mark.asyncio
async def test_get_customers_by_company_user_success(mock_company_user, mock_db_pool):
    """Test de listado de clientes por usuario de compañía exitoso."""
    pool, conn = mock_db_pool
    
    customers_data = [
        {"id": 1, "name": "Cliente 1", "status": "activo"}
    ]
    
    # Crear mock_rows usando el helper de conftest
    from tests.conftest import create_mock_record
    mock_rows = [create_mock_record({"fn_get_customers_by_company_user": json.dumps(cat)}) for cat in customers_data]
    
    # Usar función async simple en lugar de AsyncMock
    async def mock_fetch(*args, **kwargs):
        return mock_rows
    
    conn.fetch = mock_fetch
    
    # Patch get_pool en el módulo donde se usa
    with patch("app.routes.companies.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_customers_by_company_user(
            current_user=mock_company_user,
            p_user_id=None
        )
        
        assert result.status_code == 200
        data = json.loads(result.body.decode('utf-8'))
        assert len(data["customers"]) == 1


@pytest.mark.asyncio
async def test_get_categories_by_customer_and_company_user_success(mock_company_user, mock_db_pool):
    """Test de listado de categorías por cliente y usuario exitoso."""
    pool, conn = mock_db_pool
    
    categories_data = [
        {"id": 1, "name": "DDOS", "description": "Categoría DDOS"}
    ]
    
    # Crear mock_rows usando el helper de conftest
    from tests.conftest import create_mock_record
    mock_rows = [create_mock_record({"fn_get_categories_by_customer_and_company_user": json.dumps(cat)}) for cat in categories_data]
    
    # Usar función async simple en lugar de AsyncMock
    async def mock_fetch(*args, **kwargs):
        return mock_rows
    
    conn.fetch = mock_fetch
    
    # Patch get_pool en el módulo donde se usa
    with patch("app.routes.companies.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_categories_by_customer_and_company_user(
            customerId=1,
            p_user_id=None,
            current_user=mock_company_user
        )
        
        assert result.status_code == 200
        data = json.loads(result.body.decode('utf-8'))
        assert len(data["categories"]) == 1

