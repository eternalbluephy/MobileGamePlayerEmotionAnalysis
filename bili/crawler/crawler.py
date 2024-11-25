import sys
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Sequence
from time import sleep

import_path = Path(__file__).parent.parent.parent
sys.path.append(str(import_path))

from common.crawler import random_sleep
from common.log import get_logger
from common.db.mongo import MongoDB
from bili.api import api
from bili.api.enums import Sort, STATUS_CODES, StatusCode
from bili.api.wbi import getWbiKeys, encWbi

class BiliCrawler:

  lock = asyncio.Lock()

  def __init__(self, headers: Optional[dict[str, str]] = None, max_pages: int = int(1e9)):
    self.collection = MongoDB.client["MobileGameComments"]["bilibili"]
    self.headers = headers
    self.logger = get_logger("BiliLogger")
    self.max_pages = max_pages
    self.img_key, self.sub_key = getWbiKeys()

  async def fetch_one_reply_reply(self, session: aiohttp.ClientSession, aid: int, rpid: int, page: int) -> Optional[list[dict]]:
    async def run_once():
      comments = []
      res = await api.fetch_reply_reply(session, aid, rpid, pn=page)
      data = json.loads(res)
      code = int(data["code"])
      if code != 0:
        self.logger.warning(f"获取评论的回复失败，代码：{code}，原因：{STATUS_CODES.get(code, '未知')}")
        return

      replies = data["data"]["replies"]
      if not replies:
        return comments

      for reply in replies:
        comment = {}
        comment["level"] = reply["member"]["level_info"]["current_level"]
        comment["time"] = reply["ctime"]
        comment["content"] = reply["content"]["message"]
        comment["like"] = reply["like"]
        comments.append(comment)
      return comments

    try:
      return await run_once()
    except KeyError as e:
      self.logger.warning(f"响应信息中没有键：{e}")
    except json.decoder.JSONDecodeError as e:
      self.logger.error(f"非JSON格式数据") # 大概率风控
      self.logger.warning("大概率风控，线程睡眠300秒，所有爬虫暂停...")
      while True:
        sleep(300)
        self.logger.info("重试中")
        try:
          return await run_once()
        except json.decoder.JSONDecodeError as e:
          self.logger.warning("依然风控，继续睡300秒")
          continue
        except:
          return
    except Exception as e:
      self.logger.exception(e)
      return
    
  async def fetch_one_page(self, session: aiohttp.ClientSession, aid: int, sort: Sort | int, page: int) -> Optional[dict[str, str]]:
    """爬取某个视频的某一页的所有评论"""
    comments = []
    self.logger.info(f"正在爬取视频 av{aid} 第{page}页")
    try:
      data = await api.fetch_reply(session, oid=str(aid), sort=sort, pn=page)
      data = json.loads(data)

      code = int(data["code"])
      if code != 0:
        self.logger.warning(f"获取评论失败，代码：{code}，原因：{STATUS_CODES.get(code, '未知')}")
        if code == StatusCode.Closed:
          return comments
        else:
          return
      
      replies = data["data"]["replies"]

      if not replies:
        self.logger.info(f"已到达视频 av{aid} 评论最后一页")
        return comments
      
      for reply in replies:
        comment = {}
        rpid = reply["rpid"]
        comment["level"] = reply["member"]["level_info"]["current_level"]
        comment["time"] = reply["ctime"]
        comment["content"] = reply["content"]["message"]
        comment["like"] = reply["like"]
        # 子评论
        sub_comments = []
        for page in range(1, int(1e9)):
          one_sub_comments = await self.fetch_one_reply_reply(session, aid, rpid, page)
          if one_sub_comments is None:
            return
          elif one_sub_comments:
            sub_comments.extend(one_sub_comments)
          else:
            break
          await random_sleep(0.3, 0.4)

        comment["replies"] = sub_comments
        comments.append(comment)
    except KeyError as e:
      self.logger.warning(f"响应信息中没有键：{e}")
    except Exception as e:
      self.logger.exception(e)
    return comments
    
  async def fetch_video_comments(self, session: aiohttp.ClientSession, aid: int, sort: Sort | int, start_page: int = 1) -> dict[str, str]:
    """爬取某个视频的评论区的所有评论"""
    self.logger.info(f"正在爬取视频 av{aid} 评论区的所有评论，从第{start_page}页开始")
    for page in range(start_page, self.max_pages + 1):
      comments = await self.fetch_one_page(session, aid=aid, sort=sort, page=page)
      if comments is None:
        self.logger.warning("无法获取视频评论，跳过")
        return
      elif comments:
        async with BiliCrawler.lock:
          await self.collection.update_one({"_id": aid}, {"$push": {"comments": {"$each": comments}}})
          await self.collection.update_one({"_id": aid}, {"$set": {"last_page": page}})
      else:
        self.logger.info(f"视频 av{aid} 所有评论爬取完毕")
        break
  
  async def fetch_video_info(self, session: aiohttp.ClientSession, aid: int) -> Optional[dict]:
    self.logger.info("正在爬取视频信息")
    try:
      res = await api.fetch_video_info(session, aid=aid)
      data = json.loads(res)
      code = int(data["code"])
      if code != 0:
        self.logger.warning(f"获取视频信息失败，代码：{code}，原因：{STATUS_CODES.get(code, '未知')}")
        return
      return {
        "author": data["data"]["owner"]["name"],
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

  async def run(self, aids: Sequence[int]) -> None:
    """运行爬虫"""
    self.logger.info("任务开始")

    async with aiohttp.ClientSession(headers=self.headers) as session:
      for aid in aids:
        self.logger.info(f"正在爬取视频 av{aid} ...")

        last_page = await self.get_last_page(aid)
        if last_page is None:
          self.logger.info("数据库中无此视频数据")
          document = {"_id": aid, "last_page": 0, "comments": []}

          #################################################################
          # 视频基本信息
          #################################################################
          info = await self.fetch_video_info(session, aid)
          if info is None:
            self.logger.warning(f"无法获取视频基本信息，跳过")
            await random_sleep(0.1, 0.3)
            continue
          document.update(info)
          async with BiliCrawler.lock:
            await self.collection.insert_one(document)
          last_page = 0
          await random_sleep(0.1, 0.3)
        elif last_page == -1:
          self.logger.info("该视频已爬取结束，跳过")
          await random_sleep(0.1, 0.3)
          continue
        else:
          self.logger.info("数据库中已存在该视频，将在已存储的数据的基础上更新")

        #################################################################
        # 评论区
        #################################################################
        await self.fetch_video_comments(session, aid, Sort.ByLikes, start_page=last_page + 1)
        
        self.logger.info(f"视频 av{aid} 爬取完毕")
        async with BiliCrawler.lock:
          await self.collection.update_one({"_id": aid}, {"$set": {"last_page": -1}})
        await random_sleep(0.2, 0.4)

  async def stop(self) -> None: ...

  async def fetch_all_user_videos(self,
                                  mid: int) -> list[int]:
    headers = self.headers
    headers["Referer"] = f"https://space.bilibili.com/{mid}/video?pn=1"

    self.logger.info(f"正在爬取用户 {mid} 的所有投稿视频")
    aids = []
    page = 1

    async with aiohttp.ClientSession(headers=headers) as session:
      while True:
        self.logger.info(f"正在爬取第{page}页投稿")
        try:
          data = json.loads(await api.fetch_user_videos(session, mid, pn=page, img_key=self.img_key, sub_key=self.sub_key))
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
        except KeyError as e:
          self.logger.warning(f"响应信息中没有键：{e}")
        except Exception as e:
          self.logger.exception(e)
          break
        page += 1

    return aids

  # async def fetch_username(self, mid: int) -> Optional[int]:
  #   headers = self.headers
  #   headers["Referer"] = f"https://space.bilibili.com/401742377"
  #   self.logger.info(f"正在获取 用户{mid} 的昵称")
  #   try:
  #     async with aiohttp.ClientSession(headers=headers) as session:
  #       data = await api.fetch_user_info(session, mid, self.img_key, self.sub_key)
  #       with open("res.json", "w", encoding="utf-8") as f:
  #         f.write(data)
  #       data = json.loads(data)
  #       name = data["name"]
  #       self.logger.info(f"获取成功，昵称为：{name}")
  #       return name
  #   except KeyError as e:
  #     self.logger.warning(f"响应信息中没有键：{e}")
  #   except Exception as e:
  #     self.logger.error(e.with_traceback())
  
  async def get_last_page(self, aid: int) -> Optional[int]:
    async with BiliCrawler.lock:
      result = await self.collection.find_one({"_id": aid})
    return result if result is None else result["last_page"]


if __name__ == "__main__":
  import asyncio

  HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Cookie": "buvid3=045FFA68-F00D-9CD3-51BD-CC7EFF43B56C74211infoc; b_nut=1727859074; _uuid=4103EF1011-5BE1-EF93-291E-B48F17BBE1010474375infoc; header_theme_version=CLOSE; enable_web_push=DISABLE; home_feed_column=5; CURRENT_FNVAL=4048; rpdid=|(kJRYmJRmY|0J'u~k~)~)Rkl; buvid_fp_plain=undefined; buvid4=33D3C568-8110-0DA3-7F91-0EDEDD2FF65476357-024100208-EftFjGYzK8e%2BnmvtDmyFEYC8vC7CPXisBgZC93SEz739%2BeRPEAXBVPhLcxB9be7g; fingerprint=31aaa664aa47a99ff5c8dbfa3eae9a2a; buvid_fp=31aaa664aa47a99ff5c8dbfa3eae9a2a; LIVE_BUVID=AUTO4417299433676539; PVID=2; SESSDATA=ccf84baf%2C1747890518%2C72b7c%2Ab1CjAZL_G-5mnbS4dvknpKQ-hzSZ_EYiDe7yhcvr8S1IKU3FOUiqN1Eivt-jFXlq4bdmESVkgwUjVPelIyblE2N2lnOE1JTC1XYzlDOUI2RXZ6dXFJd3dmLTdWaU52REpDWEphUXJPTzRZZDlvcm1LdUJWX2ZpbW8yOGNUZTNlZHZDeDNtalpqejdBIIEC; bili_jct=64fe0b1f1d387e0e490a6d65239b9948; DedeUserID=38921801; DedeUserID__ckMd5=b1bdb63ebdbbfd3c; bp_t_offset_38921801=1002889277526245376; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzI2MTg1ODQsImlhdCI6MTczMjM1OTMyNCwicGx0IjotMX0.bUbzAeyU2GW7sdRTJHpz_6Rv_3wCQDhUo_9gVPyxGAY; bili_ticket_expires=1732618524; b_lsid=B24102724_1935C221F69; match_float_version=ENABLE; sid=o2ky4vnz; browser_resolution=1507-992",
    "accept-language": "en,zh-CN;q=0.9,zh;q=0.8",
  }
  MongoDB()
  crawlers = [BiliCrawler(headers=HEADERS)] * 2

  GENSHIN_MID = 401742377
  GENSHIN_AIDS = asyncio.run(crawlers[0].fetch_all_user_videos(401742377))

  queue = asyncio.Queue()
  for aid in GENSHIN_AIDS:
    queue.put_nowait(aid)
  async def work(crawler: BiliCrawler):
    while not queue.empty():
      try:
        aid = await queue.get()
        await crawler.run((aid, ))
      finally:
        queue.task_done()
  
  tasks = [work(crawler) for crawler in crawlers]

  async def main():
    await asyncio.gather(*tasks)
  asyncio.run(main())
  