# See https://github.com/SocialSisterYi/bilibili-API-collect/
import sys
import json
import urllib.parse
from typing import Optional
from httpx import AsyncClient
from pathlib import Path

import_path = Path(__file__).parent.parent.parent
sys.path.append(str(import_path))

from common.api import AsyncAPI
from .enums import Sort
from .wbi import getWbiKeys, encWbi

async def fetch_reply(client: AsyncClient,
                      oid: str,
                      sort: Sort | int = 0,
                      ps: int = 20,
                      pn: int = 1) -> str:
  """
  获取视频评论
  详见 https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/comment/list.md
  Args:
    client(AsyncClient): httpx会话
    oid(str): 视频号
    sort(Sort | int): 评论排序
    ps(int): 每页评论数(1-20)
    pn(int): 爬取第几页
  """
  URL = "http://api.bilibili.com/x/v2/reply"
  response = await client.get(f"{URL}?oid={oid}&type=1&sort={int(sort)}&ps={ps}&pn={pn}")
  return response.text
  

class fetch_reply_wbi(AsyncAPI):

  @staticmethod
  async def call(client: AsyncClient,
                  oid: int,
                  page: int = 1,
                  mode: int = 3,
                  img_key: Optional[str] = None,
                  sub_key: Optional[str] = None) -> str:
    URL = "http://api.bilibili.com/x/v2/reply/wbi/main"
    if not img_key or not sub_key:
      img_key, sub_key = getWbiKeys()
    params = encWbi({
      "oid": oid, "type": 1, "mode": mode, "next": page
    }, img_key, sub_key)
    response = await client.get(f"{URL}?{urllib.parse.urlencode(params)}", timeout=2000)
    return response.text
  
  @staticmethod
  async def test(headers: dict | None = None, proxy: str | None = None) -> bool:
    URL = "http://api.bilibili.com/x/v2/reply/wbi/main"
    img_key, sub_key = getWbiKeys()
    params = encWbi({
      "oid": 1256438678, "type": 1, "mode": 3, "next": 76642,
    }, img_key, sub_key)
    try:
      async with AsyncClient(headers=headers, proxies=proxy) as client:
        print(f"{URL}?{urllib.parse.urlencode(params)}")
        response = await client.get(f"{URL}?{urllib.parse.urlencode(params)}")
        with open("./res.json", "w", encoding="utf-8") as f:
          f.write(response.text)
        return response.status_code == 200 and json.loads(response.text)["code"] == 0
    except:
      return False

  
class fetch_reply_reply(AsyncAPI):

  @staticmethod
  async def call(client: AsyncClient,
                  oid: int,
                  rpid: int,
                  ps: int = 20,
                  pn: int = 1,
                  return_url: bool = False) -> str:
    """
    获取评论的所有回复
    详见 https://github.com/SocialSisterYi/bilibili-API-collect/blob/e5fbfed42807605115c6a9b96447f6328ca263c5/docs/comment/list.md
    Args:
      client(AsyncClient): httpx会话
      oid(int): 视频号
      rpid(int): 根回复id
      ps(int): 每页评论数(1-20)
      pn(int): 爬取第几页
      return_url(bool): 是否返回请求url
    """
    url = f"http://api.bilibili.com/x/v2/reply/reply?oid={oid}&type=1&root={rpid}&ps={ps}&pn={pn}"
    response = await client.get(url)
    if return_url:
      return response.text, url
    else:
      return response.text
    
  @staticmethod
  async def test(headers: dict | None = None, proxies: str | None = None) -> bool:
    url = "http://api.bilibili.com/x/v2/reply/reply?oid=1806390382&type=1&root=238657832256&ps=20&pn=1"
    try:
      async with AsyncClient(headers=headers, proxies=proxies) as client:
        response = await client.get(url)
        return response.status_code == 200 and json.loads(response.text)["code"] == 0
    except:
      return False


async def fetch_tags(client: AsyncClient,
                     aid: Optional[int] = None,
                     bvid: Optional[str] = None) -> str:
  """
  获取视频标签
  详见 https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/video/tags.md
  Args:
    client(AsyncClient): httpx会话
    aid(int | None): 视频av号，此参数与`bvid`参数两者选其一
    bvid(str | None): 视频bv号，此参数与`aid`参数两者选其一
  """
  id = aid if bvid is None else bvid
  type = "aid" if bvid is None else "bvid"
  if not id:
    raise ValueError("aid和bvid需要其中一个不为空")
  URL = "http://api.bilibili.com/x/tag/archive/tags"
  response = await client.get(f"{URL}?{type}={id}")
  return response.text
  

