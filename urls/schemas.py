import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl

class Url(BaseModel):
    id: int
    url: str
    info: str
    schedule: bool
    created_at: datetime.datetime

class UrlCreate(BaseModel):
    url: HttpUrl
    info: str

class UrlUpdateSchedule(BaseModel):
    id: int
    schedule: bool

class UrlUpdate(BaseModel):
    id: int
    url: Optional[str] = None
    info: Optional[str] = None

class UrlResponse(Url):
    class Config:
        orm_mode = True
