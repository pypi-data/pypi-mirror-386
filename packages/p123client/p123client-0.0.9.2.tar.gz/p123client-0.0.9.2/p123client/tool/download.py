#!/usr/bin/env python3
# encoding: utf-8

__author__ = "ChenyangGao <https://chenyanggao.github.io>"
__all__ = ["make_uri", "get_downurl"]

import errno

from collections.abc import Coroutine

from typing import Literal
from typing import overload, Any, Literal
from urllib.parse import unquote

from encode_uri import encode_uri_component_loose
from iterutils import run_gen_step
from p123client import check_response, P123Client


@overload
def make_uri(
    client: P123Client, 
    file_id: int, 
    ensure_ascii: bool = False, 
    *, 
    async_: Literal[False] = False, 
    **request_kwargs, 
) -> str:
    ...
@overload
def make_uri(
    client: P123Client, 
    file_id: int, 
    ensure_ascii: bool = False, 
    *, 
    async_: Literal[True], 
    **request_kwargs, 
) -> Coroutine[Any, Any, str]:
    ...
def make_uri(
    client: P123Client, 
    file_id: int, 
    ensure_ascii: bool = False, 
    *, 
    async_: Literal[False, True] = False, 
    **request_kwargs, 
) -> str | Coroutine[Any, Any, str]:
    """创建自定义 uri，格式为 f"123://{name}|{size}|{md5}?{s3_key_flag}"

    :param client: 123 网盘的客户端对象
    :param file_id: 文件 id
    :param ensure_ascii: 是否要求全部字符在 ASCII 范围内
    :param async_: 是否异步
    :param request_kwargs: 其它请求参数

    :return: 自定义 uri
    """
    def gen_step():
        resp = yield client.fs_info(file_id, async_=async_, **request_kwargs)
        check_response(resp)
        resp["payload"] = file_id
        info_list = resp["data"]["infoList"]
        if not info_list:
            raise FileNotFoundError(errno.ENOENT, resp)
        info = info_list[0]
        if info["Type"]:
            raise IsADirectoryError(errno.EISDIR, resp)
        md5 = info["Etag"]
        name = encode_uri_component_loose(info["FileName"], ensure_ascii=ensure_ascii, quote_slash=False)
        size = info["Size"]
        s3_key_flag = info["S3KeyFlag"]
        return f"123://{name}|{size}|{md5}?{s3_key_flag}"
    return run_gen_step(gen_step, async_)


@overload
def get_downurl(
    client: P123Client, 
    uri: int | str, 
    quoted: bool = True, 
    *, 
    async_: Literal[False] = False, 
    **request_kwargs, 
) -> str:
    ...
@overload
def get_downurl(
    client: P123Client, 
    uri: int | str, 
    quoted: bool = True, 
    *, 
    async_: Literal[True], 
    **request_kwargs, 
) -> Coroutine[Any, Any, str]:
    ...
def get_downurl(
    client: P123Client, 
    uri: int | str, 
    quoted: bool = True, 
    *, 
    async_: Literal[False, True] = False, 
    **request_kwargs, 
) -> str | Coroutine[Any, Any, str]:
    """获取下载链接

    :param client: 123 网盘的客户端对象
    :param uri: 如果是 int，则视为文件 id（必须存在你网盘）；如果是 str，则视为自定义链接

        .. note::
            自定义链接的格式为 f"123://{name}|{size}|{md5}?{s3_key_flag}"，前面的 "123://" 和后面的 "?{s3_key_flag}" 都可省略

            如果省略 "?{s3_key_flag}"，则会尝试先秒传到你的网盘的 "/我的秒传" 目录下，名字为 f"{md5}-{size}" 的文件，然后再获取下载链接
    :param quoted: 说明链接已经过 quote 处理，所以使用时需要 unquote 回来
    :param async_: 是否异步
    :param request_kwargs: 其它请求参数

    :return: 下载链接
    """
    def gen_step():
        nonlocal uri
        if isinstance(uri, int):
            payload: int | dict = uri
        else:
            uri, _, s3_key_flag = uri.removeprefix("123://").rpartition("?")
            if not uri:
                uri, s3_key_flag = s3_key_flag, uri
            if quoted:
                uri = unquote(uri)
            name, size_s, md5 = uri.rsplit("|", 2)
            size = int(size_s)
            if s3_key_flag:
                payload = {
                    "FileName": name, 
                    "Etag": md5, 
                    "Size": size, 
                    "S3KeyFlag": s3_key_flag, 
                }
            else:
                resp = yield client.upload_file_fast(
                    file_name=".tempfile", 
                    file_md5=md5, 
                    file_size=size, 
                    duplicate=2, 
                    async_=async_, 
                    **request_kwargs, 
                )
                check_response(resp)
                payload = resp["data"]["Info"]
        resp = yield client.download_info(payload, async_=async_, **request_kwargs)
        check_response(resp)
        return resp["data"]["DownloadUrl"]
    return run_gen_step(gen_step, async_)