async def fetch_video_info(client: AsyncClient,
                           aid: Optional[int] = None,
                           bvid: Optional[str] = None) -> str:
  """
  获取视频基本信息
  详见 https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/video/info.md
  Args:
    client(AsyncClient): httpx会话
    aid(int | None): 视频av号，此参数与`bvid`参数两者选其一
    bvid(str | None): 视频bv号，此参数与`aid`参数两者选其一
  """
  id = aid if bvid is None else bvid
  type = "aid" if bvid is None else "bvid"
  if not id:
    raise ValueError("aid和bvid需要其中一个不为空")
  URL = "https://api.bilibili.com/x/web-interface/view"
  response = await client.get(f"{URL}?{type}={id}")
  return response.text
  

async def fetch_user_videos(client: AsyncClient, 
                            mid: int,
                            ps: int = 30,
                            pn: int = 1,
                            img_key: Optional[str] = None,
                            sub_key: Optional[str] = None) -> str:
  URL = "http://api.bilibili.com/x/space/wbi/arc/search"
  if not img_key or not sub_key:
    img_key, sub_key = getWbiKeys()
  params = encWbi({
    "mid": mid, "ps": ps, "pn": pn
  }, img_key, sub_key)
  response = await client.get(f"{URL}?{urllib.parse.urlencode(params)}")
  return response.text


async def fetch_user_info(client: AsyncClient,
                          mid: int,
                          img_key: Optional[str] = None,
                          sub_key: Optional[str] = None) -> str:
  URL = "http://api.bilibili.com/x/space/wbi/acc/info"
  if not img_key or not sub_key:
    img_key, sub_key = getWbiKeys()
  params = encWbi({
    "mid": mid, "platform": "web",
  }, img_key, sub_key)
  response = await client.get(f"{URL}?{urllib.parse.urlencode(params)}")
  return response.text


if __name__ == "__main__":
  import asyncio
  headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Cookie": "buvid3=045FFA68-F00D-9CD3-51BD-CC7EFF43B56C74211infoc; b_nut=1727859074; _uuid=4103EF1011-5BE1-EF93-291E-B48F17BBE1010474375infoc; header_theme_version=CLOSE; enable_web_push=DISABLE; CURRENT_FNVAL=4048; rpdid=|(kJRYmJRmY|0J'u~k~)~)Rkl; buvid_fp_plain=undefined; buvid4=33D3C568-8110-0DA3-7F91-0EDEDD2FF65476357-024100208-EftFjGYzK8e%2BnmvtDmyFEYC8vC7CPXisBgZC93SEz739%2BeRPEAXBVPhLcxB9be7g; LIVE_BUVID=AUTO4417299433676539; PVID=2; DedeUserID=38921801; DedeUserID__ckMd5=b1bdb63ebdbbfd3c; fingerprint=0dab010e3e14d0ef598b5b67f1397bbf; buvid_fp=0dab010e3e14d0ef598b5b67f1397bbf; bp_t_offset_38921801=1003621801378447360; home_feed_column=5; browser_resolution=1455-755; b_lsid=8BE7F64C_1936BAAC5B6; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzI5MzczNzUsImlhdCI6MTczMjY3ODExNSwicGx0IjotMX0.BvIOwdefEACWTnNKveDRqZjXFZKfW1BZf_MQl95m25c; bili_ticket_expires=1732937315; SESSDATA=0f2f23d5%2C1748230175%2Cfe534%2Ab1CjBFp5fgM3x4k0Vs8PFJoG7XAHliUVGeUFt6buQadN25-C1r9K9M1Sbtm7aMiOAED3MSVlNzYU9QTlNuOHN0QURLN0VuMTJTMWhsWmpKVlVVSnNFTEZobzRiQ1BNTXoxLTgwcWp3R2NQd182RXhONFVvekczZnlTWVIwTjliZzAzQ1ZhRkZHN3NRIIEC; bili_jct=0ca01b6a3e0fcaf3a2a22759145eb89c; sid=6cgz3wci",
  }

  asyncio.run(fetch_reply_wbi.test(headers=headers))