import httpx
import asyncio
import json
from typing import Optional

async def async_test(ip: Optional[str] = None, test_url: str = "https://www.baidu.com", timeout: Optional[int] = None) -> bool:
  headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
  }
  proxies = {
    "http://": ip,
    "https://": ip
  } if ip else None
  try:
    async with httpx.AsyncClient(headers=headers, proxies=proxies, verify=False) as client:
      response = await client.get(test_url)
      data = json.loads(response.text)
      return response.status_code == 200 and data["code"] == 0
  except:
    return False
    
  

if __name__ == "__main__":
  import asyncio
  print(asyncio.run(async_test("http://47.122.62.83:8443", "http://api.bilibili.com/x/v2/reply/reply?oid=712909579&type=1&root=3762650428&ps=10&pn=1")))