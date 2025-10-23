from __future__ import annotations

import gzip
import struct
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO
from contextlib import contextmanager


@contextmanager
def _open_binary(path: Path) -> Iterator[BinaryIO]:
    """Open a binary file, handling optional gzip compression."""
    if path.suffix == ".gz":
        handle = gzip.open(path, "rb")
    else:
        handle = path.open("rb")
    try:
        yield handle
    finally:
        handle.close()


class BvecReader:
    """Stream vectors from a .bvecs or .bvecs.gz file."""

    def __init__(self, path: str | Path):
        self._path = Path(path).expanduser()

    def iter_vectors(self, limit: int | None = None) -> Iterator[list[int]]:
        """Yield vectors, optionally up to ``limit``."""
        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")
        return self._iterate(limit)

    def _iterate(self, limit: int | None) -> Iterator[list[int]]:
        remaining = limit
        with _open_binary(self._path) as handle:
            while remaining is None or remaining > 0:
                raw_dim = handle.read(4)
                if not raw_dim:
                    break
                if len(raw_dim) != 4:
                    raise ValueError(f"incomplete dimension header in {self._path}")
                (dimension,) = struct.unpack("<i", raw_dim)
                vector_bytes = handle.read(dimension)
                if len(vector_bytes) != dimension:
                    raise ValueError(f"incomplete vector payload in {self._path}")
                yield list(vector_bytes)
                if remaining is not None:
                    remaining -= 1


class IvecReader:
    """Stream vectors from a .ivecs or .ivecs.gz file."""

    def __init__(self, path: str | Path):
        self._path = Path(path).expanduser()

    def iter_vectors(self, limit: int | None = None) -> Iterator[list[int]]:
        """Yield vectors of integers, optionally up to ``limit``."""
        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")
        return self._iterate(limit)

    def _iterate(self, limit: int | None) -> Iterator[list[int]]:
        remaining = limit
        with _open_binary(self._path) as handle:
            while remaining is None or remaining > 0:
                raw_dim = handle.read(4)
                if not raw_dim:
                    break
                if len(raw_dim) != 4:
                    raise ValueError(f"incomplete dimension header in {self._path}")
                (dimension,) = struct.unpack("<i", raw_dim)
                vector_bytes = handle.read(dimension * 4)
                if len(vector_bytes) != dimension * 4:
                    raise ValueError(f"incomplete vector payload in {self._path}")
                vector = list(struct.unpack(f"<{dimension}i", vector_bytes))
                yield vector
                if remaining is not None:
                    remaining -= 1


__all__ = ["BvecReader", "IvecReader"]
