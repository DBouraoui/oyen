import datetime
from typing import Sequence

import httpx
import time
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from url_scheduler.models import PingResponse
from urls.models import Url


class SchedulerService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_schedule_urls(self)-> Sequence[Url]:
            result = await self.db.execute(select(Url).filter_by(schedule=True))

            urls = result.scalars().all()

            if not urls:
                raise HTTPException(status_code=404, detail="No scheduled URLs found")

            return urls

    async def ping_urls(self):
        result = await self.db.execute(select(Url).filter_by(schedule=True))
        urls_model = result.scalars().all()

        if not urls_model:
            raise HTTPException(status_code=404, detail="No scheduled URL found")

        responses = []

        async with httpx.AsyncClient(timeout=5) as client:
            for url_model in urls_model:
                url = url_model.url
                try:
                    start = time.perf_counter()
                    resp = await client.get(str(url))
                    elapsed = time.perf_counter() - start

                    ping_result = {
                        "url": str(url),
                        "status_code": resp.status_code,
                        "reason": resp.reason_phrase,
                        "response_time_ms": round(elapsed * 1000, 2),
                        "content_length": len(resp.content),
                        "headers": {
                            k: v for k, v in resp.headers.items()
                            if k.lower() in {"content-type", "server", "date", "x-powered-by"}
                        }
                    }

                    ping_response_model = PingResponse(
                        url=str(url),
                        response=ping_result,
                        created_at=datetime.datetime.now(datetime.timezone.utc),
                    )

                    self.db.add(ping_response_model)
                    responses.append(ping_result)

                except Exception as e:
                    responses.append({
                        "url": str(url),
                        "error": str(e)
                    })

            await self.db.commit()

        return responses