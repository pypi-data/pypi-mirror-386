# -*- coding: utf-8 -*-
"""艺术家 - Artist APIs"""
from typing import Union
from . import WeapiCryptoRequest


@WeapiCryptoRequest
def GetArtistAlbums(artist_id: Union[str, int], offset=0, total=True, limit=1000):
    """网页端 - 获取艺术家所有专辑

    Args:
        artist_id (str, int): 艺术家ID
        offset (str, int, optional): 获取偏移数. Defaults to 0.
        total (bool, optional): 是否获取全部内容. Defaults to True.
        limit (str, int, optional): 单次获取量. Defaults to 30.

    Returns:
        dict
    """
    return f"/weapi/artist/albums/{artist_id}", {
        "offset": str(offset),
        "total": str(total).lower(),
        "limit": str(limit),
    }


@WeapiCryptoRequest
def GetArtistTracks(artist_id: Union[str, int], offset=0, total=True, limit=1000, order="hot"):
    """网页端 - 以某排序方式获取艺术家所有歌曲

    Args:
        artist_id (str, int): 艺术家ID
        offset (str, int, optional): 获取偏移数. Defaults to 0.
        total (bool, optional): 是否获取全部内容. Defaults to True.
        limit (str, int, optional): 单次获取量. Defaults to 30.
        order (str, optional): 歌曲排序方式 (hot：热度最高在前/time：时间最新在前). Defaults to 'hot'.
    Returns:
        dict
    """
    return "/weapi/v1/artist/songs", {
        "id": str(artist_id),
        "offset": str(offset),
        "total": str(total).lower(),
        "limit": str(limit),
        "order": str(order),
    }


@WeapiCryptoRequest
def GetArtistDetails(artist_id: Union[str, int]):
    """网页端 - 获取艺术家详情

    Args:
        artist_id (str, int): 艺术家ID
    Returns:
        dict
    """
    return "/weapi/artist/head/info/get", {"id": str(artist_id)}
