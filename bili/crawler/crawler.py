import sys
import json
import asyncio
import httpx
from copy import deepcopy
from pathlib import Path
from typing import Optional
from time import sleep

import_path = Path(__file__).parent.parent.parent
sys.path.append(str(import_path))

from common.crawler import random_sleep, Err, CrawlResult
from common.log import get_logger
from common.db.mongo import MongoDB
from bili.api import api
from bili.api.enums import STATUS_CODES, StatusCode
from bili.api.wbi import getWbiKeys

class BiliCrawler:

  lock = asyncio.Lock()
  crawler_count = 0

  def __init__(self):
    self.db = MongoDB().client["MobileGameComments"]
    self.img_key, self.sub_key = getWbiKeys()
    # 爬虫ID
    BiliCrawler.crawler_count += 1
    self.id = BiliCrawler.crawler_count
    self.logger = get_logger(f"Bilibili#{self.id}")

  async def fetch_one_reply_reply(self, client: httpx.Client, aid: int, rpid: int, page: int) -> CrawlResult:
    res, url = "", ""
    async def run_once() -> CrawlResult:
      nonlocal url, res
      res, url = await api.fetch_reply_reply.call(client, aid, rpid, pn=page, return_url=True)
      data = json.loads(res)
      code = int(data["code"])
      if code != 0:
        self.logger.warning(f"获取评论的回复失败，代码：{code}，原因：{STATUS_CODES.get(code, '未知')}")
        return False, Err.FAILED

      replies = data["data"]["replies"]
      if not replies:
        return False, Err.EOF

      for reply in replies:
        comment = {}
        comment["aid"] = aid
        comment["level"] = reply["member"]["level_info"]["current_level"]
        comment["time"] = reply["ctime"]
        comment["content"] = reply["content"]["message"]
        comment["like"] = reply["like"]
        comment["is_root"] = False
        async with BiliCrawler.lock:
          await self.db["BilibiliComments"].insert_one(comment)
      return True, None

    try:
      return await run_once()
    except KeyError as e:
      self.logger.warning(f"响应信息中没有键：{e}")
    except json.decoder.JSONDecodeError as e:
      self.logger.error(f"非JSON格式数据：{res}") # 大概率风控
      self.logger.info(f"可以尝试访问{url}")
      self.logger.warning("大概率风控，线程睡眠17分钟，所有爬虫暂停...")
      while True:
        sleep(1020)
        self.logger.info("重试中")
        try:
          return await run_once()
        except json.decoder.JSONDecodeError as e:
          self.logger.warning("依然风控，继续等待17分钟")
          continue
        except:
          return False, Err.FAILED
    except Exception as e:
      self.logger.exception(e)
      return False, Err.FAILED
    
  async def fetch_one_page(self, client: httpx.Client, aid: int, page: int) -> CrawlResult:
    """爬取某个视频的某一页的所有评论"""
    self.logger.info(f"正在爬取视频 av{aid} 第{page}页")
    try:
      data = await api.fetch_reply_wbi.call(client, oid=str(aid), page=page, img_key=self.img_key, sub_key=self.sub_key)
      data = json.loads(data)

      code = int(data["code"])
      if code != 0:
        self.logger.warning(f"获取评论失败，代码：{code}，原因：{STATUS_CODES.get(code, '未知')}")
        if code == StatusCode.Closed:
          return False, Err.EOF
        else:
          return False, Err.FAILED
      
      replies = data["data"]["replies"]

      if not replies:
        self.logger.info(f"已到达视频 av{aid} 评论最后一页")
        return False, Err.EOF
      
      for reply in replies:
        comment = {}
        comment["rpid"] = reply["rpid"]
        comment["aid"] = aid
        comment["level"] = reply["member"]["level_info"]["current_level"]
        comment["time"] = reply["ctime"]
        comment["content"] = reply["content"]["message"]
        comment["like"] = reply["like"]
        comment["rpid"] = reply["rpid"]
        comment["is_root"] = True
        await self.db["BilibiliComments"].insert_one(comment)
        # 子评论
        for rreply in reply["replies"]:
          sub_comment = {}
          sub_comment["rpid"] = rreply["rpid"]
          sub_comment["aid"] = aid
          sub_comment["level"] = rreply["member"]["level_info"]["current_level"]
          sub_comment["time"] = rreply["ctime"]
          sub_comment["content"] = rreply["content"]["message"]
          sub_comment["like"] = rreply["like"]
          sub_comment["rpid"] = rreply["rpid"]
          sub_comment["is_root"] = False
          await self.db["BilibiliComments"].insert_one(sub_comment)
      await self.db["BilibiliVideos"].update_one({"_id": aid}, {"$set": {"last_page": page}})
    except KeyError as e:
      self.logger.warning(f"响应信息中没有键：{e}")
      return False, Err.FAILED
    except json.decoder.JSONDecodeError:
      return False, Err.FAILED
    except Exception as e:
      self.logger.exception(e)
      exit(-1)
      return False, Err.FAILED
    return True, None
    
  async def fetch_video_comments(self, client: httpx.Client, aid: int, start_page: int = 1, max_pages: int = 100) -> CrawlResult:
    """爬取某个视频的评论区的所有评论"""
    self.logger.info(f"正在爬取视频 av{aid} 评论区的所有评论，从第{start_page}页开始")
    for page in range(start_page, max_pages + 1):
      res, err = await self.fetch_one_page(client, aid=aid, page=page)
      if not res and err != Err.EOF:
        self.logger.warning("无法获取视频评论，跳过")
        return res, err
      elif err == Err.EOF:
        self.logger.info(f"视频 av{aid} 所有评论爬取完毕")
        break
      # await random_sleep(0.1, 0.3)
    return True, None
  
  async def fetch_video_info(self, client: httpx.Client, aid: int) -> Optional[dict]:
    self.logger.info("正在爬取视频信息")
    try:
      res = await api.fetch_video_info(client, aid=aid)
      data = json.loads(res)
      code = int(data["code"])
      if code != 0:
        self.logger.warning(f"获取视频信息失败，代码：{code}，原因：{STATUS_CODES.get(code, '未知')}")
        return
      return {
        "author": data["data"]["owner"]["name"],
        "mid": data["data"]["owner"]["mid"],
        "title": data["data"]["title"],
        "view": data["data"]["stat"]["view"],
        "like": data["data"]["stat"]["like"],
        "pubtime": int(data["data"]["pubdate"]),
      }
    except KeyError as e:
      self.logger.warning(f"响应信息中没有键：{e}")
    except json.decoder.JSONDecodeError as e:
      self.logger.error(f"非JSON格式数据：{res}")
    except Exception as e:
      self.logger.exception(e)

  async def run_get_comments(self, aid: int, headers: Optional[dict] = None, proxy: Optional[str] = None) -> CrawlResult:
    """运行爬虫，爬取一个视频的信息和评论"""

    self.logger.info(f"正在爬取视频 av{aid} 的所有评论")
    if not headers:
      self.logger.warning("未设置请求头，可能无法正常爬取数据")
    if proxy:
      self.logger.info(f"使用代理：{proxy}")
      proxy = {"http://": proxy, "https://": proxy}

    async with httpx.AsyncClient(headers=headers, proxies=proxy, verify=False, follow_redirects=True) as client:

      last_page = await self.get_last_page(aid)
      if last_page is None:
        self.logger.warning(f"数据库中无此视频（av{aid}）数据，跳过")
        return False, Err.NOT_EXISTS
      else:
        self.logger.info("数据库中已存在该视频，将在已存储的数据的基础上更新")

      res, err = await self.fetch_video_comments(client, aid, start_page=last_page + 1)
      if not res:
        return res, err
        
    self.logger.info(f"视频 av{aid} 评论爬取完毕")
    return True, None
  
  async def run_get_video_info(self, aid: int, headers: Optional[dict] = None, proxy: Optional[str] = None) -> bool:
    self.logger.info(f"正在爬取视频 av{aid} 的基本信息")
    if not headers:
      self.logger.warning("未设置请求头，可能无法正常爬取数据")
    if proxy:
      self.logger.info(f"使用代理：{proxy}")
      proxy = {"https://": proxy}

    async with httpx.AsyncClient(headers=headers, proxies=proxy, verify=False, follow_redirects=True) as client:
      last_page = await self.get_last_page(aid)
      if last_page is None:
        self.logger.info("数据库中无此视频数据")
        document = {"_id": aid, "last_page": 0, "comments": []}
        info = await self.fetch_video_info(client, aid)
        if info is None:
          self.logger.warning(f"无法获取视频基本信息，跳过")
          await random_sleep(0.3, 0.4)
          return False
        document.update(info)
        async with BiliCrawler.lock:
          await self.db["BilibiliVideos"].update_one({"_id": aid}, {"$set": document}, upsert=True)
        last_page = 0
        await random_sleep(0.3, 0.4)
      else:
        self.logger.info("数据库中已存在该视频，跳过")

    self.logger.info(f"爬取视频 av{aid} 结束")
    return True
  
  async def get_last_page(self, aid: int) -> Optional[int]:
    async with BiliCrawler.lock:
      result = await self.db["BilibiliVideos"].find_one({"_id": aid})
    return result if result is None else result["last_page"]
  
  async def run_fetch_all_user_videos(self,
                                      mid: int,
                                      **http_params) -> list[int]:
    params = deepcopy(http_params)
    params["headers"] = params.get("headers", {})
    params["headers"]["Referer"] = f"https://space.bilibili.com/{mid}/video?pn=1"

    self.logger.info(f"正在爬取用户 {mid} 的所有投稿视频")
    aids = []
    page = 1

    async with httpx.AsyncClient(**params) as client:
      while True:
        self.logger.info(f"正在爬取第{page}页投稿")
        try:
          res = await api.fetch_user_videos(client, mid, pn=page, img_key=self.img_key, sub_key=self.sub_key)
          data = json.loads(res)
          code = data["code"]
          if code != 0:
            self.logger.warning(f"获取用户投稿视频失败，代码：{code}，原因：{STATUS_CODES.get(code, '未知')}")
            break
          vlist = data["data"]["list"]["vlist"]
          if not vlist:
            self.logger.info("最后一页，结束")
            break
          for video in vlist:
            aids.append(video["aid"])
          await random_sleep(1, 1)
        except KeyError as e:
          self.logger.warning(f"响应信息中没有键：{e}")
          return False
        except json.decoder.JSONDecodeError as e:
          self.logger.exception(f"非JSON格式数据：{e}")
          return False
        except Exception as e:
          self.logger.exception(e)
          break
        page += 1

    return aids
  

