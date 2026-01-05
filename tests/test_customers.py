"""
Tests para los endpoints de clientes.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.customers import update_customer, delete_customer
from app.models import CustomerUpdate


@pytest.mark.asyncio
async def test_update_customer_success(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de cliente exitosa."""
    pool, conn = mock_db_pool
    
    conn.fetchval = AsyncMock(return_value="Cliente actualizado exitosamente.")
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.customers.get_pool", new_callable=AsyncMock, return_value=pool):
        customer_data = CustomerUpdate(
            name="Nuevo Nombre",
            businessName="Nueva Razón Social",
            email="nuevo@email.com",
            description="Nueva descripción"
        )
        result = await update_customer(customer_data, 1, mock_supplier_admin_user)
        
        assert "message" in result
        assert "exitosamente" in result["message"].lower()


@pytest.mark.asyncio
async def test_update_customer_not_found(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de cliente no encontrado."""
    pool, conn = mock_db_pool
    
    conn.fetchval = AsyncMock(return_value="Cliente no encontrado.")
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.customers.get_pool", new_callable=AsyncMock, return_value=pool):
        customer_data = CustomerUpdate(
            name="Nuevo Nombre",
            businessName="Nueva Razón Social",
            email="nuevo@email.com",
            description="Nueva descripción"
        )
        result = await update_customer(customer_data, 999, mock_supplier_admin_user)
        
        assert "message" in result


@pytest.mark.asyncio
async def test_delete_customer_success(mock_supplier_admin_user, mock_db_pool):
    """Test de eliminación de cliente exitosa."""
    pool, conn = mock_db_pool
    
    result_data = "Cliente eliminado exitosamente"
    
    conn.fetchval = AsyncMock(return_value=result_data)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.customers.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await delete_customer(1, mock_supplier_admin_user)
        
        assert result == result_data
        assert "eliminado" in str(result).lower()


@pytest.mark.asyncio
async def test_delete_customer_not_found(mock_supplier_admin_user, mock_db_pool):
    """Test de eliminación de cliente no encontrado."""
    pool, conn = mock_db_pool
    
    result_data = "Cliente no encontrado"
    
    conn.fetchval = AsyncMock(return_value=result_data)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.customers.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await delete_customer(999, mock_supplier_admin_user)
        
        # La función devuelve el resultado directamente, no lanza excepción
        assert result == result_data


@pytest.mark.asyncio
async def test_update_customer_db_error(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de cliente con error en BD."""
    pool, conn = mock_db_pool
    
    conn.fetchval = AsyncMock(side_effect=Exception("Error en BD"))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.customers.get_pool", new_callable=AsyncMock, return_value=pool):
        customer_data = CustomerUpdate(
            name="Nuevo Nombre",
            businessName="Nueva Razón Social",
            email="nuevo@email.com",
            description="Nueva descripción"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await update_customer(customer_data, 1, mock_supplier_admin_user)
        
        assert exc_info.value.status_code == 500

