from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from url_scheduler.service import SchedulerService
from users.users import current_active_user
from database import get_async_session
from users.models import User

router = APIRouter()

scheduler = AsyncIOScheduler()

# @router.on_event("startup")
# async def startup(db: AsyncSession = Depends(get_async_session)):
#     service = SchedulerService(db)
#
#     urls = await service.get_all_schedule_urls()
#
#     if len(urls) != 0:
#         for url in urls:
#             scheduler.add_job()
#


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
    response = await service.ping_urls()
    return response