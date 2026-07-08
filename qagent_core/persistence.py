from __future__ import annotations

import os
import json
import sqlite3
import time
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

import pandas as pd


class ReviewPersistenceError(RuntimeError):
    """User-safe error raised when a review cannot be persisted."""


class DuplicateReviewError(ReviewPersistenceError):
    """Raised when review_id already exists."""


class SQLiteReviewRepository:
    """Small SQLite repository for single-host PoC HITL audit records."""

    JSON_FIELDS = (
        "tool_trace_json", "virtual_patch_json", "self_reflection_json", "artifact_json",
    )

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with closing(self._connect()) as connection, connection:
                connection.execute("PRAGMA journal_mode = WAL")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS hitl_reviews (
                        review_id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        model TEXT NOT NULL DEFAULT '',
                        target TEXT NOT NULL DEFAULT '',
                        decision TEXT NOT NULL DEFAULT '',
                        reviewer TEXT NOT NULL DEFAULT '',
                        reviewer_note TEXT NOT NULL DEFAULT '',
                        final_answer TEXT NOT NULL DEFAULT '',
                        tool_trace_json TEXT NOT NULL DEFAULT '[]',
                        virtual_patch_json TEXT NOT NULL DEFAULT '{}',
                        self_reflection_json TEXT NOT NULL DEFAULT '{}',
                        dataset_name TEXT NOT NULL DEFAULT '',
                        app_version TEXT NOT NULL DEFAULT '',
                        artifact_path TEXT NOT NULL DEFAULT '',
                        artifact_json TEXT NOT NULL DEFAULT '{}'
                    )
                    """
                )
                columns = {
                    str(row[1]) for row in connection.execute("PRAGMA table_info(hitl_reviews)")
                }
                if "artifact_json" not in columns:
                    connection.execute(
                        "ALTER TABLE hitl_reviews "
                        "ADD COLUMN artifact_json TEXT NOT NULL DEFAULT '{}'"
                    )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_hitl_reviews_created_at "
                    "ON hitl_reviews(created_at DESC)"
                )
        except sqlite3.Error as error:
            raise ReviewPersistenceError(
                f"HITL SQLite 저장소를 초기화하지 못했습니다: {type(error).__name__}"
            ) from error

    @staticmethod
    def _normalize_json(value: object, field_name: str) -> str:
        try:
            if isinstance(value, str):
                parsed = json.loads(value)
            else:
                parsed = value
            return json.dumps(parsed, ensure_ascii=False, default=str)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ReviewPersistenceError(f"{field_name}에 유효하지 않은 JSON 값이 전달되었습니다.") from error

    def save_review(self, record: dict) -> None:
        review_id = str(record.get("review_id", "")).strip()
        created_at = str(record.get("created_at", "")).strip()
        if not review_id:
            raise ReviewPersistenceError("review_id가 없어 HITL 기록을 저장할 수 없습니다.")
        if not created_at:
            raise ReviewPersistenceError("created_at이 없어 HITL 기록을 저장할 수 없습니다.")

        normalized = dict(record)
        for field in self.JSON_FIELDS:
            default = [] if field == "tool_trace_json" else {}
            normalized[field] = self._normalize_json(normalized.get(field, default), field)

        columns = (
            "review_id", "created_at", "model", "target", "decision", "reviewer",
            "reviewer_note", "final_answer", "tool_trace_json", "virtual_patch_json",
            "self_reflection_json", "dataset_name", "app_version", "artifact_path",
            "artifact_json",
        )
        values = [str(normalized.get(column, "")) for column in columns]
        placeholders = ", ".join("?" for _ in columns)
        try:
            with closing(self._connect()) as connection, connection:
                connection.execute(
                    f"INSERT INTO hitl_reviews ({', '.join(columns)}) VALUES ({placeholders})",
                    values,
                )
        except sqlite3.IntegrityError as error:
            raise DuplicateReviewError(f"이미 저장된 review_id입니다: {review_id}") from error
        except sqlite3.Error as error:
            raise ReviewPersistenceError(
                f"HITL SQLite 기록 저장에 실패했습니다: {type(error).__name__}"
            ) from error

    def list_reviews(self, limit: int = 1000) -> pd.DataFrame:
        safe_limit = min(max(int(limit), 1), 10000)
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT review_id, created_at AS created_at_kst, reviewer,
                           decision AS review_status, target AS review_target,
                           reviewer_note AS human_comment, dataset_name AS data_profile,
                           model, app_version, artifact_path
                    FROM hitl_reviews
                    ORDER BY created_at DESC, review_id DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
            return pd.DataFrame([dict(row) for row in rows])
        except sqlite3.Error as error:
            raise ReviewPersistenceError(
                f"HITL SQLite 기록 조회에 실패했습니다: {type(error).__name__}"
            ) from error


@contextmanager
def exclusive_file_lock(target: Path, timeout_seconds: float = 10.0) -> Iterator[None]:
    """Cross-platform advisory lock using a sidecar file."""
    lock_path = target.with_suffix(target.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    fd = None
    while fd is None:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"저장소 잠금 대기 시간을 초과했습니다: {lock_path}")
            time.sleep(0.05)
    try:
        os.write(fd, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def append_csv_record(path: Path, row: dict, unique_key: str | None = None) -> None:
    """Lock, merge, and atomically replace a CSV review log."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with exclusive_file_lock(path):
        existing = pd.read_csv(path) if path.exists() else pd.DataFrame()
        if unique_key and unique_key in row and unique_key in existing.columns:
            if str(row[unique_key]) in set(existing[unique_key].astype(str)):
                raise ValueError(f"중복 {unique_key}: {row[unique_key]}")
        output = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        output.to_csv(temporary, index=False, encoding="utf-8-sig")
        os.replace(temporary, path)