class BiliCrawlerRunner: ...


if __name__ == "__main__":
  import asyncio
  import pathlib
  from common.iptest import async_test as test_ip

  CACHE_PATH = pathlib.Path(__file__).parent.parent.parent.joinpath("cache")
  PROXIES_PATH = pathlib.Path(__file__).parent.parent.parent.joinpath("proxies.txt")
  GENSHIN_AIDS_PATH = CACHE_PATH.joinpath("bili_genshin_aids.txt")

  with open(pathlib.Path(__file__).parent.joinpath("headers.json")) as f:
    headers = json.load(f)

  uids = [401742377,]

  MongoDB()
  logger = get_logger("BilibiliCrawlerController")

  proxies = asyncio.Queue()
  # if PROXIES_PATH.exists():
  #   with open(PROXIES_PATH, "r", encoding="utf-8") as f:
  #     proxy_list = [line.strip() for line in f.readlines()]
  # async def test_proxies():
  #   async def _test_ip(ip):
  #     # ok = await test_ip(ip, "http://api.bilibili.com/x/v2/reply/reply?oid=712909579&type=1&root=3762650428&ps=10&pn=1")
  #     # ok = await test_ip(ip, "https://api.bilibili.com/x/web-interface/view?aid=113225672758114")
  #     ok = False
  #     if ok:
  #       logger.info(f"测试代理可用性：{ip} - ok")
  #       await proxies.put(ip)    
  #     else:
  #       logger.warning(f"测试代理可用性：{ip} - failed")
  #   tests = [_test_ip(ip) for ip in proxy_list]
  #   await asyncio.gather(*tests)
  # asyncio.run(test_proxies())

  # 根据可用代理数决定爬虫数量
  crawlers = [BiliCrawler() for _ in range(5)]
  logger.info(f"实例化{len(crawlers)}个爬虫")

  if not GENSHIN_AIDS_PATH.exists():
    GENSHIN_MID = 401742377
    GENSHIN_AIDS = asyncio.run(crawlers[0].fetch_all_user_videos(401742377, headers=headers))
    with open(GENSHIN_AIDS_PATH, "w", encoding="utf-8") as f:
      f.write("\n".join(map(str, GENSHIN_AIDS)))
  else:
    with open(GENSHIN_AIDS_PATH, "r", encoding="utf-8") as f:
      GENSHIN_AIDS = list(map(int, f.readlines()))

  # 基本运行框架
  queue = asyncio.Queue()
  for aid in GENSHIN_AIDS:
    queue.put_nowait(aid)
  async def work(crawler: BiliCrawler):
    while not queue.empty():
      try:
        aid = await queue.get()
        ok = False
        while not ok:
          proxy = None if proxies.empty() else (await proxies.get())
          ok = await crawler.run_get_comments(aid, headers=headers, proxy=proxy)
          await random_sleep(0.3, 0.4)
          if proxy:
            await proxies.put(proxy)
      finally:
        queue.task_done()
  
  tasks = [work(crawler) for crawler in crawlers]

  async def main():
    await asyncio.gather(*tasks)
  asyncio.run(main())
  