from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .models import ServerReporting

from database import get_async_session
from .data_enhancement import enhancement_data_stats, enhancement_server_stats

router = APIRouter()
scheduler = AsyncIOScheduler()


@router.get("/pings")
async def report_pings_data(db: AsyncSession = Depends(get_async_session)):
    result =  await enhancement_data_stats(db)
    return {"report": result}

@router.get("/servers")
async def report_servers_data(db: AsyncSession = Depends(get_async_session)):
    result = await enhancement_server_stats(db)

    return {"report": result}