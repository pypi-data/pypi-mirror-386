"""
WeSTL JSON representor. It just serializes run-time WeSTL to JSON. The WeSTL spec is at
http://rwcbook.github.io/wstl-spec/.
"""

import logging
from typing import Union
from .representor import Representor, Link
from aiohttp.web import Request
from typing import Any, Callable
from collections.abc import Callable, Iterable, Mapping
from heaobject.root import json_dumps


MIME_TYPE = 'application/vnd.wstl+json'


class WeSTLJSON(Representor):
    MIME_TYPE = MIME_TYPE

    async def formats(self, request: Request,
                      wstl_obj: Union[Iterable[Mapping[str, Any]], Mapping[str, Any]],
                      dumps=json_dumps,
                      link_callback: Callable[[int, Link], None] | None = None,
                      include_data=True) -> bytes:
        """
        Serializes a run-time WeSTL document to JSON.

        :param request: the HTTP request.
        :param wstl_obj: dict with run-time WeSTL JSON, or a list of run-time WeSTL JSON dicts.
        :param dumps: any callable that accepts dict with JSON and outputs str. Cannot be None.
        :param link_callback: ignored.
        :param include_data: ignored.
        :return: str containing run-time WeSTL collection JSON.
        :raises ValueError: if an error occurs formatting the WeSTL document.
        """
        logger = logging.getLogger()
        logger.debug('dumping %s', wstl_obj)
        return dumps(wstl_obj if not isinstance(wstl_obj, Mapping) else [wstl_obj]).encode('utf-8')

    async def parse(self, request: Request) -> dict[str, Any]:
        raise NotImplementedError


