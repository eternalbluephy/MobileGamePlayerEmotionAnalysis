import yaml
import pathlib
import webbrowser
from time import sleep
from weibo import APIClient

SECRET_PATH = pathlib.Path(__file__).parent.joinpath("secret.yaml")

if not SECRET_PATH.exists:
  print("请先在weibo/secret.yaml中写入APP_KEY和APP_SECRET")
  exit(1)

with open(SECRET_PATH, "r", encoding="utf-8") as f:
  keys = yaml.safe_load(f)

if "APP_KEY" not in keys:
  print("secret.yaml缺失APP_KEY")
  exit(1)
if "APP_SECRET" not in keys:
  print("secret.yaml缺失APP_SECRET")
  exit(1)


APP_KEY = keys["APP_KEY"]
APP_SECRET = keys["APP_SECRET"]
CALLBACK_URL = "https://api.weibo.com/oauth2/default.html"
client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
print("请在接下来打开的浏览器窗口中授权后复制url中code的值")
sleep(1)
webbrowser.open_new(url=client.get_authorize_url())

code = input("请输入code：")
token = client.request_access_token(code)
print(f"access_token: {token}")

keys.update(token)
with open(SECRET_PATH, "w", encoding="utf-8") as f:
  yaml.dump(data=keys, stream=f, allow_unicode=True)
print(f"已写入到secret.yaml")