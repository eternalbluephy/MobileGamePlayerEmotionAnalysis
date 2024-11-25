from enum import IntEnum


class Sort(IntEnum):
  """评论排序"""
  ByTime = 0,
  ByLikes = 1,
  ByReplies = 2


class StatusCode(IntEnum):
  """响应code枚举"""
  Success = 0,
  Error = -400,
  NoPermit = -403,
  NoSuch = -404,
  Closed = 12002,
  Invalid = 12009,
  Invisible = 62002,
  Auditing = 62004,
  Private = 62012

STATUS_CODES = {
  0: "成功",
  -400: "请求错误",
  -403: "权限不足",
  -404: "无此项",
  12002: "评论区已关闭",
  12009: "评论主体的type不合法",
  62002: "稿件不可见",
  62004: "稿件审核中",
  62012: "仅UP自己可见"
}