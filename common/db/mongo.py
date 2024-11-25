from motor import motor_asyncio
from typing import Optional, Sequence


class MongoDB:

  client: Optional["MongoDB"] = None
  
  def __init__(self, host: str = "localhost", port: int = 27017, username: Optional[str] = None, password: Optional[str] = None) -> None:
    if username is None and password is None:
      MongoDB.client = motor_asyncio.AsyncIOMotorClient(host=host, port=port)
    else:
      MongoDB.client = motor_asyncio.AsyncIOMotorClient(f"mongodb://{username}:{password}@{host}:{port}")
  
  @staticmethod
  async def insert(database: str, collection: str, document: dict | Sequence[dict]):
    collection = MongoDB.client[database][collection]
    if isinstance(document, dict):
      return await collection.insert_one(document)
    else:
      return await collection.insert_many(document)


if __name__ == "__main__":
  import asyncio

  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  MongoDB()
  loop.run_until_complete(MongoDB.insert("test", "test", {"aid": 2}))
  loop.run_until_complete(MongoDB.insert("test", "test", [
    {"aid": 1}, {"aid": 3}
  ]))