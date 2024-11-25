# See https://github.com/SocialSisterYi/bilibili-API-collect/

import aiohttp
import urllib.parse
from typing import Optional

from .enums import Sort
from .wbi import getWbiKeys, encWbi

async def fetch_reply(session: aiohttp.ClientSession,
                      oid: str,
                      sort: Sort | int = 0,
                      ps: int = 20,
                      pn: int = 1) -> str:
  """
  获取视频评论
  详见 https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/comment/list.md
  Args:
    session(ClientSession): aiohttp会话
    oid(str): 视频号
    sort(Sort | int): 评论排序
    ps(int): 每页评论数(1-20)
    pn(int): 爬取第几页
  """
  URL = "https://api.bilibili.com/x/v2/reply"
  async with session.get(f"{URL}?oid={oid}&type=1&sort={int(sort)}&ps={ps}&pn={pn}") as response:
    return await response.text(encoding="utf-8")
  

async def fetch_reply_wbi(session: aiohttp.ClientSession,
                          oid: int,
                          page: int = 1,
                          mode: int = 3,
                          img_key: Optional[str] = None,
                          sub_key: Optional[str] = None) -> str:
  URL = "https://api.bilibili.com/x/v2/reply/wbi/main"
  if not img_key or not sub_key:
    img_key, sub_key = getWbiKeys()
  params = encWbi({
    "oid": oid, "type": 1, "mode": mode, "next": page
  }, img_key, sub_key)
  async with session.get(f"{URL}?{urllib.parse.urlencode(params)}") as response:
    return await response.text(encoding="utf-8")
  

async def fetch_reply_reply(session: aiohttp.ClientSession,
                            oid: int,
                            rpid: int,
                            ps: int = 20,
                            pn: int = 1) -> str:
  """
  获取评论的所有回复
  详见 https://github.com/SocialSisterYi/bilibili-API-collect/blob/e5fbfed42807605115c6a9b96447f6328ca263c5/docs/comment/list.md
  Args:
    session(ClientSession): aiohttp会话
    oid(int): 视频号
    rpid(int): 根回复id
    ps(int): 每页评论数(1-20)
    pn(int): 爬取第几页
  """
  URL = "https://api.bilibili.com/x/v2/reply/reply"
  async with session.get(f"{URL}?oid={oid}&type=1&root={rpid}&ps={ps}&pn={pn}") as response:
    return await response.text(encoding="utf-8")
  

async def fetch_tags(session: aiohttp.ClientSession,
                     aid: Optional[int] = None,
                     bvid: Optional[str] = None) -> str:
  """
  获取视频标签
  详见 https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/video/tags.md
  Args:
    session(ClientSession): aiohttp会话
    aid(int | None): 视频av号，此参数与`bvid`参数两者选其一
    bvid(str | None): 视频bv号，此参数与`aid`参数两者选其一
  """
  id = aid if bvid is None else bvid
  type = "aid" if bvid is None else "bvid"
  if not id:
    raise ValueError("aid和bvid需要其中一个不为空")
  URL = "https://api.bilibili.com/x/tag/archive/tags"
  async with session.get(f"{URL}?{type}={id}") as response:
    return await response.text(encoding="utf-8")
  

async def fetch_video_info(session: aiohttp.ClientSession,
                           aid: Optional[int] = None,
                           bvid: Optional[str] = None) -> str:
  """
  获取视频基本信息
  详见 https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/video/info.md
  Args:
    session(ClientSession): aiohttp会话
    aid(int | None): 视频av号，此参数与`bvid`参数两者选其一
    bvid(str | None): 视频bv号，此参数与`aid`参数两者选其一
  """
  id = aid if bvid is None else bvid
  type = "aid" if bvid is None else "bvid"
  if not id:
    raise ValueError("aid和bvid需要其中一个不为空")
  URL = "https://api.bilibili.com/x/web-interface/view"
  async with session.get(f"{URL}?{type}={id}") as response:
    return await response.text(encoding="utf-8")
  

async def fetch_user_videos(session: aiohttp.ClientSession, 
                            mid: int,
                            ps: int = 30,
                            pn: int = 1,
                            img_key: Optional[str] = None,
                            sub_key: Optional[str] = None) -> str:
  URL = "https://api.bilibili.com/x/space/wbi/arc/search"
  if not img_key or not sub_key:
    img_key, sub_key = getWbiKeys()
  params = encWbi({
    "mid": mid, "ps": ps, "pn": pn
  }, img_key, sub_key)
  async with session.get(f"{URL}?{urllib.parse.urlencode(params)}") as response:
    return await response.text(encoding="utf-8")


async def fetch_user_info(session: aiohttp.ClientSession,
                          mid: int,
                          img_key: Optional[str] = None,
                          sub_key: Optional[str] = None) -> str:
  URL = "https://api.bilibili.com/x/space/wbi/acc/info"
  if not img_key or not sub_key:
    img_key, sub_key = getWbiKeys()
  params = encWbi({
    "mid": mid, "platform": "web",
  }, img_key, sub_key)
  print(f"{URL}?{urllib.parse.urlencode(params)}")
  async with session.get(f"{URL}?{urllib.parse.urlencode(params)}") as response:
    return await response.text(encoding="utf-8")