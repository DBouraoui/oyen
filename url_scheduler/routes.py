import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from url_scheduler.service import SchedulerService
from users.users import current_active_user
from database import get_async_session
from users.models import User
from database import async_session_maker


router = APIRouter()
scheduler = AsyncIOScheduler()
load_dotenv()

async def scheduled_ping():
    async with async_session_maker() as db:
        service = SchedulerService(db)
        await service.ping_urls()


@router.on_event("startup")
async def on_startup():
    interval = int(os.getenv("PING_INTERVAL_SCHEDULER",60))
    scheduler.add_job(scheduled_ping, 'interval', seconds=interval, id="scheduled_ping")
    scheduler.start()

@router.get("")
async def get_pings(db: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    """
    Get all urls to schedule
    """
    service = SchedulerService(db)

    urls = await service.get_all_schedule_urls()

    return urls


@router.get("/ping")
async def ping_url(db: AsyncSession = Depends(get_async_session)):
    service = SchedulerService(db)
    responses = await service.ping_urls()
    return {"results": responses}