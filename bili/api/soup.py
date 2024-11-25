import aiohttp
from bs4 import BeautifulSoup

async def get_user_videos(session: aiohttp.ClientSession, mid: int, page: int) -> list[int]:
  async with session.get(f"https://space.bilibili.com/{mid}/video?pn={page}") as html:
    return await html.text(encoding="utf-8")


if __name__ == "__main__":
  import asyncio

  HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Cookie": "buvid3=045FFA68-F00D-9CD3-51BD-CC7EFF43B56C74211infoc; b_nut=1727859074; _uuid=4103EF1011-5BE1-EF93-291E-B48F17BBE1010474375infoc; header_theme_version=CLOSE; enable_web_push=DISABLE; home_feed_column=5; CURRENT_FNVAL=4048; rpdid=|(kJRYmJRmY|0J'u~k~)~)Rkl; buvid_fp_plain=undefined; buvid4=33D3C568-8110-0DA3-7F91-0EDEDD2FF65476357-024100208-EftFjGYzK8e%2BnmvtDmyFEYC8vC7CPXisBgZC93SEz739%2BeRPEAXBVPhLcxB9be7g; fingerprint=31aaa664aa47a99ff5c8dbfa3eae9a2a; buvid_fp=31aaa664aa47a99ff5c8dbfa3eae9a2a; LIVE_BUVID=AUTO4417299433676539; PVID=2; SESSDATA=ccf84baf%2C1747890518%2C72b7c%2Ab1CjAZL_G-5mnbS4dvknpKQ-hzSZ_EYiDe7yhcvr8S1IKU3FOUiqN1Eivt-jFXlq4bdmESVkgwUjVPelIyblE2N2lnOE1JTC1XYzlDOUI2RXZ6dXFJd3dmLTdWaU52REpDWEphUXJPTzRZZDlvcm1LdUJWX2ZpbW8yOGNUZTNlZHZDeDNtalpqejdBIIEC; bili_jct=64fe0b1f1d387e0e490a6d65239b9948; DedeUserID=38921801; DedeUserID__ckMd5=b1bdb63ebdbbfd3c; bp_t_offset_38921801=1002889277526245376; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzI2MTg1ODQsImlhdCI6MTczMjM1OTMyNCwicGx0IjotMX0.bUbzAeyU2GW7sdRTJHpz_6Rv_3wCQDhUo_9gVPyxGAY; bili_ticket_expires=1732618524; b_lsid=B24102724_1935C221F69; match_float_version=ENABLE; sid=o2ky4vnz; browser_resolution=1507-992"
  }

  async def test(mid: int, page: int):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
      return await get_user_videos(session, mid, page)
    
  with open("./res.html", "w", encoding="utf-8") as f:
    f.write(asyncio.run(test(401742377, 1)))