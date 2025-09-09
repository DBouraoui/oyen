import datetime
from fastapi import APIRouter, HTTPException, Depends
from database import SessionLocal, get_db
from .schemas import UrlCreate, UrlUpdate, UrlResponse
from sqlalchemy.orm import Session
from .service import PingService
from .models import Ping

router = APIRouter()

db = SessionLocal()

@router.post("", response_model=UrlResponse)
def create_url(url: UrlCreate, db: Session = Depends(get_db)):
    service = PingService(db)

    if service.is_url_exist(url.url):
        raise HTTPException(status_code=400, detail="URL déjà existante")

    url_create = Ping(
        url=url.url,
        info=url.info,
        created_at=datetime.datetime.now()
    )

    db.add(url_create)
    db.commit()
    db.refresh(url_create)

    return url_create

@router.put("")
def update_url(url: UrlUpdate, db: Session = Depends(get_db)):
    service = PingService(db)

    url_update = service.get_url_by_id(url.id)

    if url_update is None:
        raise HTTPException(status_code=404, detail="URL not found")

    if url_update.url != url.url:
        url_update.url = url.url

    if url_update.info != url.info:
        url_update.info = url.info

    db.commit()
    db.refresh(url_update)

    return url_update


@router.delete("/{id}")
def delete_url(id: int, db: Session = Depends(get_db)):
    service = PingService(db)

    url = service.get_url_by_id(id)

    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    db.delete(url)
    db.commit()

    return True

@router.get("")
def get_urls(db: Session = Depends(get_db)):
    service = PingService(db)
    urls = service.get_all_urls()

    return urls

@router.get("/{id}")
def get_url(id: int, db: Session = Depends(get_db)):
    service = PingService(db)

    url = service.get_url_by_id(id)

    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    return url