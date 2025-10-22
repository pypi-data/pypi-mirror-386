from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import override

import redis.asyncio as redis
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from alxhttp.schemas import gen_prefixed_id


def cookie_expiry(dt: datetime) -> str:
  return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')


async def secure_hset(redis: redis.Redis, name: str, secure_value: str) -> str:
  """
  Using a hash map called {name} this stores the secure_value under a randomly named key
  which is returned. The main usecase is storing the random key in a browser cookie
  that the backend can later lookup to find teh real value.
  """
  cookie_value = gen_prefixed_id(f'{name}_', num_bytes=32)

  await redis.hset(name=name, key=cookie_value, value=secure_value.encode())  # pyright: ignore[reportGeneralTypeIssues, reportArgumentType]

  return cookie_value


async def secure_hget(redis: redis.Redis, name: str, cookie_value: str) -> str | None:
  """
  Using a hash map called {name} this retrieves the secure_value via the randomly named
  cookie value. The main usecase is storing the random key in a browser cookie
  that the backend can later lookup to find teh real value.
  """

  if not cookie_value.startswith(f'{name}_'):
    raise ValueError('cookie_value is malformed')

  res = await redis.hget(name=name, key=cookie_value)  # pyright: ignore[reportGeneralTypeIssues]

  return res.decode() if res else None  # pyright: ignore[reportAttributeAccessIssue]


@dataclass
class PlainCookie:
  """
  A cookie that JS can read
  """

  name: str
  expiry_delta: timedelta

  async def set(self, res: Response, cookie_value: str, expiry_delta: timedelta | None = None) -> None:
    if not expiry_delta:
      expiry_delta = self.expiry_delta

    expires = cookie_expiry(datetime.now(timezone.utc) + expiry_delta)

    res.set_cookie(str(self.name), cookie_value, secure=True, httponly=False, samesite='Lax', expires=expires)

  async def get(self, req: Request) -> str | None:
    return req.cookies.get(self.name)

  async def unset(self, res: Response) -> None:
    res.del_cookie(self.name)


@dataclass
class HiddenCookie(PlainCookie):
  """
  A cookie {name} that JS cannot read, along with a companion cookie {name}_is_set that JS can
  query to see if the hidden cookie is currently set.
  """

  @override
  async def set(self, res: Response, cookie_value: str, expiry_delta: timedelta | None = None) -> None:
    if not expiry_delta:
      expiry_delta = self.expiry_delta

    expires = cookie_expiry(datetime.now(timezone.utc) + expiry_delta)

    res.set_cookie(str(self.name), cookie_value, secure=True, httponly=True, samesite='Strict', expires=expires)
    res.set_cookie(f'{self.name}_is_set', '1', secure=True, httponly=False, samesite='Lax', expires=expires)

  @override
  async def get(self, req: Request) -> str | None:
    return req.cookies.get(self.name)

  @override
  async def unset(self, res: Response) -> None:
    res.del_cookie(self.name)
    res.del_cookie(f'{self.name}_is_set')


@dataclass
class RedisHiddenCookie(HiddenCookie):
  """
  A cookie {name} that JS cannot read, along with a companion cookie {name}_is_set that JS can
  query to see if the hidden cookie is currently set. The value of the hidden cookie is a random
  value that can be used by the backend to lookup a truly secret value.
  """

  @override
  async def set(self, res: Response, cookie_value: str, expiry_delta: timedelta | None = None, redis: redis.Redis | None = None) -> None:
    assert redis is not None
    cookie_value = await secure_hset(redis, self.name, cookie_value)

    await super().set(res, cookie_value, expiry_delta)

  @override
  async def get(self, req: Request, redis: redis.Redis | None = None) -> str | None:
    assert redis is not None
    cookie_value = req.cookies.get(self.name)

    if not cookie_value:
      return None

    return await secure_hget(redis, self.name, cookie_value)
