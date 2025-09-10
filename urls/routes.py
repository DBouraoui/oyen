from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from users.users import current_active_user
from .service import PingService
from .schemas import UrlCreate, UrlUpdate, UrlResponse
from database import get_async_session
from users.models import User

router = APIRouter()

@router.post("", response_model=UrlResponse)
async def create_url(url: UrlCreate, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    """
    Create a new url
    :param user
    :param url:
    :param db:
    :return:
    """
    service = PingService(db)

    if await service.is_url_exist(url.url):
        raise HTTPException(status_code=400, detail="URL déjà existante")

    url_create = await service.create_url(url.url, url.info)
    return url_create

@router.put("")
async def update_url(url: UrlUpdate,user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    """
    Update an existing url
    :param url:
    :param user:
    :param db:
    :return:
    """
    service = PingService(db)
    url_update = await service.get_url_by_id(url.id)

    if url_update is None:
        raise HTTPException(status_code=404, detail="URL not found")

    if url.url is not None:
        url_update.url = url.url
    if url.info is not None:
        url_update.info = url.info

    await db.commit()
    await db.refresh(url_update)
    return url_update

@router.patch("/{id}")
async def switch_schedule_ping_url(id: int,user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    """
    Active and desactive scheduling for ping url
    :param id:
    :param user:
    :param db:
    :return:
    """
    service = PingService(db)

    url = await service.get_url_by_id(id)

    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    url.schedule = not url.schedule
    await db.commit()
    await db.refresh(url)

    return url

@router.delete("/{id}")
async def delete_url(id: int, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    """
    Delete an existing url
    :param id:
    :param user:
    :param db:
    :return:
    """
    service = PingService(db)
    url = await service.get_url_by_id(id)

    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    await db.delete(url)
    await db.commit()
    return {"deleted": True}

@router.get("", response_model=list[UrlResponse])
async def get_urls(db: AsyncSession = Depends(get_async_session),user: User = Depends(current_active_user)):
    """
    Get all urls
    :param db:
    :param user:
    :return:
    """
    service = PingService(db)
    urls = await service.get_all_urls()
    return urls

@router.get("/{id}", response_model=UrlResponse)
async def get_url(id: int, db: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    """
    Get an existing url
    :param id:
    :param user
    :param db:
    :return:
    """
    service = PingService(db)
    url = await service.get_url_by_id(id)

    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    return url
