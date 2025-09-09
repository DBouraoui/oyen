import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl

class Url(BaseModel):
    id: int
    url: str
    info: str
    created_at: datetime.datetime

class UrlCreate(BaseModel):
    url: HttpUrl
    info: str

class UrlUpdate(BaseModel):
    id: int
    url: Optional[str] = None
    info: Optional[str] = None

class UrlResponse(Url):
    class Config:
        orm_mode = True
