"""
Fixtures comunes para todos los tests.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.roles import UserRole
import json


@pytest.fixture
def client():
    """Cliente de prueba para FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_db_pool():
    """Mock del pool de conexiones a la base de datos."""
    # Crear una conexión mock que se reutilizará
    conn = MagicMock()
    
    # Crear funciones async simples que retornen inmediatamente
    # Estas pueden ser sobrescritas por los tests
    async def async_fetch(*args, **kwargs):
        return []
    
    async def async_fetchval(*args, **kwargs):
        return None
    
    async def async_fetchrow(*args, **kwargs):
        return None
    
    async def async_execute(*args, **kwargs):
        return None
    
    # Configurar métodos por defecto como funciones async simples
    conn.fetch = async_fetch
    conn.fetchval = async_fetchval
    conn.fetchrow = async_fetchrow
    conn.execute = async_execute
    
    # Crear un mock para conn.transaction() que también es un async context manager
    transaction_manager = MagicMock()
    transaction_manager.__aenter__ = AsyncMock(return_value=None)
    transaction_manager.__aexit__ = AsyncMock(return_value=None)
    conn.transaction = MagicMock(return_value=transaction_manager)
    
    # Crear el pool mock
    pool = MagicMock()
    
    # Crear un único async context manager que retorne siempre la misma conexión
    # Esto es crítico: debe ser el mismo objeto cada vez para que los tests puedan
    # configurar conn.fetch, conn.fetchval, etc. y que funcione
    async_context_manager = MagicMock()
    async_context_manager.__aenter__ = AsyncMock(return_value=conn)
    async_context_manager.__aexit__ = AsyncMock(return_value=None)
    
    # Configurar pool.acquire() para retornar siempre el mismo async context manager
    # NO usar side_effect aquí, usar return_value directamente
    pool.acquire = MagicMock(return_value=async_context_manager)
    
    return pool, conn


@pytest.fixture
def mock_super_admin_user():
    """Usuario mock con rol SUPER_ADMIN."""
    return {
        "ID": 1,
        "role": UserRole.SUPER_ADMIN,
        "supplierId": 1,
        "companyId": None,
        "customerId": None,
        "name": "Super",
        "lastName": "Admin",
        "email": "super@admin.com",
        "externalId": "super_admin",
        "status": "activo",
        "entityStatus": "activo"
    }


@pytest.fixture
def mock_supplier_admin_user():
    """Usuario mock con rol SUPPLIER_ADMIN."""
    return {
        "ID": 2,
        "role": UserRole.SUPPLIER_ADMIN,
        "supplierId": 1,
        "companyId": None,
        "customerId": None,
        "name": "Supplier",
        "lastName": "Admin",
        "email": "supplier@admin.com",
        "externalId": "supplier_admin",
        "status": "activo",
        "entityStatus": "activo"
    }


@pytest.fixture
def mock_company_admin_user():
    """Usuario mock con rol COMPANY_ADMIN."""
    return {
        "ID": 3,
        "role": UserRole.COMPANY_ADMIN,
        "supplierId": None,
        "companyId": 1,
        "customerId": None,
        "name": "Company",
        "lastName": "Admin",
        "email": "company@admin.com",
        "externalId": "company_admin",
        "status": "activo",
        "entityStatus": "activo"
    }


@pytest.fixture
def mock_company_user():
    """Usuario mock con rol COMPANY_USER."""
    return {
        "ID": 4,
        "role": UserRole.COMPANY_USER,
        "supplierId": None,
        "companyId": 1,
        "customerId": 1,
        "name": "Company",
        "lastName": "User",
        "email": "company@user.com",
        "externalId": "company_user",
        "status": "activo",
        "entityStatus": "activo"
    }


@pytest.fixture
def mock_access_token():
    """Token JWT mock."""
    return "mock_access_token_12345"


@pytest.fixture
def mock_refresh_token():
    """Refresh token JWT mock."""
    return "mock_refresh_token_12345"


@pytest.fixture
def mock_authorization_header(mock_access_token):
    """Header de autorización mock."""
    return {"Authorization": f"Bearer {mock_access_token}"}


@pytest.fixture
def mock_user_data():
    """Datos de usuario mock para la base de datos."""
    return {
        "ID": 1,
        "name": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "externalId": "johnDoe123",
        "status": "activo",
        "role": UserRole.SUPPLIER_ADMIN,
        "supplierId": 1,
        "companyId": None,
        "customerId": None,
        "hashPassword": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBWVHxkd0",
        "entityStatus": "activo"
    }


@pytest.fixture
def mock_category_data():
    """Datos de categoría mock."""
    return {
        "id": 1,
        "name": "DDOS",
        "description": "Categoría de DDOS",
        "supplierId": 1,
        "status": "activo",
        "createdBy": 1
    }


@pytest.fixture
def mock_company_data():
    """Datos de empresa mock."""
    return {
        "id": 1,
        "name": "Acme Corp",
        "businessName": "Acme Corporation SA",
        "externalId": "acme123",
        "description": "Empresa de ejemplo",
        "status": "activo",
        "supplierId": 1,
        "email": "info@acme.com"
    }


@pytest.fixture
def mock_customer_data():
    """Datos de cliente mock."""
    return {
        "id": 1,
        "name": "Cliente Test",
        "businessName": "Cliente Test SA",
        "externalId": "cliente123",
        "description": "Cliente de ejemplo",
        "status": "activo",
        "companyId": 1,
        "email": "cliente@test.com"
    }


@pytest.fixture
def mock_supplier_data():
    """Datos de proveedor mock."""
    return {
        "id": 1,
        "name": "Ecom",
        "businessName": "Ecom Center SRL",
        "externalId": "ecom123",
        "description": "Proveedor de ejemplo",
        "status": "activo",
        "email": "info@ecom.com.uy"
    }


@pytest.fixture
def mock_file_data():
    """Datos de archivo mock."""
    return {
        "id": 1,
        "nombre": "test_file",
        "categoria": "DDOS",
        "fechaReporte": "2025-01-15",
        "path": "s3://portal-informes-dev/test/file.pdf"
    }


@pytest.fixture
def mock_mfa_data():
    """Datos de MFA mock."""
    return {
        "userId": 1,
        "mfaSecret": "JBSWY3DPEHPK3PXP",
        "isEnabled": False,
        "recoveryCodes": []
    }


@pytest.fixture
def mock_log_data():
    """Datos de log mock."""
    return {
        "hora": "12:00:00",
        "fecha": "2025-01-15",
        "usuario": 1
    }


def create_mock_db_response(data, as_json=True):
    """Helper para crear respuestas mock de la base de datos."""
    if as_json:
        return json.dumps(data) if isinstance(data, dict) else data
    return data


def create_mock_cursor_response(data_list):
    """Helper para crear respuestas de cursor mock."""
    return [MagicMock(**{k: v for k, v in data.items()}) for data in data_list]


def create_mock_record(data):
    """
    Helper para crear un mock de asyncpg.Record.
    asyncpg.Record se comporta como un dict pero también tiene atributos.
    """
    class MockRecord:
        def __init__(self, data):
            self._data = data
            for key, value in data.items():
                setattr(self, key, value)
        
        def keys(self):
            return self._data.keys()
        
        def __getitem__(self, key):
            return self._data[key]
        
        def get(self, key, default=None):
            return self._data.get(key, default)
    
    return MockRecord(data)

