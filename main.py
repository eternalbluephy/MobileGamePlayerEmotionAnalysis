import sys
import asyncio
import json
from pathlib import Path
from bili.crawler.crawler import BiliCrawler
from weibo.crawler import WeiboCrawler
from common.log import get_logger
from common.db.bridge import transfer
from common.db.mongo import MongoDB
from common.crawler import random_sleep

BILIBILI_ROOT = Path(__file__).parent.joinpath("bili")
BILIBILI_MAX_PAGES = 100
WEIBO_ROOT = Path(__file__).parent.joinpath("weibo")
WEIBO_MAX_PAGES = 10

loop = asyncio.new_event_loop()
logger = get_logger("App")
bilibili_mids = [401742377, 161775300, 1340190821, 1636034895, 1955897084]
bilibili_crawlers = [BiliCrawler() for _ in range(5)]
weibo_uids = [6593199887, 6279793937, 7643376782, 7632078520, 7730797357]
weibo_crawler = WeiboCrawler()
fetch_bilibili_videos = "-bilibili-init" in sys.argv
fetch_weibo_articles = "-weibo-init" in sys.argv
with open(BILIBILI_ROOT.joinpath("headers.json"), "r", encoding="utf-8") as f:
  bilibili_headers = json.load(f)
with open(WEIBO_ROOT.joinpath("headers.json"), "r", encoding="utf-8") as f:
  weibo_headers = json.load(f)

mongo = MongoDB().client["MobileGameComments"]

async def bili_fetch_all_user_videos(mids) -> bool:
  for mid in mids:
    aids = await bilibili_crawlers[0].run_fetch_all_user_videos(mid, headers=bilibili_headers)
    for aid in aids:
      ok = await bilibili_crawlers[0].run_get_video_info(aid, headers=bilibili_headers)
      if not ok:
        return False
    await random_sleep(0.5, 0.7)
  return True

async def weibo_fetch_all_user_blogs(uids):
  for uid in uids:
    ok, _ = await weibo_crawler.run_fetch_all_user_blogs(uid, headers=weibo_headers)
    if not ok:
      return False
    await transfer(
      weibo_crawler.redis, "blogs", mongo["WeiboArticles"], logger=logger
    )
  return True

async def bilibili_run_crawler(crawlers: list[BiliCrawler], mids: list[int]):
  for mid in mids:
    cursor = mongo["BilibiliVideos"].find({"mid": mid})
    aids = asyncio.Queue()
    async for video in cursor:
      aids.put_nowait(video["_id"])

    async def task(crawler: BiliCrawler):
      while not aids.empty():
        aid = await aids.get()
        ok, _ = await crawler.run_get_comments(aid, headers=bilibili_headers)
        if not ok:
          return False
        await random_sleep(0.3, 0.5)

    tasks = [task(crawler) for crawler in crawlers]
    await asyncio.gather(*tasks)

async def weibo_run_crawler(crawler: WeiboCrawler, uids: list[int], max_pages: int = 10):
  for uid in uids:
    cursor = mongo["WeiboArticles"].find({"uid": uid})
    async for article in cursor:
      id = article["_id"]
      if article["finished"]:
        logger.info(f"文章{id}已爬取完毕，跳过")
        continue
      # 删除已存在的评论，防止重复
      await mongo["WeiboComments"].delete_many({"blogid": id})
      ok, _ = await crawler.run_fetch_blog_comments(uid, id, headers=weibo_headers, max_pages=max_pages)
      if ok:
        await transfer(crawler.redis, "comments", mongo["WeiboComments"], upsert=False, logger=logger)
      else:
        logger.error("爬取评论失败")
        return False
      logger.info(f"文章{id} 已爬取完毕")
      await mongo["WeiboArticles"].update_one({"_id": id}, {"$set": {"finished": True}})

async def main():

  async def bilibili_task():
    if fetch_bilibili_videos:
      ok = await bili_fetch_all_user_videos([1340190821, 1636034895, 1955897084])
      if not ok:
        logger.error("获取视频失败")
        return
    await bilibili_run_crawler(bilibili_crawlers, bilibili_mids)

  async def weibo_task():
    if fetch_weibo_articles:
      ok = await weibo_fetch_all_user_blogs([7632078520, 7730797357])
      if not ok:
        logger.error("获取文章失败")
        return
    await weibo_run_crawler(weibo_crawler, weibo_uids, WEIBO_MAX_PAGES)

  await asyncio.gather(bilibili_task(), weibo_task())


if __name__ == "__main__":
  asyncio.run(main())