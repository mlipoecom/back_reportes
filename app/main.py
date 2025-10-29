from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import get_pool, close_pool
from routes import empresas, users, archivos, auth, proveedor, update_status, change_password, contact, logs

@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    yield
    await close_pool()

app = FastAPI(
    title="Portal de gestión",
    description="Manejo de archivos",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(users.router)
app.include_router(empresas.router)
app.include_router(proveedor.router)
app.include_router(update_status.router)
app.include_router(archivos.router)
app.include_router(auth.router)
app.include_router(change_password.router)
app.include_router(contact.router)
app.include_router(logs.router)

