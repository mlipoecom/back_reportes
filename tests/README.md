# Tests para Portal de Reportes

Este directorio contiene los tests unitarios para todos los endpoints de la API.

## Estructura

```
tests/
├── conftest.py              # Fixtures comunes para todos los tests
├── test_auth.py             # Tests de autenticación
├── test_categories.py        # Tests de categorías
├── test_change_password.py   # Tests de cambio de contraseña
├── test_companies.py         # Tests de empresas
├── test_contact.py           # Tests de contacto
├── test_customers.py         # Tests de clientes
├── test_ecom.py              # Tests de ECOM
├── test_files.py             # Tests de archivos
├── test_logs.py              # Tests de logs
├── test_suppliers.py         # Tests de proveedores
├── test_update_status.py     # Tests de actualización de estado
├── test_upload_file.py       # Tests de subida de archivos
└── test_users.py             # Tests de usuarios
```

## Instalación

1. Instala las dependencias de tests:

```bash
pip install -r tests/requirements.txt
```

O si usas el entorno virtual del proyecto:

```bash
pip install pytest pytest-asyncio httpx
```

## Ejecución

**Importante**: Asegúrate de estar en la raíz del proyecto (`back_reportes`) cuando ejecutes los tests.

### Ejecutar todos los tests

```bash
pytest tests/
```

O usando el módulo de Python:

```bash
python -m pytest tests/
```

### Ejecutar un archivo de tests específico

```bash
pytest tests/test_auth.py
```

### Ejecutar un test específico

```bash
pytest tests/test_auth.py::test_login_success_super_admin
```

### Ejecutar con cobertura

```bash
pytest tests/ --cov=app --cov-report=html
```

### Ejecutar con salida detallada

```bash
pytest tests/ -v
```

### Ejecutar mostrando prints

```bash
pytest tests/ -s
```

### Verificar que los tests se pueden recopilar (sin ejecutarlos)

```bash
pytest tests/ --collect-only
```

## Características de los Tests

### Fixtures Comunes

El archivo `conftest.py` proporciona fixtures reutilizables:

- `client`: Cliente de prueba para FastAPI
- `mock_db_pool`: Mock del pool de conexiones a la base de datos
- `mock_super_admin_user`: Usuario mock con rol SUPER_ADMIN
- `mock_supplier_admin_user`: Usuario mock con rol SUPPLIER_ADMIN
- `mock_company_admin_user`: Usuario mock con rol COMPANY_ADMIN
- `mock_company_user`: Usuario mock con rol COMPANY_USER
- `mock_access_token`: Token JWT mock
- `mock_authorization_header`: Header de autorización mock
- Varios mocks de datos (usuarios, categorías, empresas, etc.)

### Cobertura de Tests

Los tests cubren:

1. **Casos exitosos**: Operaciones que se completan correctamente
2. **Casos de error**: Validaciones, errores de BD, permisos, etc.
3. **Casos límite**: Datos vacíos, valores nulos, etc.
4. **Validaciones de seguridad**: Tokens inválidos, roles incorrectos, etc.

### Endpoints Cubiertos

- ✅ Autenticación (login, MFA, nuevos dispositivos)
- ✅ Categorías (crear, actualizar, eliminar, listar)
- ✅ Cambio de contraseña
- ✅ Empresas (asignar cliente, listar clientes/usuarios)
- ✅ Contacto
- ✅ Clientes (actualizar, eliminar)
- ✅ ECOM (crear/listar/eliminar proveedores)
- ✅ Archivos (listar, descargar)
- ✅ Logs
- ✅ Proveedores (crear empresas/clientes, listar, editar, eliminar)
- ✅ Actualización de estado
- ✅ Subida de archivos
- ✅ Usuarios (crear, editar, eliminar, asignar roles/clientes)

## Notas

- Los tests utilizan mocks para la base de datos y servicios externos (S3, SMTP)
- No se requiere una base de datos real para ejecutar los tests
- Los tests son asíncronos y utilizan `pytest-asyncio`
- Se recomienda ejecutar los tests antes de cada commit

## Troubleshooting

### Error: "No module named 'app'"

Asegúrate de estar ejecutando los tests desde el directorio raíz del proyecto:

```bash
cd /ruta/al/proyecto/back_reportes
pytest tests/
```

### Error: "RuntimeError: Event loop is closed"

Asegúrate de tener `pytest-asyncio` instalado y configurado correctamente.

### Tests fallan por imports

Verifica que todas las dependencias estén instaladas:

```bash
pip install -r app/requirements.txt
pip install -r tests/requirements.txt
```

