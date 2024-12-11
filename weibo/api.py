import sys
from aiohttp import ClientSession
from typing import Optional
from pathlib import Path

import_path = Path(__file__).parent.parent.parent
sys.path.append(str(import_path))

from common.api import AsyncAPI

class get_user_blogs(AsyncAPI):
  @staticmethod
  async def call(session: ClientSession,
           uid: int,
           page: int = 1,
           since_id: Optional[str] = None) -> str:
    url = f"https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}&feature=0"
    if since_id is not None:
      url += f"&sinceId={since_id}"
    async with session.get(url) as response:
      return await response.text(encoding="utf-8")
  

class get_comments(AsyncAPI):
  @staticmethod
  async def call(session: ClientSession,
                 uid: int, id: int,
                 is_asc: Optional[int] = None,
                 flow: Optional[int] = None,
                 count: int = 20,
                 is_show_bulletin: int = 1,
                 is_mix: int = 0) -> str:
    """
    获取微博评论
    Args:
      session(ClientSession): aiohttp会话
      uid(int): 博客所属用户id
      id(int): 博客id
      is_asc(int | None): 当主评论按时间正序排序时，该字段为1；主评论按时间倒序时，该字段为0
      flow(int | None): 当主评论按热度排序时，该字段为0；当回复按热度排序时，该字段为0；回复按时间倒序时，该字段为1
      count(int): 每页评论数
      is_show_bulletin(int): 当查看主评论时，为1；查看回复时，为2
      is_mix: 当查看主评论时，为0；查看回复时，为1
    """
    url = f"https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={id}&is_show_bulletin={is_show_bulletin}&is_mix={is_mix}&count={count}&uid={uid}&fetch_level=0&locale=zh-CN"
    if is_asc is not None:
      url += f"&is_asc={is_asc}"
    if flow is not None:
      url += f"&flow={flow}"
    async with session.get(url) as response:
      return await response.text(encoding="utf-8")
  

if __name__ == "__main__":
  import asyncio
  import json
  import pathlib

  HEADERS_PATH = pathlib.Path(__file__).parent.joinpath("headers.json")
  with open(HEADERS_PATH, "r", encoding="utf-8") as f:
    headers = json.load(f)

  async def test_get_user_blogs(uid: int, page: int = 1, since_id: Optional[str] = None):
    async with ClientSession(headers=headers) as session:
      return await get_user_blogs(session, uid, page, since_id)
  
  with open("./res.json", "w", encoding="utf-8") as f:
    f.write(asyncio.run(test_get_user_blogs(6593199887, 2, "5102725391454353kp2")))