"""
Tests para los endpoints de ECOM.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.ecom import generate_and_create_supplier, get_suppliers, delete_supplier
from app.models import SupplierGenerate


@pytest.mark.asyncio
async def test_create_supplier_success(mock_super_admin_user, mock_db_pool):
    """Test de creación de proveedor exitosa."""
    pool, conn = mock_db_pool
    
    supplier_result = {
        "info": "Proveedor creado exitosamente.",
        "id": 1
    }
    
    mock_row = MagicMock()
    mock_row.get.side_effect = lambda key: supplier_result.get(key)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.ecom.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.ecom.generate_and_create_user", return_value=MagicMock(id=2)):
            with patch("app.routes.ecom.assign_roles", return_value=None):
                supplier_data = SupplierGenerate(
                    name="Ecom",
                    businessName="Ecom Center SRL",
                    externalId="ecom123",
                    description="Proveedor de ejemplo",
                    status="activo",
                    email="info@ecom.com.uy"
                )
                result = await generate_and_create_supplier(supplier_data, mock_super_admin_user)
                
                assert result.id == 1
                assert "exitosamente" in result.info.lower()


@pytest.mark.asyncio
async def test_create_supplier_duplicate_external_id(mock_super_admin_user, mock_db_pool):
    """Test de creación de proveedor con ID externo duplicado."""
    pool, conn = mock_db_pool
    
    supplier_result = {
        "info": "Ya existe un proveedor con el mismo ID externo",
        "id": 0
    }
    
    mock_row = MagicMock()
    mock_row.get.side_effect = lambda key: supplier_result.get(key)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.ecom.get_pool", new_callable=AsyncMock, return_value=pool):
        supplier_data = SupplierGenerate(
            name="Ecom",
            businessName="Ecom Center SRL",
            externalId="duplicate_id",
            description="Proveedor de ejemplo",
            status="activo",
            email="info@ecom.com.uy"
        )
        from fastapi.responses import JSONResponse
        result = await generate_and_create_supplier(supplier_data, mock_super_admin_user)
        
        assert result.status_code == 400


@pytest.mark.asyncio
async def test_get_suppliers_success(mock_super_admin_user, mock_db_pool):
    """Test de listado de proveedores exitoso."""
    pool, conn = mock_db_pool
    
    suppliers_data = [
        {"id": 1, "name": "Ecom", "status": "activo"},
        {"id": 2, "name": "Acme", "status": "activo"}
    ]
    
    from tests.conftest import create_mock_record
    mock_rows = [create_mock_record({"fn_get_supplier": json.dumps(sup)}) for sup in suppliers_data]
    conn.fetch = AsyncMock(return_value=mock_rows)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.ecom.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_suppliers(
            id=None,
            name=None,
            businessName=None,
            externalId=None,
            limit=10,
            offset=0,
            current_user=mock_super_admin_user
        )
        
        assert "proveedores" in result
        assert len(result["proveedores"]) == 2


@pytest.mark.asyncio
async def test_get_suppliers_with_filters(mock_super_admin_user, mock_db_pool):
    """Test de listado de proveedores con filtros."""
    pool, conn = mock_db_pool
    
    suppliers_data = [
        {"id": 1, "name": "Ecom", "status": "activo"}
    ]
    
    from tests.conftest import create_mock_record
    mock_rows = [create_mock_record({"fn_get_supplier": json.dumps(sup)}) for sup in suppliers_data]
    conn.fetch = AsyncMock(return_value=mock_rows)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.ecom.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_suppliers(
            id=1,
            name="Ecom",
            businessName=None,
            externalId=None,
            limit=10,
            offset=0,
            current_user=mock_super_admin_user
        )
        
        assert "proveedores" in result
        assert len(result["proveedores"]) == 1


@pytest.mark.asyncio
async def test_delete_supplier_success(mock_super_admin_user, mock_db_pool):
    """Test de eliminación de proveedor exitosa."""
    pool, conn = mock_db_pool
    
    result_data = {
        "message": "Proveedor eliminado correctamente",
        "affectedRows": 1
    }
    
    mock_row = MagicMock()
    mock_row.__getitem__.return_value = json.dumps(result_data)
    conn.fetchrow = AsyncMock(return_value=mock_row)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.ecom.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await delete_supplier(1, mock_super_admin_user)
        
        assert result["affectedRows"] == 1


@pytest.mark.asyncio
async def test_delete_supplier_not_found(mock_super_admin_user, mock_db_pool):
    """Test de eliminación de proveedor no encontrado."""
    pool, conn = mock_db_pool
    
    result_data = {
        "message": "El proveedor no existe",
        "affectedRows": 0
    }
    
    mock_row = MagicMock()
    mock_row.__getitem__.return_value = json.dumps(result_data)
    conn.fetchrow = AsyncMock(return_value=mock_row)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.ecom.get_pool", new_callable=AsyncMock, return_value=pool):
        from fastapi.responses import JSONResponse
        result = await delete_supplier(999, mock_super_admin_user)
        
        assert result.status_code == 404


@pytest.mark.asyncio
async def test_delete_supplier_no_data(mock_super_admin_user, mock_db_pool):
    """Test de eliminación de proveedor sin datos devueltos."""
    pool, conn = mock_db_pool
    
    conn.fetchrow = AsyncMock(return_value=None)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.ecom.get_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(HTTPException) as exc_info:
            await delete_supplier(1, mock_super_admin_user)
        
        assert exc_info.value.status_code == 500

