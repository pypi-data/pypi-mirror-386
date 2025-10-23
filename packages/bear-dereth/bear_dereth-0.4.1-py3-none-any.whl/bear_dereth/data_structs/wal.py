"""A WAL( Write-Ahead Log) data structure implementation."""

from enum import StrEnum
from pathlib import Path
import queue
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING, Any, NamedTuple, Self

from lazy_bear import LazyLoader

from bear_dereth.data_structs.counter_class import Counter
from bear_dereth.files.text.file_handler import TextFileHandler
from bear_dereth.sentinels import EXIT_SIGNAL

if TYPE_CHECKING:
    import json
else:
    json = LazyLoader("json")


class Operation(StrEnum):
    """Enumeration of WAL operations."""

    START = "START"
    COMMIT = "COMMIT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    END = "END"


class WALRecord(NamedTuple):
    """A record in the Write-Ahead Log."""

    txid: int
    op: Operation
    data: dict[str, Any]

    def to_json(self) -> str:
        """Convert the WALRecord to a dictionary."""
        return json.dumps(
            {
                "txid": self.txid,
                "op": self.op.value,
                "data": self.data,
            },
            ensure_ascii=False,
        )

    def __str__(self) -> str:
        """String representation of the WALRecord."""
        return f"WALRecord(txid={self.txid}, op={self.op}, data={self.data})"

    def __repr__(self) -> str:
        """Official string representation of the WALRecord."""
        return self.__str__()


class WriteAheadLog[T = WALRecord]:
    """A simple Write-Ahead Log (WAL) implementation."""

    default_class: type = WALRecord

    def __init__(self, file: str | Path, record_t: type[T] = WALRecord) -> None:
        """Initialize the Write-Ahead Log."""
        self._log_queue: Queue = Queue()
        self._tx_counter: Counter = Counter(start=0)
        self._file: TextFileHandler = TextFileHandler(file, touch=True)
        self._thread: Thread | None = None
        self._running: bool = False
        self.default_class = record_t

    def add_op(self, op: Operation | str, data: dict[str, Any]) -> int:
        """Log an operation to the WAL.

        Args:
            op: The operation to log (Operation enum or string)
            data: The data associated with the operation

        Returns:
            The transaction ID assigned to the logged operation
        """
        try:
            tx_id: int = self._tx_counter.tick()
            if isinstance(op, str):
                op = Operation(op)
            record = WALRecord(txid=tx_id, op=op, data=data)
            self._log_queue.put(record)
            return tx_id
        except ValueError as e:
            raise ValueError(f"Invalid operation '{op}': {e}") from e

    def _write_record(self, record: WALRecord) -> None:
        """Write a single WAL record to the file.

        We use TextFileHandler.append(..., force=True) to ensure that
        each record is flushed to disk immediately.

        Args:
            record: The WALRecord to write
        """
        try:
            self._file.append(record.to_json(), force=True)
        except Exception as e:
            raise OSError(f"Failed to write WAL record {record}: {e}") from e

    def _loop(self) -> None:
        """Write log records to the file."""
        q: Queue = self._log_queue
        has_task_done: bool = hasattr(q, "task_done")
        while True:
            try:
                record: WALRecord = q.get()
                if record is EXIT_SIGNAL:
                    if has_task_done:
                        q.task_done()
                    break
                self._write_record(record)
                if has_task_done:
                    q.task_done()
            except queue.Empty:
                continue

    def start(self) -> None:
        """Start the WAL logging thread."""
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("WAL listener already started")

        self._thread = t = Thread(target=self._loop)
        t.daemon = True
        t.start()

    def stop(self) -> None:
        """Stop the listener."""
        if self._thread is not None:
            self.enqueue_sentinel()
            self._thread.join()
            self._thread = None

    def enqueue_sentinel(self) -> None:
        """Enqueue a sentinel object to stop thread."""
        self._log_queue.put(EXIT_SIGNAL)

    def __enter__(self) -> Self:
        """Enter the context manager."""
        self.start()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the context manager."""
        self.stop()


# if __name__ == "__main__":
#     with WriteAheadLog("wal.jsonl") as wal:
#         wal.add_op("INSERT", {"id": 1, "name": "Alice"})
#         wal.add_op("UPDATE", {"id": 1, "name": "Bob"})
#         wal.add_op("DELETE", {"id": 1})
