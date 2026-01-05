"""
Tests para los endpoints de proveedores (suppliers).
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.suppliers import (
    generate_and_create_company, generate_and_create_customer,
    get_companies, get_roles, get_users_by_supplier,
    delete_company, edit_company
)
from app.models import CompanyGenerate, CustomerGenerate, CompanyUpdate


@pytest.mark.asyncio
async def test_create_company_success(mock_supplier_admin_user, mock_db_pool):
    """Test de creación de empresa exitosa."""
    pool, conn = mock_db_pool
    
    from tests.conftest import create_mock_record
    company_result = {
        "info": "Compañía creada exitosamente.",
        "id": 1
    }
    
    mock_row = create_mock_record(company_result)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.suppliers.get_pool", new_callable=AsyncMock, return_value=pool):
        company_data = CompanyGenerate(
            name="Acme",
            businessName="Acme SA",
            externalId="acme123",
            description="Empresa de ejemplo",
            status="activo",
            email="info@acme.com"
        )
        result = await generate_and_create_company(company_data, mock_supplier_admin_user)
        
        assert result.id == 1
        assert "exitosamente" in result.info.lower()


@pytest.mark.asyncio
async def test_create_company_duplicate_external_id(mock_supplier_admin_user, mock_db_pool):
    """Test de creación de empresa con ID externo duplicado."""
    pool, conn = mock_db_pool
    
    from tests.conftest import create_mock_record
    company_result = {
        "info": "Ya existe una compañía con el mismo ID externo.",
        "id": 0
    }
    
    mock_row = create_mock_record(company_result)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.suppliers.get_pool", new_callable=AsyncMock, return_value=pool):
        company_data = CompanyGenerate(
            name="Acme",
            businessName="Acme SA",
            externalId="duplicate_id",
            description="Empresa de ejemplo",
            status="activo",
            email="info@acme.com"
        )
        from fastapi.responses import JSONResponse
        result = await generate_and_create_company(company_data, mock_supplier_admin_user)
        
        assert result.status_code == 400


@pytest.mark.asyncio
async def test_create_customer_success(mock_supplier_admin_user, mock_db_pool):
    """Test de creación de cliente exitosa."""
    pool, conn = mock_db_pool
    
    from tests.conftest import create_mock_record
    customer_result = {
        "info": "Cliente creado exitosamente.",
        "id": 1
    }
    
    mock_row = create_mock_record(customer_result)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.suppliers.get_pool", new_callable=AsyncMock, return_value=pool):
        customer_data = CustomerGenerate(
            name="Cliente Test",
            businessName="Cliente Test SA",
            externalId="cliente123",
            description="Cliente de ejemplo",
            status="activo",
            companyId=1,
            email="cliente@test.com"
        )
        result = await generate_and_create_customer(customer_data, mock_supplier_admin_user)
        
        assert result.id == 1
        assert "exitosamente" in result.info.lower()


@pytest.mark.asyncio
async def test_get_companies_success(mock_supplier_admin_user, mock_db_pool):
    """Test de listado de empresas exitoso."""
    pool, conn = mock_db_pool
    
    from tests.conftest import create_mock_record
    companies_data = [
        {"id": 1, "name": "Acme", "status": "activo"},
        {"id": 2, "name": "Beta", "status": "activo"}
    ]
    
    mock_rows = [create_mock_record({"fn_get_companies": json.dumps(comp)}) for comp in companies_data]
    conn.fetch = AsyncMock(return_value=mock_rows)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.suppliers.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_companies(
            name=None,
            businessName=None,
            externalId=None,
            companyId=None,
            status=None,
            limit=10,
            offset=0,
            current_user=mock_supplier_admin_user
        )
        
        assert "companies" in result
        assert len(result["companies"]) == 2


@pytest.mark.asyncio
async def test_get_roles_success(mock_supplier_admin_user, mock_db_pool):
    """Test de listado de roles exitoso."""
    pool, conn = mock_db_pool
    
    from tests.conftest import create_mock_record
    roles_data = [
        {"id": 1, "name": "SUPER_ADMIN"},
        {"id": 2, "name": "SUPPLIER_ADMIN"}
    ]
    
    mock_rows = [create_mock_record({"fn_get_roles": json.dumps(role)}) for role in roles_data]
    conn.fetch = AsyncMock(return_value=mock_rows)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.suppliers.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_roles(mock_supplier_admin_user)
        
        assert "roles" in result
        assert len(result["roles"]) == 2


@pytest.mark.asyncio
async def test_get_users_by_supplier_success(mock_supplier_admin_user, mock_db_pool):
    """Test de listado de usuarios por proveedor exitoso."""
    pool, conn = mock_db_pool
    
    users_data = {
        "total": 10,
        "page": 1,
        "pageSize": 20,
        "data": [
            {"id": 1, "name": "Usuario 1", "status": "activo"},
            {"id": 2, "name": "Usuario 2", "status": "activo"}
        ]
    }
    
    conn.fetchval = AsyncMock(return_value=json.dumps(users_data))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.suppliers.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_users_by_supplier(
            page=1,
            pageSize=20,
            name=None,
            lastName=None,
            entityId=None,
            roleId=None,
            status=None,
            current_user=mock_supplier_admin_user
        )
        
        assert result["pagination"]["total"] == 10
        assert len(result["users"]) == 2


@pytest.mark.asyncio
async def test_delete_company_success(mock_supplier_admin_user, mock_db_pool):
    """Test de eliminación de empresa exitosa."""
    pool, conn = mock_db_pool
    
    result_data = {
        "message": "Empresa eliminada correctamente",
        "affectedRows": 1
    }
    
    mock_row = MagicMock()
    mock_row.__getitem__.return_value = json.dumps(result_data)
    conn.fetchrow = AsyncMock(return_value=mock_row)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.suppliers.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await delete_company(1, mock_supplier_admin_user)
        
        assert result["affectedRows"] == 1


@pytest.mark.asyncio
async def test_edit_company_success(mock_supplier_admin_user, mock_db_pool):
    """Test de edición de empresa exitosa."""
    pool, conn = mock_db_pool
    
    result_data = {
        "message": "Empresa modificada correctamente",
        "affectedRows": 1
    }
    
    mock_row = MagicMock()
    mock_row.__getitem__.return_value = result_data
    conn.fetchrow = AsyncMock(return_value=mock_row)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.suppliers.get_pool", new_callable=AsyncMock, return_value=pool):
        company_data = CompanyUpdate(
            name="Acme Updated",
            businessName="Acme SA Updated",
            externalId="acme123",
            description="Descripción actualizada",
            email="info@acme.com"
        )
        result = await edit_company(1, company_data, mock_supplier_admin_user)
        
        assert result["affectedRows"] == 1

