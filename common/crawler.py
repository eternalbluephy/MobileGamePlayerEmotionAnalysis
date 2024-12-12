import asyncio
from random import uniform
from enum import Enum
from typing import Any

class Err(Enum):
  IP_BANNED = 1,
  FAILED = 2,
  SERVER_ERROR = 3,
  EOF = 4,
  NOT_EXISTS = 5,

# golang like
CrawlResult = tuple[bool, Any]


class CrawlerRunner:...
  

async def random_sleep(lower: float, upper: float):
  await asyncio.sleep(uniform(lower, upper))