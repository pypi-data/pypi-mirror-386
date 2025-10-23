from __future__ import annotations

import struct
from pathlib import Path

import pytest

from neo4j_helpers.vector_tools import BvecReader, IvecReader


def test_iter_vectors_streams_expected_vectors():
    reader = BvecReader(Path(__file__).resolve().parent.parent / "sample-dbs" / "sample.bvecs.gz")

    vectors_iter = reader.iter_vectors()
    vectors = [next(vectors_iter) for _ in range(2)]

    assert len(vectors) == 2
    assert len(vectors[0]) == 128
    assert vectors[0][:8] == [3, 9, 17, 78, 83, 15, 10, 8]
    assert vectors[1][:8] == [1, 2, 8, 31, 19, 3, 0, 0]


def test_iter_vectors_rejects_negative_limit():
    reader = BvecReader(Path(__file__).resolve().parent.parent / "sample-dbs" / "sample.bvecs.gz")

    with pytest.raises(ValueError):
        list(reader.iter_vectors(limit=-1))


def test_ivec_reader_streams_integer_vectors(tmp_path: Path):
    ivecs_path = tmp_path / "sample.ivecs"
    with ivecs_path.open("wb") as handle:
        handle.write(struct.pack("<i", 3))
        handle.write(struct.pack("<3i", 1, 2, 3))
        handle.write(struct.pack("<i", 2))
        handle.write(struct.pack("<2i", -4, 7))

    reader = IvecReader(ivecs_path)
    vectors = list(reader.iter_vectors())

    assert vectors == [[1, 2, 3], [-4, 7]]
