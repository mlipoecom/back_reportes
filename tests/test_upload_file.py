"""
Tests para los endpoints de subida de archivos.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, mock_open
from fastapi import HTTPException, UploadFile
from app.routes.upload_file import upload_file
from datetime import date


@pytest.mark.asyncio
async def test_upload_file_success(mock_company_user, mock_db_pool):
    """Test de subida de archivo exitosa."""
    pool, conn = mock_db_pool
    
    from tests.conftest import create_mock_record
    file_result = {
        "info": "Archivo subido exitosamente",
        "id": 1
    }
    
    mock_row = create_mock_record(file_result)
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[mock_row])
    
    # Mock de categoría y cliente
    category_data = {"id": 1, "name": "DDOS"}
    customer_data = {"id": 1, "name": "Cliente Test"}
    
    # Mock de archivo
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.file = MagicMock()
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.upload_file.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.upload_file.get_category_by_id", new_callable=AsyncMock, return_value=category_data):
            with patch("app.routes.upload_file.get_customer_by_id", new_callable=AsyncMock, return_value=customer_data):
                with patch("app.routes.upload_file.s3") as mock_s3:
                    mock_s3.upload_fileobj = MagicMock()
                    # Mock uuid4 para retornar un UUID que al convertirlo a string y reemplazar "-" dé un valor fijo
                    mock_uuid = MagicMock()
                    mock_uuid.__str__ = MagicMock(return_value="test123456789012345678901234567890")
                    with patch("app.routes.upload_file.uuid.uuid4", return_value=mock_uuid):
                        result = await upload_file(
                            current_user=mock_company_user,
                            customer_id=1,
                            category_id=1,
                            report_date="2025-01-15",
                            file=mock_file
                        )
                        
                        assert result["id"] == 1
                        assert "exitosamente" in result["info"].lower()


@pytest.mark.asyncio
async def test_upload_file_no_file(mock_company_user, mock_db_pool):
    """Test de subida sin archivo."""
    pool, conn = mock_db_pool
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.upload_file.get_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(HTTPException) as exc_info:
            await upload_file(
                current_user=mock_company_user,
                customer_id=1,
                category_id=1,
                report_date="2025-01-15",
                file=None
            )
        
        assert exc_info.value.status_code == 400
        assert "archivo" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_upload_file_category_not_found(mock_company_user, mock_db_pool):
    """Test de subida con categoría no encontrada."""
    pool, conn = mock_db_pool
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.upload_file.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.upload_file.get_category_by_id", side_effect=HTTPException(status_code=404, detail="Categoría no encontrada")):
            with pytest.raises(HTTPException) as exc_info:
                await upload_file(
                    current_user=mock_company_user,
                    customer_id=1,
                    category_id=999,
                    report_date="2025-01-15",
                    file=mock_file
                )
            
            assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_upload_file_customer_not_found(mock_company_user, mock_db_pool):
    """Test de subida con cliente no encontrado."""
    pool, conn = mock_db_pool
    
    category_data = {"id": 1, "name": "DDOS"}
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.upload_file.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.upload_file.get_category_by_id", return_value=category_data):
            with patch("app.routes.upload_file.get_customer_by_id", side_effect=HTTPException(status_code=404, detail="Cliente no encontrado")):
                with pytest.raises(HTTPException) as exc_info:
                    await upload_file(
                        current_user=mock_company_user,
                        customer_id=999,
                        category_id=1,
                        report_date="2025-01-15",
                        file=mock_file
                    )
                
                assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_upload_file_s3_error(mock_company_user, mock_db_pool):
    """Test de subida con error en S3."""
    pool, conn = mock_db_pool
    
    category_data = {"id": 1, "name": "DDOS"}
    customer_data = {"id": 1, "name": "Cliente Test"}
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.file = MagicMock()
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.upload_file.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.upload_file.get_category_by_id", return_value=category_data):
            with patch("app.routes.upload_file.get_customer_by_id", return_value=customer_data):
                with patch("app.routes.upload_file.s3") as mock_s3:
                    mock_s3.upload_fileobj = MagicMock(side_effect=Exception("S3 Error"))
                    with pytest.raises(Exception):
                        await upload_file(
                            current_user=mock_company_user,
                            customer_id=1,
                            category_id=1,
                            report_date="2025-01-15",
                            file=mock_file
                        )

