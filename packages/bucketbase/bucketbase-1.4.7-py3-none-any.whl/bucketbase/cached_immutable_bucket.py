import io
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable, Union

from pyxtension import validate
from streamerate import slist

from bucketbase.errors import DeleteError
from bucketbase.fs_bucket import AppendOnlyFSBucket
from bucketbase.ibucket import (
    AbstractAppendOnlySynchronizedBucket,
    IBucket,
    ObjectStream,
    ShallowListing,
)


class CachedImmutableBucket(IBucket):
    def __init__(self, cache: AbstractAppendOnlySynchronizedBucket, main: IBucket) -> None:
        validate(isinstance(cache, AbstractAppendOnlySynchronizedBucket), "cache must be an AbstractAppendOnlySynchronizedBucket", exc=TypeError)
        validate(isinstance(main, IBucket), "main must be an IBucket", exc=TypeError)
        self._cache = cache
        self._main = main

    def get_object(self, name: PurePosixPath | str) -> bytes:
        """
        Note: At the first sight it would seem that concurrent calls to get_object may lead to multiple simultaneous calls to put_from_bucket,
            causing redundant fetches from the main bucket. But the put_from_bucket is synchronized, so only one thread will actually fetch the object from the main bucket,
            and all the concurrent threads will wait for the first thread to complete the PUT operation, and would throw FileExistsError,
            after which it's clear that the object is already in the cache.
        """
        name_str = str(name)
        try:
            return self._cache.get_object(name)
        except FileNotFoundError:
            try:
                self._cache.put_from_bucket(name, src_bucket=self._main, src_name=name_str)
            except FileExistsError:
                pass
            return self._cache.get_object(name)

    def get_object_stream(self, name: PurePosixPath | str) -> ObjectStream:
        """
        Note: read the note in `get_object()` for the explanation of the synchronization.
        """
        name_str = str(name)
        try:
            return self._cache.get_object_stream(name)
        except FileNotFoundError:
            try:
                self._cache.put_from_bucket(name, src_bucket=self._main, src_name=name_str)
            except FileExistsError:
                pass
            return self._cache.get_object_stream(name)

    def put_object(self, name: PurePosixPath | str, content: Union[str, bytes, bytearray]) -> None:
        raise io.UnsupportedOperation("put_object is not supported for CachedImmutableMinioObjectStorage")

    def put_object_stream(self, name: PurePosixPath | str, stream: BinaryIO) -> None:
        raise io.UnsupportedOperation("put_object_stream is not supported for CachedImmutableMinioObjectStorage")

    def list_objects(self, prefix: PurePosixPath | str = "") -> slist[PurePosixPath]:
        return self._main.list_objects(prefix)

    def shallow_list_objects(self, prefix: PurePosixPath | str = "") -> ShallowListing:
        return self._main.shallow_list_objects(prefix)

    def exists(self, name: PurePosixPath | str) -> bool:
        return self._cache.exists(name) or self._main.exists(name)

    def remove_objects(self, names: Iterable[PurePosixPath | str]) -> slist[DeleteError]:
        raise io.UnsupportedOperation("remove_objects is not supported for CachedImmutableMinioObjectStorage")

    @classmethod
    def build_from_fs(cls, cache_root: Path, main: IBucket) -> "CachedImmutableBucket":
        cache_bucket = AppendOnlyFSBucket.build(cache_root)
        return CachedImmutableBucket(cache=cache_bucket, main=main)

    def get_size(self, name: PurePosixPath | str) -> int:
        try:
            return self._cache.get_size(name)
        except FileNotFoundError:
            return self._main.get_size(name)

    @contextmanager
    def open_write(self, name: PurePosixPath | str) -> AbstractContextManager[BinaryIO]:
        """
        Returns a writable sink that delegates to the main bucket.
        Since this is an immutable bucket, writes go directly to the main bucket.
        """
        raise io.UnsupportedOperation("open_write is not supported for CachedImmutableBucket")