def export_json_record(path: Path, artifact: Any) -> None:
    """Atomically export a compatibility JSON artifact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(artifact, handle, ensure_ascii=False, indent=2, default=str)
        os.replace(temporary, path)
    except (OSError, TypeError, ValueError) as error:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise ReviewPersistenceError(
            f"HITL JSON export에 실패했습니다: {type(error).__name__}"
        ) from error


def save_review_with_mirrors(
    repository: SQLiteReviewRepository,
    db_record: dict[str, Any],
    *,
    csv_path: Path,
    csv_row: dict[str, Any],
    json_path: Path,
    json_artifact: Any,
    csv_exporter: Callable[[Path, dict, str | None], None] = append_csv_record,
    json_exporter: Callable[[Path, Any], None] = export_json_record,
) -> dict[str, Any]:
    """Commit the authoritative DB record, then attempt compatibility mirrors.

    A database failure is fatal and no mirror is attempted. Mirror failures are
    non-fatal because SQLite is the authoritative HITL record.
    """
    try:
        repository.save_review(db_record)
    except ReviewPersistenceError as error:
        error.storage_result = {
            "status": "failed",
            "db_saved": False,
            "csv_exported": False,
            "json_exported": False,
            "mirror_warning": "DB 저장 실패로 호환 export를 실행하지 않았습니다.",
        }
        raise
    result: dict[str, Any] = {
        "status": "saved",
        "db_saved": True,
        "csv_exported": False,
        "json_exported": False,
        "mirror_warning": "",
    }
    warnings: list[str] = []

    try:
        json_exporter(Path(json_path), json_artifact)
        result["json_exported"] = True
    except Exception as error:
        warnings.append(f"JSON mirror 실패: {type(error).__name__}")

    try:
        csv_exporter(Path(csv_path), csv_row, "review_id")
        result["csv_exported"] = True
    except Exception as error:
        warnings.append(f"CSV mirror 실패: {type(error).__name__}")

    if warnings:
        result["status"] = "partial"
        result["mirror_warning"] = (
            "SQLite 기준 기록은 저장됐지만 일부 호환 export가 실패했습니다. "
            + " / ".join(warnings)
        )
    return result
