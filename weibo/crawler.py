import sys
import json
import asyncio
import httpx
from redis import asyncio as aioredis
from pathlib import Path
from typing import Optional
from time import sleep

import_path = Path(__file__).parent.parent.parent
sys.path.append(str(import_path))

from common.crawler import random_sleep, Err, CrawlResult
from common.log import get_logger
from common.db.mongo import MongoDB
from common.db.redis import Redis
from .api import *


class WeiboCrawler:

  crawler_count = 0

  def __init__(self) -> None:
    WeiboCrawler.crawler_count += 1
    self.id = WeiboCrawler.crawler_count
    self.logger = get_logger(f"Weibo#{self.id}")
    self.redis = Redis(db=self.id)

  async def run_fetch_all_user_blogs(self, uid: int, **httpx_params) -> CrawlResult:
    """运行爬虫，获取指定uid用户的所有文章，并存储每个文章的数据"""
    self.logger.info(f"正在爬取 用户{uid} 的所有博文ID")
    st = set()

    page = 1
    since_id: Optional[str] = None
    res = ""
    async with httpx.AsyncClient(**httpx_params) as client:
      while True:
        try:
          res = await get_user_blogs.call(client, uid, page, since_id)
          data = json.loads(res)["data"]
          since_id = data["since_id"]
          blogs = data["list"]
          for blog in blogs:
            id = blog["id"]
            if id not in st: # 防止进入环
              st.add(id)
              blog_info = {
                "_id": id,
                "uid": blog["user"]["id"],
                "author": blog["user"]["screen_name"],
                "text": blog["text_raw"],
                "reposts": blog["reposts_count"],
                "comments": blog["comments_count"],
                "likes": blog["attitudes_count"],
                "time": blog["created_at"],
                "finished": False
              }
              await self.redis.client.lpush(f"blogs", json.dumps(blog_info))
          await random_sleep(0.5, 0.7)
          self.logger.info(f"第{page}页爬取完毕")
          if not since_id:
            self.logger.info(f"最后一页，退出")
            break
          page += 1
        except KeyError as e:
          self.logger.error(f"响应信息中没有键：{e}")
          return False, Err.FAILED
        except json.decoder.JSONDecodeError as e:
          self.logger.error(f"非JSON格式数据：{res}")
          return False, Err.FAILED
        except Exception as e:
          self.logger.exception(e)
          return False, Err.FAILED
    return True, None
  
  async def run_fetch_blog_comments(self, uid: int, id: int, max_pages: int = 10, **httpx_params):
    self.logger.info(f"正在爬取 用户{uid} 的 博文{id} 的评论")

    async with AsyncClient(**httpx_params) as client:
      max_id = None
      for page in range(1, max_pages + 1):
        try:
          self.logger.info(f"正在爬取 文章{id} 第{page}页")
          # 热度排序
          res = await get_comments.call(client, uid, id, flow=0, max_id=max_id)
          data = json.loads(res)
          comments_data = data["data"]
          for info in comments_data:
            comment = {
              "blogid": id,
              "time": info["created_at"],
              "likes": info["like_counts"],
              "content": info["text_raw"],
            }
            await self.redis.client.lpush("comments", json.dumps(comment))
          max_id = data["max_id"]
          if not max_id:
            self.logger.info("最后一页，退出")
            break
          await random_sleep(0.7, 0.7)

        except KeyError as e:
          self.logger.error(f"响应信息中没有键：{e}")
          return False, Err.FAILED
        except json.decoder.JSONDecodeError as e:
          self.logger.error(f"非JSON格式数据：{res}")
          return False, Err.FAILED
        except Exception as e:
          self.logger.exception(e)
          return False, Err.FAILED
      
    return True, None


    
      

if __name__ == "__main__":
  import asyncio
  from pathlib import Path
  from common.db.bridge import transfer
  logger = get_logger("WeiboCrawleController")
  crawler = WeiboCrawler()
  mongo = MongoDB().client["MobileGameComments"]
  loop = asyncio.new_event_loop()
  run = loop.run_until_complete

  with open(Path(__file__).parent.joinpath("headers.json"), "r", encoding="utf-8") as f:
    headers = json.loads(f.read())
  
  uids = [6593199887]

  if "videos" in sys.argv:
    for uid in uids:
      ok, _ = run(crawler.run_fetch_all_user_blogs(uid, headers=headers))
      if not ok:
        logger.error("获取所有文章失败")
      else:
        # TODO: 存入MongoDB
        run(transfer(
          crawler.redis, "blogs", mongo["WeiboArticles"], logger=logger
        ))
  
  async def main():
    for uid in uids:
      cursor = mongo["WeiboArticles"].find({"uid": uid})
      async for article in cursor:
        id = article["_id"]
        if article["finished"]:
          logger.info(f"文章{id}已爬取完毕，跳过")
          continue
        # 删除已存在的评论，防止重复
        await mongo["WeiboComments"].delete_many({"blogid": id})
        ok, _ = await crawler.run_fetch_blog_comments(uid, id, headers=headers)
        if ok:
          await transfer(crawler.redis, "comments", mongo["WeiboComments"], upsert=False, logger=logger)
        else:
          logger.error("爬取评论失败")
          break
        logger.info(f"文章{id} 已爬取完毕")
        await mongo["WeiboArticles"].update_one({"_id": id}, {"$set": {"finished": True}})

  run(main())
