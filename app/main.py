from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import get_pool, close_pool
from routes import ecom, categories, companies, files, suppliers, users, auth, update_status, change_password, contact, logs, upload_file, customers
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
app.include_router(ecom.router)
app.include_router(categories.router)
app.include_router(users.router)
app.include_router(companies.router)
app.include_router(suppliers.router)
app.include_router(update_status.router)
app.include_router(files.router)
app.include_router(auth.router)
app.include_router(change_password.router)
app.include_router(contact.router)
app.include_router(logs.router)
app.include_router(upload_file.router)
app.include_router(customers.router)

