"""
Tests para los endpoints de archivos.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.files import get_archivos, download_file_by_id
from datetime import date


@pytest.mark.asyncio
async def test_get_archivos_success(mock_company_user, mock_db_pool):
    """Test de listado de archivos exitoso."""
    pool, conn = mock_db_pool
    
    files_data = {
        "companyId": 1,
        "supplier": "Ecom",
        "totalCount": 2,
        "files": [
            {"id": 1, "nombre": "archivo1", "categoria": "DDOS"},
            {"id": 2, "nombre": "archivo2", "categoria": "Pentesting"}
        ]
    }
    
    conn.fetchval = AsyncMock(return_value=json.dumps(files_data))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.files.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_archivos(
            current_user=mock_company_user,
            nombre=None,
            categoria=None,
            fecha_desde_str=None,
            fecha_hasta_str=None,
            limit=10,
            offset=0
        )
        
        assert result["totalCount"] == 2
        assert len(result["files"]) == 2


@pytest.mark.asyncio
async def test_get_archivos_with_filters(mock_company_user, mock_db_pool):
    """Test de listado de archivos con filtros."""
    pool, conn = mock_db_pool
    
    files_data = {
        "companyId": 1,
        "supplier": "Ecom",
        "totalCount": 1,
        "files": [
            {"id": 1, "nombre": "archivo1", "categoria": "DDOS"}
        ]
    }
    
    conn.fetchval = AsyncMock(return_value=json.dumps(files_data))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.files.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_archivos(
            current_user=mock_company_user,
            nombre="archivo1",
            categoria="DDOS",
            fecha_desde_str="2025-01-01",
            fecha_hasta_str="2025-12-31",
            limit=10,
            offset=0
        )
        
        assert result["totalCount"] == 1
        assert len(result["files"]) == 1


@pytest.mark.asyncio
async def test_get_archivos_invalid_date(mock_company_user, mock_db_pool):
    """Test de listado de archivos con fecha inválida."""
    pool, conn = mock_db_pool
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.files.get_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(HTTPException) as exc_info:
            await get_archivos(
                current_user=mock_company_user,
                nombre=None,
                categoria=None,
                fecha_desde_str="invalid-date",
                fecha_hasta_str=None,
                limit=10,
                offset=0
            )
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_archivos_no_data(mock_company_user, mock_db_pool):
    """Test de listado de archivos sin datos."""
    pool, conn = mock_db_pool
    
    conn.fetchval = AsyncMock(return_value=None)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.files.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_archivos(
            current_user=mock_company_user,
            nombre=None,
            categoria=None,
            fecha_desde_str=None,
            fecha_hasta_str=None,
            limit=10,
            offset=0
        )
        
        assert result["totalCount"] == 0
        assert result["files"] == []


@pytest.mark.asyncio
async def test_download_file_by_id_success(mock_company_user, mock_db_pool):
    """Test de descarga de archivo exitosa."""
    pool, conn = mock_db_pool
    
    file_data = {
        "fn_get_file_path": "s3://portal-informes-dev/test/file.pdf"
    }
    
    mock_row = MagicMock()
    for key, value in file_data.items():
        setattr(mock_row, key, value)
    
    conn.fetch = AsyncMock(return_value=[mock_row])
    conn.execute = AsyncMock()
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.files.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.files.get_file_by_id", return_value=file_data):
            with patch("app.routes.files.log_file_download", return_value=None):
                with patch("app.routes.files.generate_presigned_url", return_value="https://presigned-url.com"):
                    result = await download_file_by_id(1, mock_company_user)
                    
                    assert result == "https://presigned-url.com"


@pytest.mark.asyncio
async def test_download_file_by_id_not_found(mock_company_user, mock_db_pool):
    """Test de descarga de archivo no encontrado."""
    pool, conn = mock_db_pool
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.files.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.files.get_file_by_id", side_effect=HTTPException(status_code=404, detail="Archivo no encontrado")):
            with pytest.raises(HTTPException) as exc_info:
                await download_file_by_id(999, mock_company_user)
            
            assert exc_info.value.status_code == 404

