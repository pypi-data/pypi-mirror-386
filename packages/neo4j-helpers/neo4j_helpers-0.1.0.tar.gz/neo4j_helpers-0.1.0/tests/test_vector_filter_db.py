from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest


def load_vector_filter():
    module_path = Path(__file__).resolve().parent.parent / "sample-dbs" / "vector-filter.py"
    spec = importlib.util.spec_from_file_location("vector_filter", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load vector-filter module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_bvecs_path() -> Path:
    return Path(__file__).resolve().parent.parent / "sample-dbs" / "sample.bvecs.gz"


def test_vector_filter_read_bvecs_vectors_streams():
    module = load_vector_filter()
    vf = module.VectorFilterDB(neo4j_tools=None, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    iterator = vf.read_bvecs_vectors(_sample_bvecs_path())
    vectors = [next(iterator) for _ in range(2)]

    assert len(vectors) == 2
    assert len(vectors[0]) == 128
    assert vectors[0][:8] == [-125, -119, -111, -50, -45, -113, -118, -120]
    assert vectors[1][:8] == [-127, -126, -120, -97, -109, -125, -128, -128]


def test_vector_filter_read_bvecs_vectors_validates_limit():
    module = load_vector_filter()
    vf = module.VectorFilterDB(neo4j_tools=None, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        list(vf.read_bvecs_vectors(_sample_bvecs_path(), limit=-1))


def test_write_chunk_csv_writes_header_and_rows(tmp_path: Path):
    module = load_vector_filter()
    vf = module.VectorFilterDB(neo4j_tools=None, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    vf._write_chunk_csv(tmp_path, rows=2)

    output_path = tmp_path / "chunk.csv"
    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    assert rows[0] == module.CHUNK_HEADER
    assert rows[1][0] == "0"
    assert rows[2][0] == "1"
    assert rows[1][1].split(";")[0:8] == ["-125", "-119", "-111", "-50", "-45", "-113", "-118", "-120"]


def test_write_project_csv_uses_custom_bucket_distribution(tmp_path: Path):
    module = load_vector_filter()
    custom_buckets = [
        module.DistributionBucket("Alpha", 5, 1),
        module.DistributionBucket("Beta", 7, 2),
    ]
    vf = module.VectorFilterDB(
        neo4j_tools=None,
        sift_bvecsgz_path=str(_sample_bvecs_path()),
        project_buckets=custom_buckets,
    )  # type: ignore[arg-type]

    vf._write_project_csv(tmp_path, proj_count=5)

    output_path = tmp_path / "projects.csv"
    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    assert rows[0] == module.PROJECT_HEADER
    labels = [row[1] for row in rows[1:]]
    assert labels == ["Alpha", "Beta", "Beta", "Alpha", "Beta"]


def test_get_proj_count_uses_bucket_sizes():
    module = load_vector_filter()
    custom_buckets = [
        module.DistributionBucket("Alpha", 2, 1),
        module.DistributionBucket("Beta", 3, 1),
    ]
    vf = module.VectorFilterDB(
        neo4j_tools=None,
        sift_bvecsgz_path=str(_sample_bvecs_path()),
        project_buckets=custom_buckets,
    )  # type: ignore[arg-type]

    assert vf._get_proj_count(0) == 0
    assert vf._get_proj_count(5) == 2
    assert vf._get_proj_count(7) == 3


def test_validate_buckets_rejects_invalid_configurations():
    module = load_vector_filter()

    with pytest.raises(ValueError, match="project buckets must not be empty"):
        module._validate_buckets("project", [])

    with pytest.raises(ValueError, match="project bucket sizes must be positive"):
        module._validate_buckets("project", [module.DistributionBucket("Alpha", 0, 1)])

    with pytest.raises(ValueError, match="project bucket distributions must be positive"):
        module._validate_buckets("project", [module.DistributionBucket("Alpha", 1, 0)])


def test_write_author_csv_uses_bucket_distribution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = load_vector_filter()
    custom_author_buckets = (
        module.DistributionBucket("Alpha", 2, 1),
        module.DistributionBucket("Beta", 5, 2),
    )
    monkeypatch.setattr(module, "AUTHOR_BUCKETS", custom_author_buckets)
    vf = module.VectorFilterDB(neo4j_tools=None, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    vf._write_author_csv(tmp_path, author_count=5)

    output_path = tmp_path / "authors.csv"
    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    assert rows[0] == module.AUTHOR_HEADER
    labels = [row[1] for row in rows[1:]]
    assert labels == ["Alpha", "Beta", "Beta", "Alpha", "Beta"]


def test_get_author_count_uses_bucket_sizes(monkeypatch: pytest.MonkeyPatch):
    module = load_vector_filter()
    custom_author_buckets = (
        module.DistributionBucket("Alpha", 2, 1),
        module.DistributionBucket("Beta", 3, 1),
    )
    monkeypatch.setattr(module, "AUTHOR_BUCKETS", custom_author_buckets)
    vf = module.VectorFilterDB(neo4j_tools=None, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    assert vf._get_author_count(0) == 0
    assert vf._get_author_count(2) == 1
    assert vf._get_author_count(3) == 2
    assert vf._get_author_count(5) == 2


def test_write_document_csv_cycles_year_distribution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = load_vector_filter()
    monkeypatch.setattr(module, "YEAR_DISTRIBUTION", [1, 2])
    monkeypatch.setattr(module, "YEARS", [2000, 2001])
    vf = module.VectorFilterDB(neo4j_tools=None, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    vf._write_document_csv(tmp_path, doc_count=5)

    output_path = tmp_path / "documents.csv"
    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    assert rows[0] == module.DOCUMENT_HEADER
    years = [int(row[1]) for row in rows[1:]]
    assert years == [2000, 2001, 2001, 2000, 2001]


def test_write_chunk_rels_csv_assigns_documents(tmp_path: Path):
    module = load_vector_filter()
    vf = module.VectorFilterDB(neo4j_tools=None, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    vf._write_chunk_rels_csv(tmp_path, rows=12)

    output_path = tmp_path / "chunk_rels.csv"
    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    assert rows[0] == module.CHUNK_REL_HEADER
    data = [(int(row[0]), int(row[1])) for row in rows[1:]]
    assert data[:5] == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
    assert data[10:] == [(10, 1), (11, 1)]


def test_write_doc_proj_rels_respects_bucket_counts(tmp_path: Path):
    module = load_vector_filter()
    custom_buckets = [
        module.DistributionBucket("Alpha", 2, 1),
        module.DistributionBucket("Beta", 3, 1),
    ]
    vf = module.VectorFilterDB(
        neo4j_tools=None,
        sift_bvecsgz_path=str(_sample_bvecs_path()),
        project_buckets=custom_buckets,
    )  # type: ignore[arg-type]

    output_path = tmp_path / "doc_proj.csv"
    vf._write_doc_proj_rels(output_path, doc_count=5, proj_count=2)

    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    assert rows[0] == module.DOC_PROJ_REL_HEADER
    doc_ids = [int(row[0]) for row in rows[1:]]
    project_ids = [int(row[1]) for row in rows[1:]]
    expected_docs = list(module.coprime_progression(5, seed=2))
    assert doc_ids == expected_docs
    assert project_ids == [0, 0, 1, 1, 1]


def test_write_doc_author_rels_respects_bucket_counts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = load_vector_filter()
    custom_author_buckets = (
        module.DistributionBucket("Alpha", 2, 1),
        module.DistributionBucket("Beta", 1, 1),
    )
    monkeypatch.setattr(module, "AUTHOR_BUCKETS", custom_author_buckets)
    vf = module.VectorFilterDB(neo4j_tools=None, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    output_path = tmp_path / "doc_author.csv"
    vf._write_doc_author_rels(output_path, doc_count=4, author_count=3)

    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    assert rows[0] == module.DOC_AUTHOR_REL_HEADER
    doc_ids = [int(row[0]) for row in rows[1:]]
    author_ids = [int(row[1]) for row in rows[1:]]
    expected_docs = list(module.coprime_progression(4, seed=3))
    assert doc_ids == expected_docs
    assert author_ids == [0, 0, 1, 2]


def test_coprime_progression_with_seed_is_permutation():
    module = load_vector_filter()
    values = list(module.coprime_progression(10, seed=1))

    assert values == [2, 9, 6, 3, 0, 7, 4, 1, 8, 5]
    assert len(values) == 10
    assert sorted(values) == list(range(10))


def test_coprime_progression_with_explicit_step():
    module = load_vector_filter()
    values = list(module.coprime_progression(7, start=2, step=3))

    assert values == [2, 5, 1, 4, 0, 3, 6]


def test_coprime_progression_handles_single_value():
    module = load_vector_filter()
    assert list(module.coprime_progression(1)) == [0]


def test_run_offline_import_calls_run_admin(tmp_path: Path):
    module = load_vector_filter()

    class StubTools:
        def __init__(self, import_dir: Path):
            self.import_dir = import_dir
            self.calls: list[tuple[list[str], dict[str, object]]] = []

        def run_admin(self, args, **kwargs):
            self.calls.append((list(args), kwargs))
            logger = kwargs.get("logger")
            if logger:
                logger.log("[stdout] simulated output")

    class StubLogger:
        def __init__(self) -> None:
            self.messages: list[str] = []

        def log(self, message: str) -> None:
            self.messages.append(message)

    tools = StubTools(import_dir=tmp_path)
    logger = StubLogger()
    vf = module.VectorFilterDB(neo4j_tools=tools, sift_bvecsgz_path=str(_sample_bvecs_path()), logger=logger)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        vf.run_offline_import()

    vf.run_offline_import("database", "import", "--overwrite-destination=true")

    assert tools.calls == [
        (
            ["database", "import", "--overwrite-destination=true"],
            {"logger": logger, "capture_output": False},
        )
    ]
    assert logger.messages[0] == "Running neo4j-admin database import --overwrite-destination=true"
    assert "[stdout] simulated output" in logger.messages


def test_run_offline_import_raises_on_failure(tmp_path: Path):
    module = load_vector_filter()

    class StubTools:
        def __init__(self, import_dir: Path):
            self.import_dir = import_dir

        def run_admin(self, args, **kwargs):
            raise RuntimeError("neo4j-admin failed")

    tools = StubTools(import_dir=tmp_path)
    vf = module.VectorFilterDB(neo4j_tools=tools, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="neo4j-admin failed"):
        vf.run_offline_import("database", "import")


def test_run_offline_import_can_disable_streaming(tmp_path: Path):
    module = load_vector_filter()

    class StubTools:
        def __init__(self, import_dir: Path):
            self.import_dir = import_dir
            self.calls: list[tuple[list[str], dict[str, object]]] = []

        def run_admin(self, args, **kwargs):
            self.calls.append((list(args), kwargs))

    tools = StubTools(import_dir=tmp_path)
    vf = module.VectorFilterDB(neo4j_tools=tools, sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]

    vf.run_offline_import("database", "import", stream_output=False)

    assert tools.calls == [
        (
            ["database", "import"],
            {"logger": vf._logger, "capture_output": True},
        )
    ]


def test_is_running_delegates_to_tools():
    module = load_vector_filter()

    class StubTools:
        def is_running(self):
            return True

    vf = module.VectorFilterDB(neo4j_tools=StubTools(), sift_bvecsgz_path=str(_sample_bvecs_path()))  # type: ignore[arg-type]
    assert vf.is_running is True


def test_start_and_stop_server_delegate_to_tools():
    module = load_vector_filter()

    class StubTools:
        def __init__(self):
            self.calls: list[tuple[str, dict[str, object]]] = []

        def start_server(self, **kwargs):
            self.calls.append(("start", kwargs))

        def stop_server(self, **kwargs):
            self.calls.append(("stop", kwargs))

    tools = StubTools()
    logger = module.ConsoleLogger()
    vf = module.VectorFilterDB(neo4j_tools=tools, sift_bvecsgz_path=str(_sample_bvecs_path()), logger=logger)  # type: ignore[arg-type]

    vf.start_server(wait=True)
    vf.stop_server(wait=False)

    assert tools.calls == [
        ("start", {"wait": True, "timeout": 60.0, "poll_interval": 1.0, "logger": logger}),
        ("stop", {"wait": False, "timeout": 60.0, "poll_interval": 1.0, "logger": logger}),
    ]
