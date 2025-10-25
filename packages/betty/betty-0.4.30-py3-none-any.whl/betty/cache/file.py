"""
Provide caching that persists cache items to files.
"""

from __future__ import annotations

import asyncio
import shutil
from abc import abstractmethod
from contextlib import AbstractAsyncContextManager, suppress
from functools import partial
from os import utime
from pickle import dumps, loads
from typing import (
    TYPE_CHECKING,
    Generic,
    Literal,
    Self,
    TypeVar,
    final,
    overload,
)

import aiofiles
from aiofiles.ospath import getmtime
from typing_extensions import override

from betty.cache import CacheItem, CacheItemValueSetter
from betty.cache._base import _CommonCacheBase, _CommonCacheBaseState
from betty.hashid import hashid
from betty.typing import processsafe

if TYPE_CHECKING:
    from collections.abc import Sequence
    from multiprocessing.managers import SyncManager
    from pathlib import Path

_CacheItemValueCoT = TypeVar("_CacheItemValueCoT", covariant=True)
_CacheItemValueContraT = TypeVar("_CacheItemValueContraT", contravariant=True)


class _FileCacheItem(CacheItem[_CacheItemValueCoT], Generic[_CacheItemValueCoT]):
    __slots__ = "_modified", "_path"

    def __init__(
        self,
        modified: int | float,
        path: Path,
    ):
        self._modified = modified
        self._path = path

    @override
    @property
    def modified(self) -> int | float:
        return self._modified

    @override
    async def value(self) -> _CacheItemValueCoT:
        async with aiofiles.open(self._path, "rb") as f:
            value_bytes = await f.read()
        return await self._load_value(value_bytes)

    @abstractmethod
    async def _load_value(self, value_bytes: bytes) -> _CacheItemValueCoT:
        pass


@final
class _PickledFileCacheItem(
    _FileCacheItem[_CacheItemValueCoT], Generic[_CacheItemValueCoT]
):
    @override
    async def _load_value(self, value_bytes: bytes) -> _CacheItemValueCoT:
        return loads(value_bytes)  # type: ignore[no-any-return]


@final
class _BinaryFileCacheItem(_FileCacheItem[bytes]):
    @override
    async def _load_value(self, value_bytes: bytes) -> bytes:
        return value_bytes


class _FileCache(
    _CommonCacheBase[_CacheItemValueContraT], Generic[_CacheItemValueContraT]
):
    """
    Provide a cache that persists cache items on a file system.
    """

    _cache_item_cls: type[_FileCacheItem[_CacheItemValueContraT]]

    def __init__(
        self,
        cache_directory_path: Path,
        *,
        scopes: Sequence[str] | None = None,
        manager: SyncManager | _CommonCacheBaseState[Self] | None = None,
    ):
        super().__init__(scopes=scopes, manager=manager)
        self._root_path = cache_directory_path

    @override
    def with_scope(self, scope: str) -> Self:
        return type(self)(
            self._root_path,
            scopes=(*self._scopes, scope),
            manager=_CommonCacheBaseState(
                self._cache_lock, self._cache_item_lock_ledger
            ),
        )

    def _cache_item_file_path(
        self, cache_item_id: str, suffix: str | None = None
    ) -> Path:
        cache_item_file_path = self._path / hashid(cache_item_id)
        if suffix is not None:
            assert suffix.startswith(".")
            cache_item_file_path = cache_item_file_path.parent / (
                cache_item_file_path.name + suffix
            )
        return cache_item_file_path

    @abstractmethod
    def _dump_value(self, value: _CacheItemValueContraT) -> bytes:
        pass

    @override
    async def _get(
        self, cache_item_id: str, *, suffix: str | None = None
    ) -> CacheItem[_CacheItemValueContraT] | None:
        try:
            cache_item_file_path = self._cache_item_file_path(cache_item_id, suffix)
            return self._cache_item_cls(
                await getmtime(cache_item_file_path),
                cache_item_file_path,
            )
        except OSError:
            return None

    @override
    async def _set(
        self,
        cache_item_id: str,
        value: _CacheItemValueContraT,
        *,
        suffix: str | None = None,
        modified: int | float | None = None,
    ) -> None:
        value = self._dump_value(value)
        cache_item_file_path = self._cache_item_file_path(cache_item_id, suffix)
        try:
            await self._write(cache_item_file_path, value, modified)
        except FileNotFoundError:
            await aiofiles.os.makedirs(cache_item_file_path.parent, exist_ok=True)
            await self._write(cache_item_file_path, value, modified)

    async def _write(
        self,
        cache_item_file_path: Path,
        value: bytes,
        modified: int | float | None = None,
    ) -> None:
        async with aiofiles.open(cache_item_file_path, "wb") as f:
            await f.write(value)
        if modified is not None:
            await asyncio.to_thread(utime, cache_item_file_path, (modified, modified))

    @override
    async def _delete(self, cache_item_id: str, *, suffix: str | None = None) -> None:
        with suppress(FileNotFoundError):
            await aiofiles.os.remove(self._cache_item_file_path(cache_item_id, suffix))

    @override
    async def _clear(self) -> None:
        with suppress(FileNotFoundError):
            await asyncio.to_thread(shutil.rmtree, self._path)

    @property
    def _path(self) -> Path:
        return self._root_path.joinpath(*self._scopes)

    @overload
    def getset(
        self, cache_item_id: str, *, suffix: str | None = None
    ) -> AbstractAsyncContextManager[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT],
        ]
    ]:
        pass

    @overload
    def getset(
        self,
        cache_item_id: str,
        *,
        suffix: str | None = None,
        wait: Literal[False] = False,
    ) -> AbstractAsyncContextManager[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT] | None,
        ]
    ]:
        pass

    @override
    def getset(
        self, cache_item_id: str, *, suffix: str | None = None, wait: bool = True
    ) -> AbstractAsyncContextManager[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT] | None,
        ]
    ]:
        return self._getset(
            cache_item_id,
            partial(self._get, suffix=suffix),
            partial(self._set, suffix=suffix),
            wait=wait,
        )


@final
@processsafe
class PickledFileCache(
    _FileCache[_CacheItemValueContraT], Generic[_CacheItemValueContraT]
):
    """
    Provide a cache that pickles values and persists them to files.
    """

    _cache_item_cls = _PickledFileCacheItem

    @override
    def _dump_value(self, value: _CacheItemValueContraT) -> bytes:
        return dumps(value)


@final
@processsafe
class BinaryFileCache(_FileCache[bytes]):
    """
    Provide a cache that persists bytes values to binary files.
    """

    _cache_item_cls = _BinaryFileCacheItem

    @override
    def _dump_value(self, value: bytes) -> bytes:
        return value

    @property
    def path(self) -> Path:
        """
        The path to the cache's root directory.
        """
        return self._path

    def cache_item_file_path(
        self, cache_item_id: str, suffix: str | None = None
    ) -> Path:
        """
        Get the file path for a cache item with the given ID.

        The cache item itself may or may not exist.
        """
        return self._cache_item_file_path(cache_item_id, suffix)
