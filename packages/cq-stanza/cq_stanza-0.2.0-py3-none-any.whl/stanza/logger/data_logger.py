from __future__ import annotations

import getpass
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Any

from stanza.exceptions import LoggingError
from stanza.logger.datatypes import SessionMetadata
from stanza.logger.session import LoggerSession
from stanza.logger.writers.hdf5_writer import HDF5Writer
from stanza.logger.writers.jsonl_writer import JSONLWriter

logger = logging.getLogger(__name__)


class DataLogger:
    """Logger for data collection."""

    _WRITER_REGISTRY = {
        "hdf5": HDF5Writer,
        "jsonl": JSONLWriter,
    }

    def __init__(
        self,
        routine_name: str,
        base_dir: str | Path,
        name: str = "logger",
        formats: list[str] | None = None,
        routine_dir_name: str | None = None,
        compression: str | None = None,
        compression_level: int = 6,
        buffer_size: int = 1000,
        auto_flush_interval: float | None = 30.0,
    ):
        if not routine_name or not routine_name.strip():
            raise ValueError("Routine name is required")

        self.name = name
        self.routine_name = routine_name
        dir_name = routine_dir_name or self.routine_name
        dir_name = self._slugify(dir_name)
        self.base_directory = Path(base_dir) / dir_name
        self.base_directory.mkdir(parents=True, exist_ok=True)

        if formats is None:
            formats = ["jsonl"]

        for format in formats:
            if format not in self._WRITER_REGISTRY:
                raise ValueError(f"Invalid format: {format}")

        self._formats = formats
        self._active_sessions: dict[str, LoggerSession] = {}
        self._current_session: LoggerSession | None = None
        self._compression = compression
        self._compression_level = compression_level
        self._buffer_size = buffer_size
        self._auto_flush_interval = auto_flush_interval

    @staticmethod
    def _slugify(name: str) -> str:
        """Slugify a name."""
        name = name.strip()
        name = re.sub(r"[^A-Za-z0-9_-]+", "_", name)
        return name

    def create_session(self, session_id: str | None = None) -> LoggerSession:
        """Create a new logger session."""
        if session_id is None:
            timestamp = str(int(time.time()))
            unique_id = str(uuid.uuid4())[:8]
            session_id = f"{self.routine_name}_{timestamp}_{unique_id}"

        if self.get_session(session_id) is not None:
            raise LoggingError(f"Session with ID {session_id} already exists")

        if self._current_session is not None:
            if len(self._current_session._buffer) > 0:
                self._current_session.flush()
            current_session_id = self._current_session.session_id
            self.close_session(current_session_id)

        metadata = SessionMetadata(
            session_id=session_id,
            routine_name=self.routine_name,
            start_time=time.time(),
            user=getpass.getuser(),
            device_config=None,
            parameters={},
        )

        session_base_dir = self.base_directory / session_id
        session_base_dir.mkdir(parents=True, exist_ok=True)

        session_writers = []
        for format in self._formats:
            writer_class = self._WRITER_REGISTRY[format]

            writer = writer_class(
                base_directory=session_base_dir,
                compression=self._compression,
                compression_level=self._compression_level,
            )
            session_writers.append(writer)

        session_writer_pool = dict(zip(self._formats, session_writers, strict=False))

        writer_refs = list(session_writer_pool.keys())

        session = LoggerSession(
            metadata=metadata,
            writer_pool=session_writer_pool,
            writer_refs=writer_refs,
            base_dir=session_base_dir,
            buffer_size=self._buffer_size,
            auto_flush_interval=self._auto_flush_interval,
        )

        self._active_sessions[session_id] = session
        self._current_session = session
        session.initialize()

        logger.info("Created session: %s", session_id)
        return session

    def get_session(self, session_id: str) -> LoggerSession | None:
        """Get a session by ID."""
        return self._active_sessions.get(session_id)

    @property
    def active_sessions(self) -> list[LoggerSession]:
        """Get all active sessions."""
        return list(self._active_sessions.values())

    @property
    def current_session(self) -> LoggerSession | None:
        """Get the current session."""
        return self._current_session

    def close_session(self, session_id: str) -> None:
        """Close and remove a specific session."""
        if self.get_session(session_id) is None:
            raise LoggingError(f"Session with ID {session_id} does not exist")

        session = self._active_sessions[session_id]

        try:
            if len(session._buffer) > 0:
                logger.debug(
                    "Flushing %s buffered items before closing session %s",
                    len(session._buffer),
                    session_id,
                )
                session.flush()
            session.finalize()
            logger.debug("Closed session: %s", session_id)
        except Exception as e:
            logger.error("Failed to close session %s: %s", session_id, str(e))
        finally:
            del self._active_sessions[session_id]
            if self._current_session is session:
                self._current_session = None

    def close_all_sessions(self) -> None:
        """Close all active sessions."""
        session_ids = list(self._active_sessions.keys())
        for session_id in session_ids:
            try:
                self.close_session(session_id)
            except Exception as e:
                logger.error("Failed to close session %s: %s", session_id, str(e))

        logger.debug("Closed %s sessions", len(session_ids))

    def finalize(self) -> None:
        """Finalize the data logger."""
        self.close_all_sessions()

    def __enter__(self) -> DataLogger:
        """Enter the data logger context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """Exit the data logger context."""
        self.finalize()

    def __repr__(self) -> str:
        return (
            f"DataLogger(routine_name={self.routine_name}, "
            f"sessions={len(self._active_sessions)})"
        )
