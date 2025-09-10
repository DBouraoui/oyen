import datetime
import os
import psutil

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from reporting.models import ServerReporting
from url_scheduler.models import PingResponse
from sqlalchemy.future import select

load_dotenv()

async def enhancement_data_stats(database: AsyncSession):

    hours = int(os.environ.get("REPORTING_PINGS_TIMELAPS",12))
    now = datetime.datetime.now(datetime.timezone.utc)
    since = now - datetime.timedelta(hours=hours)

    result = await database.execute(select(PingResponse).filter(PingResponse.created_at >= since))
    pings_model = result.scalars().all()

    if not pings_model:
        return {"message": "No data"}

    times = [ping.response.get("response_time_ms", 0) for ping in pings_model]
    codes = [ping.response.get("status_code", 0) for ping in pings_model]

    return {
        "total_pings": len(pings_model),
        "avg_response_time_ms": round(sum(times) / len(times), 2),
        "min_response_time_ms": min(times),
        "max_response_time_ms": max(times),
        "status_codes_distribution": {code: codes.count(code) for code in set(codes)},
    }

async def enhancement_server_stats(database: AsyncSession):

        cpu_percent = psutil.cpu_percent(interval=1)

        ram = psutil.virtual_memory()
        ram_total = round(ram.total / (1024 ** 3), 2)  # en Go
        ram_used = round(ram.used / (1024 ** 3), 2)
        ram_percent = ram.percent

        disk = psutil.disk_usage('/')
        disk_total = round(disk.total / (1024 ** 3), 2)
        disk_used = round(disk.used / (1024 ** 3), 2)
        disk_percent = disk.percent

        net = psutil.net_io_counters()
        bytes_sent = round(net.bytes_sent / (1024 ** 2), 2)  # en Mo
        bytes_recv = round(net.bytes_recv / (1024 ** 2), 2)

        result = {
            "cpu_percent": cpu_percent,
            "ram": {
                "total_gb": ram_total,
                "used_gb": ram_used,
                "percent": ram_percent,
            },
            "disk": {
                "total_gb": disk_total,
                "used_gb": disk_used,
                "percent": disk_percent,
            },
            "network": {
                "sent_mb": bytes_sent,
                "recv_mb": bytes_recv,
            }
        }

        server_reporting_model = ServerReporting(
            response=result
        )

        database.add(server_reporting_model)
        await database.commit()
        await database.refresh(server_reporting_model)

        return result

