from abc import ABC, abstractmethod
from typing import Optional


class API(ABC):

  @staticmethod
  @abstractmethod
  def call(*args, **kwargs) -> str: ...

  @staticmethod
  @abstractmethod
  def test(self, proxy: Optional[str]) -> bool: ...


class AsyncAPI(ABC):

  @staticmethod
  @abstractmethod
  async def call(*args, **kwargs) -> str: ...

  @staticmethod
  @abstractmethod
  async def test(headers: Optional[dict] = None, proxies: Optional[dict] = None) -> bool: ...