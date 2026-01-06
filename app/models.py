from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class UserGenerate(BaseModel):
    name: str = Field(..., max_length=50, example="John", description="Nombre del usuario")
    lastName: str = Field(..., max_length=50, example="Doe", description="Apellido del usuario")
    email: EmailStr = Field(..., example="john.doe@ecom.com.uy", description="Email del usuario")
    externalId: str = Field(..., max_length=50, example="johnDoe123", description="Identificador externo del usuario")
    supplierId: Optional[int] = Field(None, example=1, description="ID del proveedor al que pertenece el usuario")
    companyId: Optional[int] = Field(None, example=1, description="ID de la compañía a la que pertenece el usuario")
    customerId: Optional[int] = Field(None, example=1, description="ID del cliente al que pertenece el usuario")
    status: str = Field('activo', description="Estado inicial del usuario ('activo', 'suspendido', 'inactivo')")
    role: Optional[str] = Field(None, example="supplier_admin", description="Nombre del rol a asignar al usuario")

class CompanyGenerate(BaseModel):
    name: str = Field(..., max_length=50, example="Acme", description="Nombre fantasía de la empresa")
    businessName: str = Field(..., max_length=50, example="Acme SA", description="Razón social de la empresa")
    externalId: str = Field(..., max_length=50, example="1234567890212", description="Identificador externo de la empresa")
    description: str = Field(..., max_length=256, example="Consultance services", description="Descripción de la empresa")
    status: str = Field('activo', description="Estado inicial de la empresa ('activo', 'suspendido', 'inactivo')")
    email: EmailStr = Field(..., example="info@acme.com", description="Email de la empresa")

class CustomerGenerate(BaseModel):
    name: str = Field(..., max_length=50, example="Acme", description="Nombre fantasía de la empresa")
    businessName: str = Field(..., max_length=50, example="Acme SA", description="Razón social de la empresa")
    externalId: str = Field(..., max_length=50, example="1234567890212", description="Identificador externo de la empresa")
    description: str = Field(..., max_length=256, example="Consultance services", description="Descripción de la empresa")
    status: str = Field('activo', description="Identificador de empresa ('activo', 'suspendido', 'inactivo')")
    companyId: int = Field(...,  description="Identificador de la empresa", example=1)
    email: EmailStr = Field(..., example="info@acme.com", description="Email de la empresa")

class CompanyGenerateResponse(BaseModel):
    info: str = Field(example="Compañía creada exitosamente.")
    id: int = Field(example=1)

class CustomerGenerateResponse(BaseModel):
    info: str = Field(example="Cliente creado exitosamente.")
    id: int = Field(example=1)

class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(..., max_length=50, example="Nuevo Nombre", description="Nombre fantasía del cliente")
    businessName: Optional[str] = Field(..., max_length=50, example="Nueva Razón Social", description="Razón social del cliente")
    email: Optional[EmailStr] = Field(..., example="nuevo@email.com", description="Email del cliente")
    description: Optional[str] = Field(..., max_length=256, example="Nueva descripción", description="Descripción del cliente")

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(..., max_length=50, example="Acme", description="Nombre fantasía de la empresa")
    businessName: Optional[str] = Field(..., max_length=50, example="Acme SA", description="Razón social de la empresa")
    externalId: Optional[str] = Field(..., max_length=50, example="1234567890212", description="Identificador externo de la empresa")
    description: Optional[str] = Field(..., max_length=256, example="Consultance services", description="Descripción de la empresa")
    email: EmailStr = Field(..., example="info@acme.com", description="Email de la empresa")

class UserUpdate(BaseModel):
    name: str = Field(..., max_length=50, example="John", description="Nombre del usuario")
    lastName: str = Field(..., max_length=50, example="Doe", description="Apellido del usuario")
    email: EmailStr = Field(..., example="john.doe@ecom.com.uy", description="Email del usuario")
    externalId: str = Field(..., max_length=50, example="johnDoe123", description="Identificador externo del usuario")
    status: str = Field('activo', description="Estado inicial del usuario ('activo', 'suspendido', 'inactivo')")
    role: Optional[str] = Field(None, example="supplier_admin", description="Nombre del rol a asignar al usuario")

class SupplierGenerate(BaseModel):
    name: str = Field(..., max_length=50, example="Ecom", description="Nombre fantasía del proveedor")
    businessName: str = Field(..., max_length=50, example="Ecom Center SRL", description="Razón social del proveedor")
    externalId: str = Field(..., max_length=50, example="987654321223", description="Identificador externo del proveedor")
    description: str = Field(..., max_length=256, example="Software Factory", description="Descripción del proveedor")
    status: str = Field('activo', description="Estado inicial del proveedor ('activo', 'suspendido', 'inactivo')")
    email: EmailStr = Field(..., example="info@ecom.com.uy", description="Email del proveedor")

class SupplierGenerateResponse(BaseModel):
    info: str
    id: int

class UserGenerateResponse(BaseModel):
    info: str
    id: int

class UpdateStatusResponse(BaseModel):
    ejecutado: bool
    info: str

class LoginRequest(BaseModel):
    usuario: str = Field(..., example="johnDoe123")
    contraseña: str = Field(..., example="5YGEuL#8&X")

class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str

class MessageResponse(BaseModel):
    message: str
    status: str

class AssignRolesRequest(BaseModel):
    user_id: int = Field(..., example=1, description="ID del usuario")
    role_id: int = Field(..., example=1, description="ID del rol")

class AssignClientRequest(BaseModel):
    userId: int = Field(..., example=1, description="ID del usuario")
    customerId: int = Field(..., example=1, description="ID del cliente")
    categoryIds: List[int] = Field(..., example=[1, 2, 3], description="IDs de las categorías")

class CategoryCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryUpdateRequest(BaseModel):
    newName: Optional[str] = None
    newDescription: Optional[str] = None

class MfaRequiredResponse(BaseModel):
    requiresMfa: bool
    mfaStatus: str
    mfaToken: str
    mfaSecret: Optional[str] = None

class MfaVerifyRequest(BaseModel):
   code: str
   mfaToken: str = Field(...)

