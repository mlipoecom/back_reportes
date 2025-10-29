from pydantic import BaseModel, Field, EmailStr

class UserGenerate(BaseModel):
    name: str = Field(..., max_length=50, example="John", description="Nombre del usuario")
    lastName: str = Field(..., max_length=50, example="Doe", description="Apellido del usuario")
    email: EmailStr = Field(..., max_length=50, example="john.doe@ecom.com.uy", description="Email del usuario")
    externalId: str = Field(..., max_length=50, example="johnDoe123", description="Identificador externo del usuario")
    companyId: int = Field(..., example=1, description="ID de la compañía a la que pertenece el usuario")
    status: str = Field('activo', description="Estado inicial del usuario ('activo', 'suspendido', 'inactivo')")

class CompanyGenerate(BaseModel):
    name: str = Field(..., max_length=50, example="Acme", description="Nombre fantasía de la empresa")
    businessName: str = Field(..., max_length=50, example="Acme SA", description="Razón social de la empresa")
    externalId: str = Field(..., max_length=50, example="1234567890212", description="Identificador externo de la empresa")
    description: str = Field(..., max_length=256, example="Consultance services", description="Descripción de la empresa")
    status: str = Field('activo', description="Estado inicial de la empresa ('activo', 'suspendido', 'inactivo')")
    supplierId: int = Field(..., example=1, description="ID del proveedor")
    email: EmailStr = Field(..., max_length=50, example="info@acme.com", description="Email de la empresa")

class CompanyGenerateResponse(BaseModel):
    info: str = Field(example="Compañía creada exitosamente.")
    id: int = Field(example=1)

class SupplierGenerate(BaseModel):
    name: str = Field(..., max_length=50, example="Ecom", description="Nombre fantasía del proveedor")
    businessName: str = Field(..., max_length=50, example="Ecom Center SRL", description="Razón social del proveedor")
    externalId: str = Field(..., max_length=50, example="987654321223", description="Identificador externo del proveedor")
    description: str = Field(..., max_length=256, example="Software Factory", description="Descripción del proveedor")
    status: str = Field('activo', description="Estado inicial del proveedor ('activo', 'suspendido', 'inactivo')")
    email: EmailStr = Field(..., max_length=50, example="info@ecom.com.uy", description="Email del proveedor")

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

