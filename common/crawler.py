import asyncio
from random import uniform
from abc import ABC, abstractmethod


class Crawler(ABC):

  @abstractmethod
  async def run(self) -> None: ...

  @abstractmethod
  async def stop(self) -> None: ...


async def random_sleep(lower: float, upper: float):
  await asyncio.sleep(uniform(lower, upper))