"""
Storage backends for checkpoint persistence.

Provides protocol for storage backends and filesystem implementation.
"""

import json
import logging
import shutil
import tempfile
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from .types import AgentState, CheckpointMetadata

logger = logging.getLogger(__name__)


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol for checkpoint storage backends"""

    @abstractmethod
    async def save(self, state: AgentState) -> str:
        """
        Save checkpoint and return checkpoint_id.

        Args:
            state: Agent state to checkpoint

        Returns:
            checkpoint_id of saved checkpoint

        Raises:
            IOError: If save fails
        """
        ...

    @abstractmethod
    async def load(self, checkpoint_id: str) -> AgentState:
        """
        Load checkpoint by ID.

        Args:
            checkpoint_id: ID of checkpoint to load

        Returns:
            AgentState restored from checkpoint

        Raises:
            FileNotFoundError: If checkpoint doesn't exist
        """
        ...

    @abstractmethod
    async def list_checkpoints(
        self, agent_id: str | None = None
    ) -> list[CheckpointMetadata]:
        """
        List all checkpoints (optionally filtered by agent_id).

        Args:
            agent_id: Filter checkpoints for specific agent (None = all)

        Returns:
            List of checkpoint metadata sorted by timestamp (newest first)
        """
        ...

    @abstractmethod
    async def delete(self, checkpoint_id: str) -> None:
        """
        Delete checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to delete

        Raises:
            FileNotFoundError: If checkpoint doesn't exist
        """
        ...

    @abstractmethod
    async def exists(self, checkpoint_id: str) -> bool:
        """
        Check if checkpoint exists.

        Args:
            checkpoint_id: ID of checkpoint

        Returns:
            True if checkpoint exists
        """
        ...


class FilesystemStorage:
    """
    Filesystem-based checkpoint storage (JSONL format).

    Stores checkpoints as JSONL files with atomic writes and compression support.
    """

    def __init__(
        self,
        base_dir: str | Path = ".kaizen/checkpoints",
        compress: bool = False,
    ):
        """
        Initialize filesystem storage.

        Args:
            base_dir: Directory for checkpoint storage
            compress: Whether to compress checkpoints (gzip)
        """
        self.base_dir = Path(base_dir)
        self.compress = compress

        # Create directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Filesystem storage initialized: {self.base_dir}")

    async def save(self, state: AgentState) -> str:
        """
        Save checkpoint as JSONL file with atomic write.

        Uses temp file + rename for atomicity.

        Args:
            state: Agent state to checkpoint

        Returns:
            checkpoint_id

        Raises:
            IOError: If save fails
        """
        checkpoint_path = self.base_dir / f"{state.checkpoint_id}.jsonl"

        try:
            # Convert state to dict
            state_dict = state.to_dict()

            # Write to temp file first (atomic write pattern)
            with tempfile.NamedTemporaryFile(
                mode="w", dir=self.base_dir, delete=False, suffix=".tmp"
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                json.dump(state_dict, tmp_file)
                tmp_file.write("\n")

            # Atomic rename
            shutil.move(str(tmp_path), str(checkpoint_path))

            size_bytes = checkpoint_path.stat().st_size
            logger.info(f"Checkpoint saved: {state.checkpoint_id} ({size_bytes} bytes)")

            return state.checkpoint_id

        except Exception as e:
            logger.error(f"Failed to save checkpoint {state.checkpoint_id}: {e}")
            # Clean up temp file if it exists
            if tmp_path.exists():
                tmp_path.unlink()
            raise IOError(f"Failed to save checkpoint: {e}")

    async def load(self, checkpoint_id: str) -> AgentState:
        """
        Load checkpoint from JSONL file.

        Args:
            checkpoint_id: ID of checkpoint to load

        Returns:
            AgentState restored from checkpoint

        Raises:
            FileNotFoundError: If checkpoint doesn't exist
        """
        checkpoint_path = self.base_dir / f"{checkpoint_id}.jsonl"

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")

        try:
            with open(checkpoint_path, "r") as f:
                state_dict = json.loads(f.read().strip())

            state = AgentState.from_dict(state_dict)
            logger.info(f"Checkpoint loaded: {checkpoint_id}")

            return state

        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            raise IOError(f"Failed to load checkpoint: {e}")

    async def list_checkpoints(
        self, agent_id: str | None = None
    ) -> list[CheckpointMetadata]:
        """
        List all checkpoints in directory.

        Args:
            agent_id: Filter checkpoints for specific agent (None = all)

        Returns:
            List of checkpoint metadata sorted by timestamp (newest first)
        """
        checkpoints = []

        try:
            for path in self.base_dir.glob("*.jsonl"):
                # Read checkpoint to get metadata
                try:
                    with open(path, "r") as f:
                        state_dict = json.loads(f.read().strip())

                    # Filter by agent_id if specified
                    if agent_id and state_dict.get("agent_id") != agent_id:
                        continue

                    # Parse timestamp
                    timestamp_str = state_dict["timestamp"]
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str)
                    else:
                        timestamp = timestamp_str

                    metadata = CheckpointMetadata(
                        checkpoint_id=state_dict["checkpoint_id"],
                        agent_id=state_dict["agent_id"],
                        timestamp=timestamp,
                        step_number=state_dict["step_number"],
                        status=state_dict["status"],
                        size_bytes=path.stat().st_size,
                        parent_checkpoint_id=state_dict.get("parent_checkpoint_id"),
                    )
                    checkpoints.append(metadata)

                except Exception as e:
                    logger.warning(f"Failed to read checkpoint {path.name}: {e}")
                    continue

            # Sort by timestamp (newest first)
            checkpoints.sort(key=lambda c: c.timestamp, reverse=True)

            return checkpoints

        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def delete(self, checkpoint_id: str) -> None:
        """
        Delete checkpoint file.

        Args:
            checkpoint_id: ID of checkpoint to delete

        Raises:
            FileNotFoundError: If checkpoint doesn't exist
        """
        checkpoint_path = self.base_dir / f"{checkpoint_id}.jsonl"

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")

        try:
            checkpoint_path.unlink()
            logger.info(f"Checkpoint deleted: {checkpoint_id}")

        except Exception as e:
            logger.error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            raise IOError(f"Failed to delete checkpoint: {e}")

    async def exists(self, checkpoint_id: str) -> bool:
        """
        Check if checkpoint exists.

        Args:
            checkpoint_id: ID of checkpoint

        Returns:
            True if checkpoint exists
        """
        checkpoint_path = self.base_dir / f"{checkpoint_id}.jsonl"
        return checkpoint_path.exists()


# Export all public types
__all__ = [
    "StorageBackend",
    "FilesystemStorage",
]
