import atexit
import json
import logging
import queue
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import httpx

Log = Tuple[Dict[str, str], str, str]


class LokiHandler(logging.Handler):
    def __init__(
        self,
        url: str,
        labels: Optional[Dict[str, str]] = None,
        batch_size: int = 100,
        flush_interval: float = 2.0,
    ):
        super().__init__()
        self.url = url
        self.labels_ = labels or {}
        self.temp_labels = {}
        self.batch_size: int = batch_size
        self.flush_interval: float = flush_interval
        self.queue: queue.Queue[Log] = queue.Queue()
        self._stop_event: threading.Event = threading.Event()
        self.worker: threading.Thread = threading.Thread(
            target=self._worker_loop, daemon=True
        )
        self.worker.start()

    def emit(self, record: logging.LogRecord) -> None:
        extra = getattr(record, "labels", {})
        ts_nanoseconds = str(int(time.time() * 1e9))
        msg = self.format(record)
        labels: Dict[str, str] = {
            **self.labels_,
            **self.temp_labels,
            "severity": record.levelname.lower(),
            "logger": record.name,
            **extra,
        }
        self.queue.put_nowait((labels, ts_nanoseconds, msg))

    def _worker_loop(self) -> None:
        buffer: List[Log] = []
        last_flush: float = time.time()
        atexit.register(self._flush, buffer)
        while True:
            try:
                item = self.queue.get(timeout=0.5)
                buffer.append(item)
            except queue.Empty:
                pass

            if (len(buffer) >= self.batch_size) or (
                time.time() - last_flush >= self.flush_interval
            ):
                if buffer:
                    self._flush(buffer)
                    buffer.clear()
                    last_flush = time.time()

    def _flush(self, batch: List[Log]) -> None:
        if not batch:
            return

        # Group by identical labels to form streams
        streams: Dict[str, Dict[str, Any]] = {}
        grouped: Dict[str, List[List[str]]] = defaultdict(list)
        for labels, ts, msg in batch:
            key = json.dumps(labels, sort_keys=True)
            grouped[key].append([ts, msg])
            if key not in streams:
                streams[key] = {"stream": labels, "values": []}

        for key, values in grouped.items():
            streams[key]["values"].extend(values)

        payload = {"streams": list(streams.values())}
        try:
            httpx.post(
                self.url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=2,
            )
        except httpx.HTTPError:
            pass  # Silent on failure

    @contextmanager
    def labels(self, labels: Dict[str, str]):
        """Temporarily set a Loki label for the duration of a block."""
        self.temp_labels = labels
        try:
            yield
        finally:
            self.temp_labels = {}
