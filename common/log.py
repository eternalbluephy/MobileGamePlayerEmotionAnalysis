import logging
from rich.logging import RichHandler
from pathlib import Path

loggers: dict[str, logging.Logger] = {}
LOGGING_PATH = Path(__file__).parent.parent.joinpath("cache").joinpath("logs")
LOGGING_PATH.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "App", level: int = logging.INFO, file: bool = True, console: bool = True):
  """
  获取指定名称的logger，若不存在，则创建。
  Args:
    name(str): logger名称
    level(int): 创建logger的等级。只在创建时有效。
    file(bool): 是否输出到文件。只在创建时有效。
    console(bool): 是否输出到控制台。只在创建时有效。
  """
  if name not in loggers:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if file:
      formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
      handler = logging.FileHandler(str(LOGGING_PATH.joinpath(f"{name}.log")), encoding="utf-8")
      handler.setLevel(level)
      handler.setFormatter(formatter)
      logger.addHandler(handler)
    if console:
      formatter = logging.Formatter(
        "%(name)s - %(message)s",
        datefmt="%H:%M:%S"
      )
      handler = RichHandler()
      handler.setLevel(level)
      handler.setFormatter(formatter)
      logger.addHandler(handler)
    loggers[name] = logger
  return loggers[name]