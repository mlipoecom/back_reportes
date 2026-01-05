"""
Tests para los endpoints de categorías.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.categories import create_category, update_category, delete_category, get_categories
from app.models import CategoryCreateRequest, CategoryUpdateRequest
from tests.conftest import create_mock_record


@pytest.mark.asyncio
async def test_create_category_success(mock_supplier_admin_user, mock_db_pool):
    """Test de creación de categoría exitosa."""
    pool, conn = mock_db_pool
    
    category_data = {
        "id": 1,
        "name": "DDOS",
        "description": "Categoría de DDOS",
        "info": "Categoría creada exitosamente"
    }
    
    mock_row = create_mock_record(category_data)
    
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.categories.get_pool", new_callable=AsyncMock, return_value=pool):
        body = CategoryCreateRequest(name="DDOS", description="Categoría de DDOS")
        result = await create_category(body, mock_supplier_admin_user)
        
        assert result.status_code == 200
        assert "DDOS" in str(result.body)


@pytest.mark.asyncio
async def test_create_category_no_data_returned(mock_supplier_admin_user, mock_db_pool):
    """Test de creación de categoría sin datos devueltos."""
    pool, conn = mock_db_pool
    
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.categories.get_pool", new_callable=AsyncMock, return_value=pool):
        body = CategoryCreateRequest(name="DDOS", description="Categoría de DDOS")
        
        with pytest.raises(HTTPException) as exc_info:
            await create_category(body, mock_supplier_admin_user)
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_update_category_success(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de categoría exitosa."""
    pool, conn = mock_db_pool
    
    category_data = {
        "id": 1,
        "name": "DDOS Updated",
        "description": "Descripción actualizada",
        "info": "Categoría actualizada exitosamente"
    }
    
    mock_row = create_mock_record(category_data)
    
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.categories.get_pool", new_callable=AsyncMock, return_value=pool):
        body = CategoryUpdateRequest(newName="DDOS Updated", newDescription="Descripción actualizada")
        result = await update_category(1, body, mock_supplier_admin_user)
        
        assert result.status_code == 200


@pytest.mark.asyncio
async def test_delete_category_success(mock_supplier_admin_user, mock_db_pool):
    """Test de eliminación de categoría exitosa."""
    pool, conn = mock_db_pool
    
    result_data = {"message": "Categoría eliminada exitosamente", "affectedRows": 1}
    conn.fetchval = AsyncMock(return_value=json.dumps(result_data))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.categories.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await delete_category(1, mock_supplier_admin_user)
        
        assert result.status_code == 200


@pytest.mark.asyncio
async def test_delete_category_not_found(mock_supplier_admin_user, mock_db_pool):
    """Test de eliminación de categoría no encontrada."""
    pool, conn = mock_db_pool
    
    conn.fetchval = AsyncMock(return_value=None)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.categories.get_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(HTTPException) as exc_info:
            await delete_category(999, mock_supplier_admin_user)
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_categories_success(mock_supplier_admin_user, mock_db_pool):
    """Test de listado de categorías exitoso."""
    pool, conn = mock_db_pool
    
    categories_data = [
        {"id": 1, "name": "DDOS", "description": "Categoría DDOS"},
        {"id": 2, "name": "Pentesting", "description": "Categoría Pentesting"}
    ]
    
    # En el código real, fn_get_categories retorna filas donde row[0] es un JSON string
    # Necesitamos simular esto correctamente
    import json
    mock_rows = []
    for cat in categories_data:
        # Crear un mock que tenga [0] como JSON string
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: json.dumps(cat) if key == 0 else None
        mock_rows.append(mock_row)
    
    conn.fetch = AsyncMock(return_value=mock_rows)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.categories.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_categories(
            name=None,
            createdBy=None,
            status=None,
            current_user=mock_supplier_admin_user
        )
        
        assert "categories" in result
        assert len(result["categories"]) == 2


@pytest.mark.asyncio
async def test_get_categories_with_filters(mock_supplier_admin_user, mock_db_pool):
    """Test de listado de categorías con filtros."""
    pool, conn = mock_db_pool
    
    categories_data = [
        {"id": 1, "name": "DDOS", "description": "Categoría DDOS"}
    ]
    
    # En el código real, fn_get_categories retorna filas donde row[0] es un JSON string
    import json
    mock_rows = []
    for cat in categories_data:
        # Crear un mock que tenga [0] como JSON string
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: json.dumps(cat) if key == 0 else None
        mock_rows.append(mock_row)
    
    conn.fetch = AsyncMock(return_value=mock_rows)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.categories.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_categories(
            name="DDOS",
            createdBy=1,
            status="activo",
            current_user=mock_supplier_admin_user
        )
        
        assert "categories" in result
        assert len(result["categories"]) == 1

