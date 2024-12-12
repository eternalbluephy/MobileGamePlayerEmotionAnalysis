from motor import motor_asyncio
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Optional, Sequence
from pymongo import UpdateOne

class MongoDB:
  
  def __init__(self, host: str = "localhost", port: int = 27017, username: Optional[str] = None, password: Optional[str] = None) -> None:
    if username is None and password is None:
      self.client = motor_asyncio.AsyncIOMotorClient(host=host, port=port)
    else:
      self.client = motor_asyncio.AsyncIOMotorClient(f"mongodb://{username}:{password}@{host}:{port}")

  @staticmethod
  async def upsert_many(collection: AsyncIOMotorCollection, documents: list[dict], session = None) -> None:
    upserts = MongoDB.make_upserts(documents)
    return await collection.bulk_write(upserts, session=session)

  @staticmethod
  def make_upserts(documents: list[dict]) -> list[UpdateOne]:
    return [UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True) for doc in documents]


if __name__ == "__main__":
  import asyncio

  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  MongoDB()
  loop.run_until_complete(MongoDB.insert("test", "test", {"aid": 2}))
  loop.run_until_complete(MongoDB.insert("test", "test", [
    {"aid": 1}, {"aid": 3}
  ]))