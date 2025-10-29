import asyncpg
from config import DB_CONFIG

db_pool = None

async def get_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(**DB_CONFIG)
    return db_pool

async def close_pool():
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None
