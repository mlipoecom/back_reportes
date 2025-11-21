from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from database import get_pool
import json
from utils import get_company_id_from_token, get_user_id_from_token

router = APIRouter(
    prefix="/api",
    tags=["Api"]
)


