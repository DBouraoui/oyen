from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .models import ServerReporting, JsonReporting
import os

from database import get_async_session, async_session_maker
from .data_enhancement import enhancement_data_stats_average, enhancement_server_stats, \
    enhancement_reporting_server_average, gpt_reporting_average, oyen_reporting_average

router = APIRouter()
scheduler = AsyncIOScheduler()
load_dotenv()

async def scheduled_ping_server_stats():
    async with async_session_maker() as db:
        await enhancement_server_stats(db)

@router.on_event("startup")
async def on_startup():
    interval = int(os.getenv("REPORTING_SERVER_TIMELAPS",60))
    scheduler.add_job(scheduled_ping_server_stats, 'interval', seconds=interval, id="scheduled_ping_server_stats")
    scheduler.start()

# Reporting pings in timelaps
@router.get("/pings-average")
async def report_pings_data(db: AsyncSession = Depends(get_async_session)):
    result =  await enhancement_data_stats_average(db)
    return {"report": result}

@router.get("/server-average")
async def report_server_middle(db: AsyncSession = Depends(get_async_session)):
    result = await enhancement_reporting_server_average(db)
    return {"report": result}

#Reporting server stats instant
@router.get("/servers")
async def report_servers_data(db: AsyncSession = Depends(get_async_session)):
    result = await enhancement_server_stats(db)

    return {"report": result}


@router.get("/oyen")
async def report_oyen(db: AsyncSession = Depends(get_async_session)):
    result = await oyen_reporting_average(db)
    return result

@router.get("/gpt")
async def report_gpt(db: AsyncSession = Depends(get_async_session)):
    result = await gpt_reporting_average(db)

    return result
