from redis import asyncio as aioredis

class Redis:

  def __init__(self,
               host: str = "localhost",
               port: int = 6379,
               db: str | int = 0,
               password: str | None = None):
    self.client = aioredis.Redis(
      host=host, port=port, db=db, password=password
    )
    self._db = db
    