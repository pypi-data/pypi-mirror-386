from aiohttp.typedefs import Handler, PathLike
from aiohttp.web import FileResponse


def get_file(path: PathLike) -> Handler:
  async def handler(_) -> FileResponse:
    return FileResponse(path)

  return handler
