import asyncio
import logging
import json
from motor.motor_asyncio import AsyncIOMotorCollection
from .mongo import MongoDB
from .redis import Redis


async def transfer(redis: Redis,
                   name: str,
                   collection: AsyncIOMotorCollection,
                   upsert: bool = True,
                   batch_size: int = 1000,
                   logger: logging.Logger | None = None,
                   delete: bool = True) -> None:
  """
  将数据从Redis列表中分块写入MongoDB
  Args:
    redis(Redis): redis连接对象
    name(str): redis list名称
    collection(AsyncIOMotorCollection): 要写入的异步MongoDB集合
    upsert(bool): 是否优先更新而不是插入，默认为True
    batch_size(int): 单次插入数量，默认为1000
  """
  if logger:
    logger.info(f"准备从Redis缓存写入MongoDB")
  length = await redis.client.llen(name)
  if logger:
    logger.info(f"总数量：{length}，块大小：{batch_size}")

  for i in range(0, length, batch_size):
    j = min(i + batch_size - 1, length - 1)
    if logger:
      logger.info(f"正在写入第{i + 1}-{j + 1}条数据")
    r = await redis.client.lrange(name, i, j)
    data = [json.loads(x) for x in r]
    if not data:
      break
    if upsert:
      await MongoDB.upsert_many(collection, data)
    else:
      await collection.insert_many(data)
    
  if delete:
    await redis.client.delete(name)
    