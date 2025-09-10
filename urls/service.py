from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import Url

class PingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_url_exist(self, url: HttpUrl) -> bool:
        url_str = str(url)
        result = await self.db.execute(select(Url).filter_by(url=url_str))
        return result.scalars().first() is not None

    async def create_url(self, url: HttpUrl, info: str) -> Url:
        url_str = str(url)
        ping = Url(url=url_str, info=info)
        self.db.add(ping)
        await self.db.commit()
        await self.db.refresh(ping)
        return ping

    async def get_url_by_id(self, url_id: int):
        result = await self.db.execute(select(Url).filter_by(id=url_id))
        return result.scalars().first()

    async def get_all_urls(self):
        result = await self.db.execute(select(Url))
        return result.scalars().all()
