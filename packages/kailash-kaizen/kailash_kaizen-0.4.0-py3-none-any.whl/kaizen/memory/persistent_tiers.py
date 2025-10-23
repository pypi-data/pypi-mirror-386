"""
Persistent memory tier implementations for warm and cold storage.

This module provides persistent storage implementations with different
performance characteristics and use cases.
"""

import gzip
import hashlib
import json
import logging
import os
import pickle
import sqlite3
import time
from typing import Any, Optional

import aiosqlite

from .tiers import MemoryTier

logger = logging.getLogger(__name__)


class WarmMemoryTier(MemoryTier):
    """Fast persistent storage with <10ms access time"""

    def __init__(self, storage_path: str = None, max_size_mb: int = 1000):
        super().__init__("warm")
        self.storage_path = storage_path or os.path.join(
            os.getcwd(), ".kaizen", "memory", "warm.db"
        )
        self.max_size_mb = max_size_mb
        self._connection_pool = {}
        self._setup_database()

    def _setup_database(self):
        """Setup SQLite database for warm tier storage"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

            # Create database with optimized settings
            conn = sqlite3.connect(self.storage_path, check_same_thread=False)

            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")

            # Create table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS warm_memory (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    metadata TEXT,
                    ttl INTEGER,
                    created_at REAL,
                    last_accessed REAL,
                    access_count INTEGER DEFAULT 1,
                    value_size INTEGER
                )
            """
            )

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ttl ON warm_memory(ttl)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_last_accessed ON warm_memory(last_accessed)"
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to setup warm memory database: {e}")
            raise

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve data from warm tier with <10ms target"""
        start_time = time.perf_counter()

        try:
            async with aiosqlite.connect(self.storage_path) as conn:
                # Enable optimizations
                await conn.execute("PRAGMA cache_size=10000")

                cursor = await conn.execute(
                    """
                    SELECT value, ttl, last_accessed
                    FROM warm_memory
                    WHERE key = ?
                """,
                    (key,),
                )

                row = await cursor.fetchone()

                if row is None:
                    self._record_miss()
                    return None

                value_blob, ttl, last_accessed = row

                # Check TTL
                if ttl and time.time() > ttl:
                    await self.delete(key)
                    self._record_miss()
                    return None

                # Update access tracking
                current_time = time.time()
                await conn.execute(
                    """
                    UPDATE warm_memory
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE key = ?
                """,
                    (current_time, key),
                )
                await conn.commit()

                # Deserialize value
                try:
                    value = pickle.loads(value_blob)
                except:
                    # Fallback to JSON
                    value = json.loads(value_blob.decode("utf-8"))

                self._record_hit()

                # Log performance if it exceeds target
                elapsed = (time.perf_counter() - start_time) * 1000  # ms
                if elapsed > 10.0:
                    logger.warning(
                        f"Warm tier access took {elapsed:.2f}ms, exceeds <10ms target"
                    )

                return value

        except Exception as e:
            logger.error(f"Error in WarmMemoryTier.get({key}): {e}")
            self._record_miss()
            return None

    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store data in warm tier"""
        try:
            # Serialize value
            try:
                value_blob = pickle.dumps(value)
            except:
                # Fallback to JSON
                value_blob = json.dumps(value).encode("utf-8")

            value_size = len(value_blob)
            current_time = time.time()
            ttl_timestamp = current_time + ttl if ttl else None

            metadata = json.dumps(
                {
                    "serialization": (
                        "pickle" if isinstance(value_blob, bytes) else "json"
                    ),
                    "compressed": False,
                }
            )

            async with aiosqlite.connect(self.storage_path) as conn:
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO warm_memory
                    (key, value, metadata, ttl, created_at, last_accessed, value_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        key,
                        value_blob,
                        metadata,
                        ttl_timestamp,
                        current_time,
                        current_time,
                        value_size,
                    ),
                )

                await conn.commit()

            # Check if we need to cleanup due to size limits
            await self._cleanup_if_needed()

            self._record_put()
            return True

        except Exception as e:
            logger.error(f"Error in WarmMemoryTier.put({key}): {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete data from warm tier"""
        try:
            async with aiosqlite.connect(self.storage_path) as conn:
                cursor = await conn.execute(
                    """
                    DELETE FROM warm_memory WHERE key = ?
                """,
                    (key,),
                )
                await conn.commit()

                if cursor.rowcount > 0:
                    self._record_delete()
                    return True
                return False

        except Exception as e:
            logger.error(f"Error in WarmMemoryTier.delete({key}): {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in warm tier"""
        try:
            async with aiosqlite.connect(self.storage_path) as conn:
                cursor = await conn.execute(
                    """
                    SELECT 1 FROM warm_memory WHERE key = ? AND (ttl IS NULL OR ttl > ?)
                """,
                    (key, time.time()),
                )

                row = await cursor.fetchone()
                return row is not None

        except Exception as e:
            logger.error(f"Error in WarmMemoryTier.exists({key}): {e}")
            return False

    async def clear(self) -> bool:
        """Clear all data from warm tier"""
        try:
            async with aiosqlite.connect(self.storage_path) as conn:
                await conn.execute("DELETE FROM warm_memory")
                await conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error in WarmMemoryTier.clear(): {e}")
            return False

    async def size(self) -> int:
        """Get current size of warm tier"""
        try:
            async with aiosqlite.connect(self.storage_path) as conn:
                cursor = await conn.execute(
                    """
                    SELECT COUNT(*) FROM warm_memory WHERE ttl IS NULL OR ttl > ?
                """,
                    (time.time(),),
                )
                row = await cursor.fetchone()
                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Error getting WarmMemoryTier size: {e}")
            return 0

    async def _cleanup_if_needed(self):
        """Cleanup expired items and enforce size limits"""
        try:
            async with aiosqlite.connect(self.storage_path) as conn:
                # Remove expired items
                await conn.execute(
                    """
                    DELETE FROM warm_memory WHERE ttl IS NOT NULL AND ttl <= ?
                """,
                    (time.time(),),
                )

                # Check total size
                cursor = await conn.execute(
                    """
                    SELECT SUM(value_size) FROM warm_memory
                """
                )
                row = await cursor.fetchone()
                total_size_bytes = row[0] if row and row[0] else 0
                total_size_mb = total_size_bytes / (1024 * 1024)

                # If over limit, remove least recently accessed items
                if total_size_mb > self.max_size_mb:
                    # Calculate how much to remove (10% buffer)
                    target_size_mb = self.max_size_mb * 0.9

                    await conn.execute(
                        """
                        DELETE FROM warm_memory WHERE key IN (
                            SELECT key FROM warm_memory
                            ORDER BY last_accessed ASC
                            LIMIT (
                                SELECT COUNT(*) FROM warm_memory
                            ) / 10
                        )
                    """
                    )

                await conn.commit()

        except Exception as e:
            logger.error(f"Error in warm tier cleanup: {e}")


class ColdMemoryTier(MemoryTier):
    """Archival storage with <100ms access time"""

    def __init__(self, storage_path: str = None, compression: bool = True):
        super().__init__("cold")
        self.storage_path = storage_path or os.path.join(
            os.getcwd(), ".kaizen", "memory", "cold"
        )
        self.compression = compression
        self._setup_storage()

    def _setup_storage(self):
        """Setup file-based storage for cold tier"""
        try:
            os.makedirs(self.storage_path, exist_ok=True)

            # Create metadata database
            metadata_path = os.path.join(self.storage_path, "metadata.db")
            conn = sqlite3.connect(metadata_path, check_same_thread=False)

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cold_metadata (
                    key TEXT PRIMARY KEY,
                    filename TEXT,
                    ttl INTEGER,
                    created_at REAL,
                    last_accessed REAL,
                    file_size INTEGER,
                    compressed INTEGER
                )
            """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cold_ttl ON cold_metadata(ttl)"
            )
            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to setup cold memory storage: {e}")
            raise

    def _get_file_path(self, key: str) -> str:
        """Get file path for key using hash-based directory structure"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        # Use first 2 chars for subdirectory to avoid too many files in one dir
        subdir = key_hash[:2]
        filename = f"{key_hash}.dat"

        dir_path = os.path.join(self.storage_path, subdir)
        os.makedirs(dir_path, exist_ok=True)

        return os.path.join(dir_path, filename)

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve data from cold tier with <100ms target"""
        start_time = time.perf_counter()

        try:
            metadata_path = os.path.join(self.storage_path, "metadata.db")

            async with aiosqlite.connect(metadata_path) as conn:
                cursor = await conn.execute(
                    """
                    SELECT filename, ttl, compressed, last_accessed
                    FROM cold_metadata
                    WHERE key = ?
                """,
                    (key,),
                )

                row = await cursor.fetchone()

                if row is None:
                    self._record_miss()
                    return None

                filename, ttl, compressed, last_accessed = row

                # Check TTL
                if ttl and time.time() > ttl:
                    await self.delete(key)
                    self._record_miss()
                    return None

                # Read file
                file_path = (
                    os.path.join(self.storage_path, filename)
                    if filename
                    else self._get_file_path(key)
                )

                if not os.path.exists(file_path):
                    # File missing, clean up metadata
                    await conn.execute(
                        "DELETE FROM cold_metadata WHERE key = ?", (key,)
                    )
                    await conn.commit()
                    self._record_miss()
                    return None

                # Read and deserialize
                with open(file_path, "rb") as f:
                    data = f.read()

                if compressed:
                    data = gzip.decompress(data)

                try:
                    value = pickle.loads(data)
                except:
                    # Fallback to JSON
                    value = json.loads(data.decode("utf-8"))

                # Update access time
                current_time = time.time()
                await conn.execute(
                    """
                    UPDATE cold_metadata
                    SET last_accessed = ?
                    WHERE key = ?
                """,
                    (current_time, key),
                )
                await conn.commit()

                self._record_hit()

                # Log performance if it exceeds target
                elapsed = (time.perf_counter() - start_time) * 1000  # ms
                if elapsed > 100.0:
                    logger.warning(
                        f"Cold tier access took {elapsed:.2f}ms, exceeds <100ms target"
                    )

                return value

        except Exception as e:
            logger.error(f"Error in ColdMemoryTier.get({key}): {e}")
            self._record_miss()
            return None

    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store data in cold tier"""
        try:
            # Serialize value
            try:
                data = pickle.dumps(value)
            except:
                # Fallback to JSON
                data = json.dumps(value).encode("utf-8")

            # Compress if enabled
            compressed = False
            if self.compression and len(data) > 1024:  # Only compress larger items
                data = gzip.compress(data)
                compressed = True

            # Write to file
            file_path = self._get_file_path(key)
            with open(file_path, "wb") as f:
                f.write(data)

            # Update metadata
            current_time = time.time()
            ttl_timestamp = current_time + ttl if ttl else None
            filename = os.path.relpath(file_path, self.storage_path)

            metadata_path = os.path.join(self.storage_path, "metadata.db")
            async with aiosqlite.connect(metadata_path) as conn:
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO cold_metadata
                    (key, filename, ttl, created_at, last_accessed, file_size, compressed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        key,
                        filename,
                        ttl_timestamp,
                        current_time,
                        current_time,
                        len(data),
                        compressed,
                    ),
                )

                await conn.commit()

            self._record_put()
            return True

        except Exception as e:
            logger.error(f"Error in ColdMemoryTier.put({key}): {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete data from cold tier"""
        try:
            metadata_path = os.path.join(self.storage_path, "metadata.db")

            async with aiosqlite.connect(metadata_path) as conn:
                cursor = await conn.execute(
                    """
                    SELECT filename FROM cold_metadata WHERE key = ?
                """,
                    (key,),
                )

                row = await cursor.fetchone()

                if row:
                    filename = row[0]

                    # Delete file
                    file_path = (
                        os.path.join(self.storage_path, filename)
                        if filename
                        else self._get_file_path(key)
                    )
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    # Delete metadata
                    await conn.execute(
                        "DELETE FROM cold_metadata WHERE key = ?", (key,)
                    )
                    await conn.commit()

                    self._record_delete()
                    return True

                return False

        except Exception as e:
            logger.error(f"Error in ColdMemoryTier.delete({key}): {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cold tier"""
        try:
            metadata_path = os.path.join(self.storage_path, "metadata.db")

            async with aiosqlite.connect(metadata_path) as conn:
                cursor = await conn.execute(
                    """
                    SELECT 1 FROM cold_metadata WHERE key = ? AND (ttl IS NULL OR ttl > ?)
                """,
                    (key, time.time()),
                )

                row = await cursor.fetchone()
                return row is not None

        except Exception as e:
            logger.error(f"Error in ColdMemoryTier.exists({key}): {e}")
            return False

    async def clear(self) -> bool:
        """Clear all data from cold tier"""
        try:
            metadata_path = os.path.join(self.storage_path, "metadata.db")

            # Get all filenames to delete
            async with aiosqlite.connect(metadata_path) as conn:
                cursor = await conn.execute("SELECT filename FROM cold_metadata")
                filenames = await cursor.fetchall()

                # Delete all files
                for (filename,) in filenames:
                    file_path = os.path.join(self.storage_path, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)

                # Clear metadata
                await conn.execute("DELETE FROM cold_metadata")
                await conn.commit()

            return True

        except Exception as e:
            logger.error(f"Error in ColdMemoryTier.clear(): {e}")
            return False

    async def size(self) -> int:
        """Get current size of cold tier"""
        try:
            metadata_path = os.path.join(self.storage_path, "metadata.db")

            async with aiosqlite.connect(metadata_path) as conn:
                cursor = await conn.execute(
                    """
                    SELECT COUNT(*) FROM cold_metadata WHERE ttl IS NULL OR ttl > ?
                """,
                    (time.time(),),
                )
                row = await cursor.fetchone()
                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Error getting ColdMemoryTier size: {e}")
            return 0
