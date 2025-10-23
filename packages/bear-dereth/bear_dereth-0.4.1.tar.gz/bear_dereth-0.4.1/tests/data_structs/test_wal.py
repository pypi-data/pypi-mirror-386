from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003

import pytest

from bear_dereth.data_structs.wal import Operation, WALRecord, WriteAheadLog


def _load_wal_records(path: Path) -> list[dict[str, object]]:
    """Return decoded WAL entries from the backing file."""
    raw: str = path.read_text().strip()
    if not raw:
        return []
    return [json.loads(line) for line in raw.splitlines() if line]


def test_write_ahead_log_persists_operations(tmp_path: Path) -> None:
    wal_file: Path = tmp_path / "wal.log"

    with WriteAheadLog(wal_file) as wal:
        first_tx: int = wal.add_op(Operation.INSERT, {"id": 1, "name": "Alice"})
        second_tx: int = wal.add_op("UPDATE", {"id": 1, "name": "Bob"})
        third_tx: int = wal.add_op(Operation.DELETE, {"id": 2})

    records: list[dict[str, object]] = _load_wal_records(wal_file)
    assert [record["txid"] for record in records] == [first_tx, second_tx, third_tx]
    assert [record["op"] for record in records] == ["INSERT", "UPDATE", "DELETE"]
    assert records[0]["data"] == {"id": 1, "name": "Alice"}
    assert records[1]["data"] == {"id": 1, "name": "Bob"}
    assert records[2]["data"] == {"id": 2}
    assert first_tx == 1
    assert second_tx == 2
    assert third_tx == 3


def test_write_ahead_log_start_twice_raises(tmp_path: Path) -> None:
    """Starting an already started WAL raises."""
    wal_file: Path = tmp_path / "wal.log"
    wal: WriteAheadLog[WALRecord] = WriteAheadLog(wal_file)

    try:
        wal.start()
        with pytest.raises(RuntimeError, match="WAL listener already started"):
            wal.start()
    finally:
        wal.stop()
    assert wal._thread is None  # pyright: ignore[reportPrivateUsage]


def test_write_ahead_log_flushes_prestart_entries(tmp_path: Path) -> None:
    """Entries added before starting are flushed on start."""
    wal_file: Path = tmp_path / "wal.log"
    wal: WriteAheadLog[WALRecord] = WriteAheadLog(wal_file)
    first_tx: int = wal.add_op(Operation.START, {"state": "booting"})

    try:
        wal.start()
    finally:
        wal.stop()

    records: list[dict[str, object]] = _load_wal_records(wal_file)
    assert len(records) == 1
    assert records[0]["txid"] == first_tx
    assert records[0]["op"] == Operation.START.value
    assert records[0]["data"] == {"state": "booting"}
    assert wal._thread is None  # pyright: ignore[reportPrivateUsage]


def test_write_ahead_log_stop_is_idempotent(tmp_path: Path) -> None:
    """Stopping an already stopped WAL is a no-op."""
    wal_file: Path = tmp_path / "wal.log"
    wal: WriteAheadLog[WALRecord] = WriteAheadLog(wal_file)

    wal.stop()
    assert wal._thread is None  # pyright: ignore[reportPrivateUsage]

    wal.start()
    wal.stop()
    wal.stop()
    assert wal._thread is None  # pyright: ignore[reportPrivateUsage]


def test_write_ahead_log_rejects_unknown_operation(tmp_path: Path) -> None:
    wal_file: Path = tmp_path / "wal.log"
    wal: WriteAheadLog[WALRecord] = WriteAheadLog(wal_file)

    with pytest.raises(ValueError, match="NOPE"):
        wal.add_op("NOPE", {"id": 99})
