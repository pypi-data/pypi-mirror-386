import inspect
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, override

import asyncpg
import pglast  # pyright: ignore[reportMissingTypeStubs]
from typing_extensions import TypeVar

from alxhttp.file_watcher import register_file_listener
from alxhttp.pydantic.basemodel import BaseModel


def get_caller_dir(idx: int = 1) -> Path:
  current_frame = inspect.currentframe()

  while idx > 0 and current_frame:
    current_frame = current_frame.f_back
    idx -= 1

  if not current_frame:
    raise ValueError

  frame_info = inspect.getframeinfo(current_frame)
  return Path(os.path.dirname(os.path.abspath(frame_info.filename)))


ListType = TypeVar('ListType')


class SQLValidator[T: BaseModel]:
  def __init__(self, file: str | Path, cls: type[T], stack_offset: int = 2):
    super().__init__()
    self.file: Path = get_caller_dir(stack_offset) / file
    self._query: str | None = None
    self.cls: type[T] = cls

    if modified_recently(self.file):
      self.validate()
    register_file_listener(self.file, self.validate)

  @override
  def __str__(self) -> str:
    return self.query

  @property
  def query(self) -> str:
    if not self._query:
      self.validate()
      assert self._query

    return self._query

  def validate(self) -> None:
    self._query = validate_sql(self.file)

  async def fetchrow(self, conn: asyncpg.pool.PoolConnectionProxy, *args: Any) -> T:
    record = await conn.fetchrow(self.query, *args)
    return self.cls.from_record(record)

  async def fetch(self, conn: asyncpg.pool.PoolConnectionProxy, *args: Any) -> list[T]:
    records = await conn.fetch(self.query, *args)
    return [self.cls.from_record(record) for record in records]

  async def fetchlist[TT](self, list_type: type[TT], conn: asyncpg.pool.PoolConnectionProxy, *args: Any) -> list[TT]:
    records = await conn.fetch(self.query, *args)
    return [list_type(record[0]) for record in records]  # pyright: ignore[reportCallIssue]

  async def execute(self, conn: asyncpg.pool.PoolConnectionProxy, *args: Any) -> str:
    return await conn.execute(self.query, *args)


class SQLArgValidator[T: BaseModel, **P, PT](SQLValidator[T]):
  def __init__(self, file: str | Path, cls: type[T], argorder: Callable[P, PT], stack_offset: int = 3):
    super().__init__(file, cls, stack_offset=stack_offset)
    self.argorder: Callable[P, PT] = argorder

  def _get_query_args(self, *_args: Any, **kwargs: Any) -> list[Any]:
    """
    The kwargs could be in any order, so it's important that we re-order
    based on the defined field order from `argorder`

    This also gives a natural place to perform some type conversions
    """
    ordered = []
    for field_name in self.argorder.model_fields.keys():  # pyright: ignore[reportFunctionMemberAccess]
      arg = kwargs[field_name]
      if isinstance(arg, BaseModel):
        arg = arg.model_dump_json()
      elif isinstance(arg, dict):
        arg = json.dumps(arg)
      ordered.append(arg)
    return ordered

  @override
  async def fetchrow(self, conn: asyncpg.pool.PoolConnectionProxy, *args: P.args, **kwargs: P.kwargs) -> T:
    return await super().fetchrow(conn, *self._get_query_args(*args, **kwargs))

  @override
  async def fetch(self, conn: asyncpg.pool.PoolConnectionProxy, *args: P.args, **kwargs: P.kwargs) -> list[T]:
    return await super().fetch(conn, *self._get_query_args(*args, **kwargs))

  @override
  async def fetchlist[TT](self, list_type: type[TT], conn: asyncpg.pool.PoolConnectionProxy, *args: P.args, **kwargs: P.kwargs) -> list[TT]:
    return await super().fetchlist(list_type, conn, *self._get_query_args(*args, **kwargs))

  @override
  async def execute(self, conn: asyncpg.pool.PoolConnectionProxy, *args: P.args, **kwargs: P.kwargs) -> str:
    return await super().execute(conn, *self._get_query_args(*args, **kwargs))


def modified_recently(path: Path) -> bool:
  current_time = time.time()
  modification_time = os.path.getmtime(path)
  return (current_time - modification_time) <= 600


def validate_sql(sql_file: Path) -> str:
  with open(sql_file) as f:
    txt = f.read()

  try:
    pglast.parser.parse_sql(txt)
    print(f'validated {sql_file}')
    return txt
  except Exception as e:
    raise ValueError(f'Unable to parse {sql_file}') from e
