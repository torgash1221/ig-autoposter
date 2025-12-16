import asyncio
import logging
import os
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)


def parse_cron(expr: str) -> CronTrigger:
    parts = expr.strip().split()

    if len(parts) == 4:
        minute = "0"
        hour, day, month, dow = parts
    elif len(parts) == 5:
        minute, hour, day, month, dow = parts
    else:
        raise ValueError(f"Bad cron: {expr}")

    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=dow,
    )


async def test_job():
    logger.info("TEST JOB OK")


async def main():
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")

    for c in cfg["brands"][0]["schedule_stories"]:
        scheduler.add_job(test_job, parse_cron(c))

    scheduler.start()
    logger.info("Scheduler started")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
