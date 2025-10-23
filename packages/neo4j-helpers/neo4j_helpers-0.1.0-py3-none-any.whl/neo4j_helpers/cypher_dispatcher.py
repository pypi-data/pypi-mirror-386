"""Thread-based dispatcher for running Cypher queries concurrently.

Example
-------

```python
from neo4j_helpers import Neo4jInfo, CypherDispatcher

neo_info = Neo4jInfo.GetDefaultLocalHost()

with CypherDispatcher(neo_info, "CREATE (:Person {name: $name})") as dispatcher:
    for name in ["Ada", "Grace", "Linus"]:
        dispatcher.submit({"name": name})

dispatcher.close()  # optional when using the context manager
```

The dispatcher spins up a worker pool that will reuse the connections it opens,
so the `submit` calls only need to provide the Cypher parameters. Once the queue
is drained, `close()` (or exiting the context manager) waits for the threads to
finish and releases their driver resources.
"""

from __future__ import annotations

import threading
import time
from queue import Empty, Queue
from typing import Any, Callable, Optional, TYPE_CHECKING

from neo4j import GraphDatabase, Result

if TYPE_CHECKING:  # pragma: no cover
    from . import Neo4jInfo


_WorkItem = tuple[dict[str, Any], Optional[Callable[[Result], Any]], int]
_ErrorHandler = Optional[Callable[[Exception, dict[str, Any]], Any]]


class CypherDispatcher:
    """Concurrent worker pool that executes a Cypher query for queued work items."""

    def __init__(
        self,
        neo4j_info: "Neo4jInfo",
        query: str,
        *,
        workers: int = 8,
        queue_maxsize: int = 0,
        result_handler: Optional[Callable[[Result], Any]] = None,
        error_handler: _ErrorHandler = None,
        max_retries: Optional[int] = None,
    ) -> None:
        if workers < 1:
            raise ValueError("workers must be >= 1")
        if max_retries is not None and max_retries < 0:
            raise ValueError("max_retries must be >= 0 or None for unlimited retries")

        self._neo4j_info = neo4j_info
        self._query = query
        self._default_handler = result_handler
        self._error_handler = error_handler
        self._workers = workers
        self._max_retries = max_retries

        if queue_maxsize == 0:
            queue_maxsize = workers * 2
        self._queue: "Queue[_WorkItem | object]" = Queue(maxsize=queue_maxsize)
        self._threads: list[threading.Thread] = []
        self._sentinel: object = object()
        self._started = False
        self._closed = False
        self._start_lock = threading.Lock()
        self._errors: list[Exception] = []
        self._errors_lock = threading.Lock()
        self._abort_event = threading.Event()
        self._sentinel_push_lock = threading.Lock()
        self._sentinels_enqueued = 0

        self._driver = GraphDatabase.driver(
            neo4j_info.uri,
            auth=neo4j_info.auth,
        )

    def __enter__(self) -> "CypherDispatcher":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start(self) -> None:
        """Launch worker threads if they have not been started yet."""
        with self._start_lock:
            if self._started:
                return
            if self._closed:
                raise RuntimeError("Dispatcher is already closed")
            self._started = True
        for index in range(self._workers):
            thread = threading.Thread(
                target=self._worker,
                name=f"CypherDispatcher-{index + 1}",
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)

    def submit(
        self,
        parameters: Optional[dict[str, Any]] = None,
        *,
        result_handler: Optional[Callable[[Result], Any]] = None,
    ) -> None:
        """Queue a new work item for execution."""

        if self._closed or self._abort_event.is_set():
            raise RuntimeError("Dispatcher is closed")

        if not self._started:
            self.start()

        item: _WorkItem = (parameters or {}, result_handler or self._default_handler, 0)
        self._queue.put(item)

    def close(self, *, wait: bool = True) -> None:
        """Signal shutdown and optionally wait for workers to finish outstanding work."""
        if self._closed:
            return

        self._closed = True

        if wait and not self._abort_event.is_set():
            self._queue.join()

        # Release workers by feeding sentinel tasks.
        self._signal_stop_workers()

        if wait:
            for thread in self._threads:
                thread.join()

        self._threads.clear()
        self._driver.close()

    def wait_for_idle(self) -> None:
        """Block until the queue has been processed by all workers."""

        self._queue.join()

    def errors(self) -> list[Exception]:
        """Return a snapshot of exceptions raised during processing."""

        with self._errors_lock:
            return list(self._errors)

    def _worker(self) -> None:
        driver = self._driver
        database = self._neo4j_info.database

        while True:
            item = self._queue.get()
            try:
                if item is self._sentinel:
                    return

                if self._abort_event.is_set():
                    continue

                params, handler, attempt = item  # type: ignore[assignment]

                while True:
                    try:
                        with driver.session(database=database) as session:
                            result = session.run(self._query, params)
                            if handler is not None:
                                handler(result)
                            else:
                                result.consume()
                        break
                    except Exception as exc:  # pragma: no cover - requires live DB failure
                        if self._handle_error(exc, params, handler, attempt):
                            attempt += 1
                            continue
                        break
            finally:
                self._queue.task_done()

    def _handle_error(
        self,
        exc: Exception,
        params: dict[str, Any],
        handler: Optional[Callable[[Result], Any]],
        attempt: int,
    ) -> bool:
        """Handle a worker exception.

        Returns ``True`` when the worker should retry the same payload, ``False``
        when processing should stop.
        """

        is_transient = getattr(exc, "code", "").startswith("Neo.TransientError")
        should_retry = (
            is_transient
            and (self._max_retries is None or attempt < self._max_retries)
            and not self._abort_event.is_set()
            and not self._closed
        )
        if should_retry:
            if self._error_handler is not None:
                self._error_handler(exc, params)
            # brief pause to avoid immediate lock contention on retry
            time.sleep(0.01)
            return True

        if self._error_handler is not None:
            self._error_handler(exc, params)
        else:
            with self._errors_lock:
                self._errors.append(exc)

        self._abort_event.set()
        self._drain_queue()
        self._signal_stop_workers()
        return False

    def _signal_stop_workers(self) -> None:
        with self._sentinel_push_lock:
            remaining = self._workers - self._sentinels_enqueued
            if remaining <= 0:
                return
            for _ in range(remaining):
                self._queue.put(self._sentinel)
            self._sentinels_enqueued = self._workers

    def _drain_queue(self) -> None:
        while True:
            try:
                pending = self._queue.get_nowait()
            except Empty:
                break
            else:
                self._queue.task_done()
