import urllib.parse
import aiohttp
import asyncio
from bili.api import api

HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
  "Cookie": "buvid3=045FFA68-F00D-9CD3-51BD-CC7EFF43B56C74211infoc; b_nut=1727859074; _uuid=4103EF1011-5BE1-EF93-291E-B48F17BBE1010474375infoc; header_theme_version=CLOSE; enable_web_push=DISABLE; home_feed_column=5; CURRENT_FNVAL=4048; rpdid=|(kJRYmJRmY|0J'u~k~)~)Rkl; buvid_fp_plain=undefined; buvid4=33D3C568-8110-0DA3-7F91-0EDEDD2FF65476357-024100208-EftFjGYzK8e%2BnmvtDmyFEYC8vC7CPXisBgZC93SEz739%2BeRPEAXBVPhLcxB9be7g; fingerprint=31aaa664aa47a99ff5c8dbfa3eae9a2a; buvid_fp=31aaa664aa47a99ff5c8dbfa3eae9a2a; LIVE_BUVID=AUTO4417299433676539; PVID=2; SESSDATA=ccf84baf%2C1747890518%2C72b7c%2Ab1CjAZL_G-5mnbS4dvknpKQ-hzSZ_EYiDe7yhcvr8S1IKU3FOUiqN1Eivt-jFXlq4bdmESVkgwUjVPelIyblE2N2lnOE1JTC1XYzlDOUI2RXZ6dXFJd3dmLTdWaU52REpDWEphUXJPTzRZZDlvcm1LdUJWX2ZpbW8yOGNUZTNlZHZDeDNtalpqejdBIIEC; bili_jct=64fe0b1f1d387e0e490a6d65239b9948; DedeUserID=38921801; DedeUserID__ckMd5=b1bdb63ebdbbfd3c; bp_t_offset_38921801=1002889277526245376; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzI2MTg1ODQsImlhdCI6MTczMjM1OTMyNCwicGx0IjotMX0.bUbzAeyU2GW7sdRTJHpz_6Rv_3wCQDhUo_9gVPyxGAY; bili_ticket_expires=1732618524; b_lsid=B24102724_1935C221F69; match_float_version=ENABLE; sid=o2ky4vnz; browser_resolution=1507-992",
  "accept-language": "en,zh-CN;q=0.9,zh;q=0.8",
  "Referer": "https://space.bilibili.com/401742377/video?pn=1"
}

async def fetch(session: aiohttp.ClientSession, url: str) -> str:
  async with session.get(url) as response:
    return await response.text()

async def main():
  video_id = "113521522121449"
  async with aiohttp.ClientSession(headers=HEADERS) as session:
    response = await api.fetch_reply(session, video_id, pn=1)
    with open("./res.json", "w", encoding="UTF-8") as f:
      f.write(str(response))

async def get_tag(aid: int):
  async with aiohttp.ClientSession(headers=HEADERS) as session:
    response = await api.fetch_tags(session, aid=aid)
    with open("./res.json", "w", encoding="UTF-8") as f:
      f.write(str(response))

async def get_video_info(aid: int):
  async with aiohttp.ClientSession(headers=HEADERS) as session:
    response = await api.fetch_video_info(session, aid=aid)
    with open("./res.json", "w", encoding="UTF-8") as f:
      f.write(str(response))

async def get_user_videos(mid: int):
  async with aiohttp.ClientSession(headers=HEADERS) as session:
    response = await api.fetch_user_videos(session, mid, pn=18)
    with open("./res.json", "w", encoding="utf-8") as f:
      f.write(str(response))

async def get_comments(oid: int, page: int):
  async with aiohttp.ClientSession(headers=HEADERS) as session:
    response = await api.fetch_reply_wbi(session, oid, page)
    with open("./res.json", "w", encoding="utf-8") as f:
      f.write(str(response))

asyncio.run(get_video_info(113503704848440))