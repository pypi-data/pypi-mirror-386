"""SQLAlchemy-based metadata store implementation for Nexus.

Production-ready metadata store using SQLAlchemy ORM with support for:
- File path mapping (virtual path → physical backend path)
- File metadata (arbitrary key-value pairs)
- Content chunks (for deduplication)
- Multiple database backends (SQLite, PostgreSQL)
"""

from __future__ import annotations

import builtins
import json
import os
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, pool, select, text
from sqlalchemy.orm import sessionmaker

from nexus.core.exceptions import MetadataError
from nexus.core.metadata import FileMetadata, MetadataStore
from nexus.storage.cache import _CACHE_MISS, MetadataCache
from nexus.storage.models import Base, FileMetadataModel, FilePathModel, VersionHistoryModel


class SQLAlchemyMetadataStore(MetadataStore):
    """
    SQLAlchemy-based metadata store supporting multiple database backends.

    Uses SQLAlchemy ORM for database operations with support for:
    - File path mapping (virtual path -> physical backend path)
    - File metadata (arbitrary key-value pairs)
    - Content chunks (for deduplication)
    - Multiple database backends (SQLite, PostgreSQL)

    Environment Variables:
        NEXUS_DATABASE_URL: Database connection URL (e.g., postgresql://user:pass@host/db)
                           If not set, falls back to db_path parameter (SQLite)
        POSTGRES_URL: Alternative to NEXUS_DATABASE_URL for PostgreSQL
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        db_url: str | None = None,
        run_migrations: bool = False,
        enable_cache: bool = True,
        cache_path_size: int = 512,
        cache_list_size: int = 128,
        cache_kv_size: int = 256,
        cache_exists_size: int = 1024,
        cache_ttl_seconds: int | None = 300,
    ):
        """
        Initialize SQLAlchemy metadata store.

        Args:
            db_path: Path to SQLite database file (deprecated, use db_url for flexibility)
            db_url: Database URL (e.g., 'postgresql://user:pass@host/db' or 'sqlite:///path/to/db')
                   If not provided, checks NEXUS_DATABASE_URL or POSTGRES_URL env vars,
                   then falls back to db_path parameter
            run_migrations: If True, run Alembic migrations on startup (default: False)
            enable_cache: If True, enable in-memory caching (default: True)
            cache_path_size: Max entries for path metadata cache (default: 512)
            cache_list_size: Max entries for directory listing cache (default: 128)
            cache_kv_size: Max entries for file metadata KV cache (default: 256)
            cache_exists_size: Max entries for existence check cache (default: 1024)
            cache_ttl_seconds: Cache TTL in seconds, None = no expiry (default: 300)
        """
        # Determine database URL from multiple sources (priority order)
        self.database_url: str = (
            db_url
            or os.getenv("NEXUS_DATABASE_URL")
            or os.getenv("POSTGRES_URL")
            or (f"sqlite:///{db_path}" if db_path else None)
            or ""
        )

        if not self.database_url:
            raise MetadataError(
                "Database URL must be provided via db_url parameter, db_path parameter, "
                "NEXUS_DATABASE_URL, or POSTGRES_URL environment variable"
            )

        # Detect database type
        self.db_type = self._detect_db_type(self.database_url)

        # For SQLite, extract and ensure parent directory exists
        self.db_path: Path | None
        if self.db_type == "sqlite":
            self.db_path = self._extract_sqlite_path(self.database_url)
            self._ensure_parent_exists()
        else:
            self.db_path = None

        # Create engine with database-specific configuration
        engine_kwargs = self._get_engine_config()
        self.engine = create_engine(self.database_url, **engine_kwargs)

        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

        # Initialize cache
        self._cache_enabled = enable_cache
        self._cache: MetadataCache | None
        if enable_cache:
            self._cache = MetadataCache(
                path_cache_size=cache_path_size,
                list_cache_size=cache_list_size,
                kv_cache_size=cache_kv_size,
                exists_cache_size=cache_exists_size,
                ttl_seconds=cache_ttl_seconds,
            )
        else:
            self._cache = None

        # Track if store has been closed
        self._closed = False

        # Initialize schema
        if run_migrations:
            self._run_migrations()
        else:
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            # Create SQL views for work detection
            self._create_views()

        # Apply database-specific optimizations
        self._apply_db_optimizations()

    def _detect_db_type(self, db_url: str) -> str:
        """Detect database type from connection URL.

        Args:
            db_url: Database connection URL

        Returns:
            Database type: 'sqlite', 'postgresql', etc.
        """
        if db_url.startswith("sqlite"):
            return "sqlite"
        elif db_url.startswith(("postgres", "postgresql")):
            return "postgresql"
        else:
            # Default to generic SQL database
            return "unknown"

    def _extract_sqlite_path(self, db_url: str) -> Path:
        """Extract file path from SQLite URL.

        Args:
            db_url: SQLite database URL (e.g., 'sqlite:///path/to/db')

        Returns:
            Path object to the database file
        """
        # Remove sqlite:/// prefix
        path_str = db_url.replace("sqlite:///", "")
        return Path(path_str)

    def _get_engine_config(self) -> dict[str, Any]:
        """Get database-specific engine configuration.

        Returns:
            Dictionary of engine kwargs for create_engine()
        """
        config: dict[str, Any] = {
            "pool_pre_ping": True,  # Check connections before using them
        }

        if self.db_type == "sqlite":
            # SQLite-specific configuration
            # Use NullPool to avoid concurrency issues with SQLite
            config["poolclass"] = pool.NullPool
        elif self.db_type == "postgresql":
            # PostgreSQL-specific configuration
            # Use QueuePool with reasonable defaults for production
            config["poolclass"] = pool.QueuePool
            config["pool_size"] = 5  # Number of connections to maintain
            config["max_overflow"] = 10  # Max connections above pool_size
            config["pool_timeout"] = 30  # Seconds to wait for connection
            config["pool_recycle"] = 3600  # Recycle connections after 1 hour

        return config

    def _apply_db_optimizations(self) -> None:
        """Apply database-specific performance optimizations."""
        if self.db_type == "sqlite":
            # Enable WAL mode for better concurrency and to avoid journal files
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("PRAGMA journal_mode=WAL"))
                    # Use FULL synchronous mode to prevent race conditions
                    # This ensures commits are fully written to disk before returning
                    # Critical for preventing "File not found" errors in CAS operations
                    conn.execute(text("PRAGMA synchronous=FULL"))
                    conn.commit()
            except Exception:
                # Ignore if optimizations cannot be enabled
                pass
        elif self.db_type == "postgresql":
            # PostgreSQL optimizations can be set at connection level if needed
            # Most optimizations are better set in postgresql.conf
            pass

    def _ensure_parent_exists(self) -> None:
        """Create parent directory for database if it doesn't exist (SQLite only)."""
        if self.db_path:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _run_migrations(self) -> None:
        """Run Alembic migrations to create/update schema."""
        try:
            from alembic.config import Config

            from alembic import command

            # Configure Alembic
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

            # Run migrations
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            raise MetadataError(f"Failed to run migrations: {e}") from e

    def _create_views(self) -> None:
        """Create SQL views for work detection if they don't exist.

        For PostgreSQL: Uses CREATE OR REPLACE VIEW (always updates views)
        For SQLite: Uses CREATE VIEW IF NOT EXISTS (creates only if missing)
        """
        import sys

        try:
            from nexus.storage import views

            # Get database-specific views
            all_views = views.get_all_views(self.db_type)

            with self.engine.connect() as conn:
                for _name, view_sql in all_views:
                    try:
                        conn.execute(view_sql)
                        conn.commit()
                    except Exception:
                        # For PostgreSQL, if CREATE OR REPLACE fails, rollback and try dropping first
                        if self.db_type == "postgresql":
                            try:
                                # CRITICAL: Rollback the failed transaction first
                                conn.rollback()
                                conn.execute(text(f"DROP VIEW IF EXISTS {_name} CASCADE"))
                                conn.commit()
                                conn.execute(view_sql)
                                conn.commit()
                            except Exception:
                                # Still failed - skip this view
                                conn.rollback()  # Clean up after failure
                                pass
                        # For SQLite, IF NOT EXISTS should handle it - silently skip failures
                        pass

        except Exception as e:
            # Log but don't fail initialization
            print(f"[Nexus] ERROR: View creation failed: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)

    def get(self, path: str) -> FileMetadata | None:
        """
        Get metadata for a file.

        Args:
            path: Virtual path

        Returns:
            FileMetadata if found, None otherwise
        """
        # Check cache first
        if self._cache_enabled and self._cache:
            cached = self._cache.get_path(path)
            if cached is not _CACHE_MISS:
                # Type narrowing: we know it's FileMetadata | None here
                return cached if isinstance(cached, FileMetadata) or cached is None else None

        try:
            with self.SessionLocal() as session:
                stmt = select(FilePathModel).where(
                    FilePathModel.virtual_path == path, FilePathModel.deleted_at.is_(None)
                )
                file_path = session.scalar(stmt)

                if file_path is None:
                    # Cache the negative result
                    if self._cache_enabled and self._cache:
                        self._cache.set_path(path, None)
                    return None

                metadata = FileMetadata(
                    path=file_path.virtual_path,
                    backend_name=file_path.backend_id,
                    physical_path=file_path.physical_path,
                    size=file_path.size_bytes,
                    etag=file_path.content_hash,
                    mime_type=file_path.file_type,
                    created_at=file_path.created_at,
                    modified_at=file_path.updated_at,
                    version=file_path.current_version,  # Version tracking (v0.3.5)
                    # UNIX-style permissions (v0.3.0)
                    owner=file_path.owner,
                    group=file_path.group,
                    mode=file_path.mode,
                )

                # Cache the result
                if self._cache_enabled and self._cache:
                    self._cache.set_path(path, metadata)

                return metadata
        except Exception as e:
            raise MetadataError(f"Failed to get metadata: {e}", path=path) from e

    def put(self, metadata: FileMetadata) -> None:
        """
        Store or update file metadata WITH VERSION TRACKING.

        When updating an existing file, creates a version history entry
        preserving the old content hash before updating to new content.

        Args:
            metadata: File metadata to store
        """
        # Validate BEFORE database operation
        metadata.validate()

        try:
            with self.SessionLocal() as session:
                # Check if file path already exists
                stmt = select(FilePathModel).where(
                    FilePathModel.virtual_path == metadata.path,
                    FilePathModel.deleted_at.is_(None),
                )
                existing = session.scalar(stmt)

                if existing:
                    # FILE UPDATE - Increment version and create history entry for NEW version

                    # Update existing record with new content
                    existing.backend_id = metadata.backend_name
                    existing.physical_path = metadata.physical_path
                    existing.size_bytes = metadata.size
                    existing.content_hash = metadata.etag  # NEW content hash
                    existing.file_type = metadata.mime_type
                    existing.updated_at = metadata.modified_at or datetime.now(UTC)
                    # Update permissions (v0.3.0)
                    existing.owner = metadata.owner
                    existing.group = metadata.group
                    existing.mode = metadata.mode

                    # Only create version history if we have actual content (etag is not None)
                    if metadata.etag is not None:
                        # Get the current version entry to link lineage
                        prev_version_stmt = (
                            select(VersionHistoryModel)
                            .where(
                                VersionHistoryModel.resource_type == "file",
                                VersionHistoryModel.resource_id == existing.path_id,
                                VersionHistoryModel.version_number == existing.current_version,
                            )
                            .limit(1)
                        )
                        prev_version = session.scalar(prev_version_stmt)

                        existing.current_version += 1  # Increment version

                        # Create version history entry for NEW version
                        version_entry = VersionHistoryModel(
                            version_id=str(uuid.uuid4()),
                            resource_type="file",
                            resource_id=existing.path_id,
                            version_number=existing.current_version,  # NEW version number
                            content_hash=metadata.etag,  # NEW content hash
                            size_bytes=metadata.size,
                            mime_type=metadata.mime_type,
                            parent_version_id=prev_version.version_id if prev_version else None,
                            source_type="original",
                            created_at=datetime.now(UTC),
                        )
                        version_entry.validate()
                        session.add(version_entry)
                else:
                    # NEW FILE - Create record and initial version history
                    file_path = FilePathModel(
                        path_id=str(uuid.uuid4()),
                        tenant_id=str(uuid.uuid4()),  # Default tenant for embedded mode
                        virtual_path=metadata.path,
                        backend_id=metadata.backend_name,
                        physical_path=metadata.physical_path,
                        size_bytes=metadata.size,
                        content_hash=metadata.etag,
                        file_type=metadata.mime_type,
                        created_at=metadata.created_at or datetime.now(UTC),
                        updated_at=metadata.modified_at or datetime.now(UTC),
                        current_version=1,  # Initial version
                        # UNIX-style permissions (v0.3.0)
                        owner=metadata.owner,
                        group=metadata.group,
                        mode=metadata.mode,
                    )
                    # Validate model before inserting
                    file_path.validate()
                    session.add(file_path)
                    session.flush()  # Get path_id

                    # Only create version history if we have actual content (etag is not None)
                    if metadata.etag is not None:
                        # Create initial version history entry
                        version_entry = VersionHistoryModel(
                            version_id=str(uuid.uuid4()),
                            resource_type="file",
                            resource_id=file_path.path_id,
                            version_number=1,
                            content_hash=metadata.etag,
                            size_bytes=metadata.size,
                            mime_type=metadata.mime_type,
                            parent_version_id=None,
                            source_type="original",
                            created_at=file_path.created_at,
                        )
                        version_entry.validate()
                        session.add(version_entry)

                session.commit()

            # Invalidate cache for this path
            if self._cache_enabled and self._cache:
                self._cache.invalidate_path(metadata.path)
        except Exception as e:
            raise MetadataError(f"Failed to store metadata: {e}", path=metadata.path) from e

    def delete(self, path: str) -> None:
        """
        Delete file metadata (soft delete).

        Args:
            path: Virtual path
        """
        try:
            with self.SessionLocal() as session:
                stmt = select(FilePathModel).where(
                    FilePathModel.virtual_path == path, FilePathModel.deleted_at.is_(None)
                )
                file_path = session.scalar(stmt)

                if file_path:
                    # Soft delete
                    file_path.deleted_at = datetime.now(UTC)
                    session.commit()

            # Invalidate cache for this path
            if self._cache_enabled and self._cache:
                self._cache.invalidate_path(path)
        except Exception as e:
            raise MetadataError(f"Failed to delete metadata: {e}", path=path) from e

    def rename_path(self, old_path: str, new_path: str) -> None:
        """
        Rename/move a file by updating its virtual path in metadata.

        This is a metadata-only operation that does NOT touch the actual
        file content in CAS storage. Only the virtual_path is updated.

        Args:
            old_path: Current virtual path
            new_path: New virtual path

        Raises:
            MetadataError: If the old path doesn't exist or new path already exists
        """
        try:
            with self.SessionLocal() as session:
                # Check if source exists
                stmt_old = select(FilePathModel).where(
                    FilePathModel.virtual_path == old_path, FilePathModel.deleted_at.is_(None)
                )
                file_path = session.scalar(stmt_old)

                if not file_path:
                    raise MetadataError(f"Source path not found: {old_path}", path=old_path)

                # Check if destination already exists
                stmt_new = select(FilePathModel).where(
                    FilePathModel.virtual_path == new_path, FilePathModel.deleted_at.is_(None)
                )
                existing = session.scalar(stmt_new)

                if existing:
                    raise MetadataError(
                        f"Destination path already exists: {new_path}", path=new_path
                    )

                # Update the virtual path (metadata-only, no CAS I/O!)
                file_path.virtual_path = new_path
                file_path.updated_at = datetime.now(UTC)
                session.commit()

            # Invalidate cache for both paths
            if self._cache_enabled and self._cache:
                self._cache.invalidate_path(old_path)
                self._cache.invalidate_path(new_path)
                # Also invalidate parent directories (this invalidates their listings too)
                old_parent = old_path.rsplit("/", 1)[0] or "/"
                new_parent = new_path.rsplit("/", 1)[0] or "/"
                self._cache.invalidate_path(old_parent)
                if old_parent != new_parent:
                    self._cache.invalidate_path(new_parent)

        except MetadataError:
            raise
        except Exception as e:
            raise MetadataError(f"Failed to rename path: {e}", path=old_path) from e

    def exists(self, path: str) -> bool:
        """
        Check if metadata exists for a path.

        Args:
            path: Virtual path

        Returns:
            True if metadata exists, False otherwise
        """
        # Check cache first
        if self._cache_enabled and self._cache:
            cached = self._cache.get_exists(path)
            if cached is not None:
                return cached

        try:
            with self.SessionLocal() as session:
                stmt = select(FilePathModel.path_id).where(
                    FilePathModel.virtual_path == path, FilePathModel.deleted_at.is_(None)
                )
                exists = session.scalar(stmt) is not None

                # Cache the result
                if self._cache_enabled and self._cache:
                    self._cache.set_exists(path, exists)

                return exists
        except Exception as e:
            raise MetadataError(f"Failed to check existence: {e}", path=path) from e

    def is_implicit_directory(self, path: str) -> bool:
        """
        Check if path is an implicit directory (has files beneath it).

        In NexusFS, directories are implicit - they exist if any files exist
        with the directory path as a prefix.

        Args:
            path: Virtual path to check

        Returns:
            True if path is an implicit directory, False otherwise
        """
        try:
            # Normalize path - ensure it ends with / for prefix matching
            dir_path = path.rstrip("/") + "/"

            with self.SessionLocal() as session:
                # Check if any files exist with this path as a prefix
                stmt = (
                    select(FilePathModel.path_id)
                    .where(
                        FilePathModel.virtual_path.like(f"{dir_path}%"),
                        FilePathModel.deleted_at.is_(None),
                    )
                    .limit(1)
                )
                has_children = session.scalar(stmt) is not None
                return has_children
        except Exception:
            return False

    def list(self, prefix: str = "") -> list[FileMetadata]:
        """
        List all files with given path prefix.

        Args:
            prefix: Path prefix to filter by

        Returns:
            List of file metadata
        """
        # Check cache first
        if self._cache_enabled and self._cache:
            cached = self._cache.get_list(prefix)
            if cached is not None:
                return cached

        try:
            with self.SessionLocal() as session:
                if prefix:
                    stmt = (
                        select(FilePathModel)
                        .where(
                            FilePathModel.virtual_path.like(f"{prefix}%"),
                            FilePathModel.deleted_at.is_(None),
                        )
                        .order_by(FilePathModel.virtual_path)
                    )
                else:
                    stmt = (
                        select(FilePathModel)
                        .where(FilePathModel.deleted_at.is_(None))
                        .order_by(FilePathModel.virtual_path)
                    )

                results = []
                for file_path in session.scalars(stmt):
                    results.append(
                        FileMetadata(
                            path=file_path.virtual_path,
                            backend_name=file_path.backend_id,
                            physical_path=file_path.physical_path,
                            size=file_path.size_bytes,
                            etag=file_path.content_hash,
                            mime_type=file_path.file_type,
                            created_at=file_path.created_at,
                            modified_at=file_path.updated_at,
                            version=file_path.current_version,  # Version tracking (v0.3.5)
                            # UNIX-style permissions (v0.3.0)
                            owner=file_path.owner,
                            group=file_path.group,
                            mode=file_path.mode,
                        )
                    )

                # Cache the results
                if self._cache_enabled and self._cache:
                    self._cache.set_list(prefix, results)

                return results
        except Exception as e:
            raise MetadataError(f"Failed to list metadata: {e}") from e

    def close(self) -> None:
        """Close database connection and dispose of engine."""
        import gc
        import sys
        import time

        if not hasattr(self, "engine"):
            return  # Already closed or never initialized

        # Prevent double-close
        if getattr(self, "_closed", False):
            return
        self._closed = True

        try:
            # CRITICAL: Force garbage collection BEFORE closing database
            # This ensures any lingering session references are cleaned up first
            # Especially important on Windows where sessions may hold file locks
            gc.collect()
            gc.collect(1)
            gc.collect(2)
            # Brief wait to let OS release file handles
            if sys.platform == "win32":
                time.sleep(0.05)  # 50ms on Windows
            else:
                time.sleep(0.01)  # 10ms elsewhere

            # SQLite-specific cleanup
            if self.db_type == "sqlite":
                # For SQLite, checkpoint WAL/journal files before disposing
                try:
                    # Create a new connection to ensure we have exclusive access
                    with self.engine.connect() as conn:
                        # Checkpoint WAL file to merge changes back to main database
                        conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
                        conn.commit()

                        # Switch to DELETE mode to remove WAL files
                        conn.execute(text("PRAGMA journal_mode=DELETE"))
                        conn.commit()

                        # Close the connection explicitly
                        conn.close()
                except Exception:
                    # Ignore errors during checkpoint (e.g., database already closed)
                    pass

            # Dispose of the connection pool - this closes all connections
            # Note: All sessions should be closed via context managers (with statements)
            # before this point. The dispose() call will close any remaining connections.
            self.engine.dispose()

            # CRITICAL: On Windows, force GC after disposal to release lingering references
            gc.collect()
            gc.collect(1)
            gc.collect(2)
            # Minimal wait for OS to release handles
            if sys.platform == "win32":
                time.sleep(0.1)  # 100ms on Windows
            else:
                time.sleep(0.01)  # 10ms elsewhere

            # SQLite-specific file cleanup
            if self.db_type == "sqlite" and self.db_path:
                # Additional cleanup: Try to remove any lingering SQLite temp files
                # This helps with test cleanup when using tempfile.TemporaryDirectory()
                try:
                    import os

                    for suffix in ["-wal", "-shm", "-journal"]:
                        temp_file = Path(str(self.db_path) + suffix)
                        if temp_file.exists():
                            # Retry a few times with small delays
                            # Windows needs more retries due to file locking behavior
                            max_retries = 10 if sys.platform == "win32" else 3
                            for attempt in range(max_retries):
                                try:
                                    os.remove(temp_file)
                                    break
                                except (OSError, PermissionError):
                                    # Short exponential backoff: 10ms, 20ms, 40ms, 80ms, ...
                                    # Cap at 500ms to avoid long delays
                                    wait_time = 0.01 * (2**attempt)
                                    time.sleep(min(wait_time, 0.5))
                                    # On last attempt, do one final GC
                                    if attempt == max_retries - 1:
                                        gc.collect()
                                        gc.collect(1)
                                        gc.collect(2)
                                        time.sleep(0.1)
                except Exception:
                    # Ignore errors - these files may not exist or may be locked
                    pass
        finally:
            # Mark as closed even if cleanup partially failed
            self._closed = True

    def get_cache_stats(self) -> dict[str, Any] | None:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics, or None if caching is disabled
        """
        if self._cache_enabled and self._cache:
            return self._cache.get_stats()
        return None

    def clear_cache(self) -> None:
        """Clear all cache entries."""
        if self._cache_enabled and self._cache:
            self._cache.clear()

    # Batch operations for performance

    def get_batch(self, paths: Sequence[str]) -> dict[str, FileMetadata | None]:
        """
        Get metadata for multiple files in a single query.

        This is more efficient than calling get() multiple times as it uses
        a single SQL query with IN clause instead of N queries.

        Args:
            paths: List of virtual paths

        Returns:
            Dictionary mapping path to FileMetadata (or None if not found)
        """
        if not paths:
            return {}

        # Check cache first for all paths
        result: dict[str, FileMetadata | None] = {}
        uncached_paths: list[str] = []

        if self._cache_enabled and self._cache:
            for path in paths:
                cached = self._cache.get_path(path)
                if cached is not _CACHE_MISS:
                    # Type narrowing: we know it's FileMetadata | None here
                    result[path] = (
                        cached if isinstance(cached, FileMetadata) or cached is None else None
                    )
                else:
                    uncached_paths.append(path)
        else:
            uncached_paths = list(paths)

        # If all paths were cached, return early
        if not uncached_paths:
            return result

        # Batch query for uncached paths
        try:
            with self.SessionLocal() as session:
                stmt = select(FilePathModel).where(
                    FilePathModel.virtual_path.in_(uncached_paths),
                    FilePathModel.deleted_at.is_(None),
                )

                # Build result dict
                found_paths = set()
                for file_path in session.scalars(stmt):
                    metadata = FileMetadata(
                        path=file_path.virtual_path,
                        backend_name=file_path.backend_id,
                        physical_path=file_path.physical_path,
                        size=file_path.size_bytes,
                        etag=file_path.content_hash,
                        mime_type=file_path.file_type,
                        created_at=file_path.created_at,
                        modified_at=file_path.updated_at,
                        version=file_path.current_version,  # Version tracking (v0.3.5)
                        # UNIX-style permissions (v0.3.0)
                        owner=file_path.owner,
                        group=file_path.group,
                        mode=file_path.mode,
                    )
                    result[file_path.virtual_path] = metadata
                    found_paths.add(file_path.virtual_path)

                    # Cache the result
                    if self._cache_enabled and self._cache:
                        self._cache.set_path(file_path.virtual_path, metadata)

                # Add None for paths not found
                for path in uncached_paths:
                    if path not in found_paths:
                        result[path] = None
                        # Cache the negative result
                        if self._cache_enabled and self._cache:
                            self._cache.set_path(path, None)

                return result
        except Exception as e:
            raise MetadataError(f"Failed to get batch metadata: {e}") from e

    def delete_batch(self, paths: Sequence[str]) -> None:
        """
        Delete multiple files in a single transaction.

        This is more efficient than calling delete() multiple times as it uses
        a single SQL UPDATE with IN clause instead of N queries.

        Args:
            paths: List of virtual paths to delete
        """
        if not paths:
            return

        try:
            with self.SessionLocal() as session:
                # Soft delete all paths in a single query
                stmt = select(FilePathModel).where(
                    FilePathModel.virtual_path.in_(paths), FilePathModel.deleted_at.is_(None)
                )

                deleted_paths: list[str] = []
                for file_path in session.scalars(stmt):
                    file_path.deleted_at = datetime.now(UTC)
                    deleted_paths.append(file_path.virtual_path)

                session.commit()

            # Invalidate cache for all deleted paths
            if self._cache_enabled and self._cache:
                for path in deleted_paths:
                    self._cache.invalidate_path(path)
        except Exception as e:
            raise MetadataError(f"Failed to delete batch metadata: {e}") from e

    def put_batch(self, metadata_list: Sequence[FileMetadata]) -> None:
        """
        Store or update multiple file metadata entries in a single transaction.

        This is more efficient than calling put() multiple times as it uses
        a single transaction instead of N transactions.

        Args:
            metadata_list: List of file metadata to store
        """
        if not metadata_list:
            return

        # Validate all metadata BEFORE any database operations
        for metadata in metadata_list:
            metadata.validate()

        try:
            with self.SessionLocal() as session:
                # Get all paths to check for existing entries
                paths: list[str] = [m.path for m in metadata_list]
                stmt = select(FilePathModel).where(
                    FilePathModel.virtual_path.in_(paths), FilePathModel.deleted_at.is_(None)
                )

                # Build dict of existing entries
                existing = {fp.virtual_path: fp for fp in session.scalars(stmt)}

                # Update or create entries
                for metadata in metadata_list:
                    if metadata.path in existing:
                        # Update existing record
                        file_path = existing[metadata.path]
                        file_path.backend_id = metadata.backend_name
                        file_path.physical_path = metadata.physical_path
                        file_path.size_bytes = metadata.size
                        file_path.content_hash = metadata.etag
                        file_path.file_type = metadata.mime_type
                        file_path.updated_at = metadata.modified_at or datetime.now(UTC)
                        # Update permissions (v0.3.0)
                        file_path.owner = metadata.owner
                        file_path.group = metadata.group
                        file_path.mode = metadata.mode
                    else:
                        # Create new record
                        file_path = FilePathModel(
                            path_id=str(uuid.uuid4()),
                            tenant_id=str(uuid.uuid4()),  # Default tenant for embedded mode
                            virtual_path=metadata.path,
                            backend_id=metadata.backend_name,
                            physical_path=metadata.physical_path,
                            size_bytes=metadata.size,
                            content_hash=metadata.etag,
                            file_type=metadata.mime_type,
                            created_at=metadata.created_at or datetime.now(UTC),
                            updated_at=metadata.modified_at or datetime.now(UTC),
                            # UNIX-style permissions (v0.3.0)
                            owner=metadata.owner,
                            group=metadata.group,
                            mode=metadata.mode,
                        )
                        # Validate model before inserting
                        file_path.validate()
                        session.add(file_path)

                session.commit()

            # Invalidate cache for all affected paths
            if self._cache_enabled and self._cache:
                for metadata in metadata_list:
                    self._cache.invalidate_path(metadata.path)
        except Exception as e:
            raise MetadataError(f"Failed to store batch metadata: {e}") from e

    def batch_get_content_ids(self, paths: Sequence[str]) -> dict[str, str | None]:
        """
        Get content IDs (hashes) for multiple paths in a single query.

        This is optimized for CAS (Content-Addressable Storage) deduplication.
        Instead of fetching full metadata for each file, this only fetches the
        content_hash field, which is more efficient for deduplication checks.

        Performance: Single SQL query with IN clause instead of N queries.

        Args:
            paths: List of virtual paths

        Returns:
            Dictionary mapping path to content_hash (or None if file not found)

        Example:
            >>> hashes = store.batch_get_content_ids(["/a.txt", "/b.txt", "/c.txt"])
            >>> # Find duplicates
            >>> from collections import defaultdict
            >>> by_hash = defaultdict(list)
            >>> for path, hash in hashes.items():
            ...     if hash:
            ...         by_hash[hash].append(path)
            >>> duplicates = {h: paths for h, paths in by_hash.items() if len(paths) > 1}
        """
        if not paths:
            return {}

        try:
            with self.SessionLocal() as session:
                # Single query to fetch only virtual_path and content_hash
                stmt = select(FilePathModel.virtual_path, FilePathModel.content_hash).where(
                    FilePathModel.virtual_path.in_(paths),
                    FilePathModel.deleted_at.is_(None),
                )

                # Build result dict
                result: dict[str, str | None] = {}
                found_paths = set()

                for virtual_path, content_hash in session.execute(stmt):
                    result[virtual_path] = content_hash
                    found_paths.add(virtual_path)

                # Add None for paths not found
                for path in paths:
                    if path not in found_paths:
                        result[path] = None

                return result
        except Exception as e:
            raise MetadataError(f"Failed to get batch content IDs: {e}") from e

    # Additional methods for file metadata (key-value pairs)

    def get_file_metadata(self, path: str, key: str) -> Any | None:
        """
        Get a specific metadata value for a file.

        Args:
            path: Virtual path
            key: Metadata key

        Returns:
            Metadata value (deserialized from JSON) or None
        """
        # Check cache first
        if self._cache_enabled and self._cache:
            cached = self._cache.get_kv(path, key)
            if cached is not _CACHE_MISS:
                return cached

        try:
            with self.SessionLocal() as session:
                # Get file path ID
                path_stmt = select(FilePathModel.path_id).where(
                    FilePathModel.virtual_path == path, FilePathModel.deleted_at.is_(None)
                )
                path_id = session.scalar(path_stmt)

                if path_id is None:
                    # Cache the negative result
                    if self._cache_enabled and self._cache:
                        self._cache.set_kv(path, key, None)
                    return None

                # Get metadata
                metadata_stmt = select(FileMetadataModel).where(
                    FileMetadataModel.path_id == path_id, FileMetadataModel.key == key
                )
                metadata = session.scalar(metadata_stmt)

                if metadata is None:
                    # Cache the negative result
                    if self._cache_enabled and self._cache:
                        self._cache.set_kv(path, key, None)
                    return None

                value = json.loads(metadata.value) if metadata.value else None

                # Cache the result
                if self._cache_enabled and self._cache:
                    self._cache.set_kv(path, key, value)

                return value
        except Exception as e:
            raise MetadataError(f"Failed to get file metadata: {e}", path=path) from e

    def set_file_metadata(self, path: str, key: str, value: Any) -> None:
        """
        Set a metadata value for a file.

        Args:
            path: Virtual path
            key: Metadata key
            value: Metadata value (will be serialized to JSON)
        """
        try:
            with self.SessionLocal() as session:
                # Get file path ID
                path_stmt = select(FilePathModel.path_id).where(
                    FilePathModel.virtual_path == path, FilePathModel.deleted_at.is_(None)
                )
                path_id = session.scalar(path_stmt)

                if path_id is None:
                    raise MetadataError("File not found", path=path)

                # Check if metadata exists
                metadata_stmt = select(FileMetadataModel).where(
                    FileMetadataModel.path_id == path_id, FileMetadataModel.key == key
                )
                metadata = session.scalar(metadata_stmt)

                value_json = json.dumps(value) if value is not None else None

                if metadata:
                    # Update existing
                    metadata.value = value_json
                else:
                    # Create new
                    metadata = FileMetadataModel(
                        metadata_id=str(uuid.uuid4()),
                        path_id=path_id,
                        key=key,
                        value=value_json,
                        created_at=datetime.now(UTC),
                    )
                    # Validate model before inserting
                    metadata.validate()
                    session.add(metadata)

                session.commit()

            # Invalidate cache for this specific key
            if self._cache_enabled and self._cache:
                self._cache.invalidate_kv(path, key)
        except Exception as e:
            raise MetadataError(f"Failed to set file metadata: {e}", path=path) from e

    def get_path_id(self, path: str) -> str | None:
        """Get the UUID path_id for a virtual path.

        This is useful for setting up work dependencies (depends_on metadata).

        Args:
            path: Virtual path

        Returns:
            UUID path_id string or None if path doesn't exist
        """
        try:
            with self.SessionLocal() as session:
                stmt = select(FilePathModel.path_id).where(
                    FilePathModel.virtual_path == path, FilePathModel.deleted_at.is_(None)
                )
                path_id = session.scalar(stmt)
                return path_id
        except Exception as e:
            raise MetadataError(f"Failed to get path_id: {e}", path=path) from e

    # Work detection queries (using SQL views)

    def get_ready_work(self, limit: int | None = None) -> builtins.list[dict[str, Any]]:
        """Get files that are ready for processing.

        Uses the ready_work_items SQL view which efficiently finds files with:
        - status='ready'
        - No blocking dependencies

        Args:
            limit: Optional limit on number of results

        Returns:
            List of work item dicts with path, status, priority, etc.
        """
        try:
            with self.SessionLocal() as session:
                query = "SELECT * FROM ready_work_items"
                if limit:
                    query += f" LIMIT {limit}"

                result = session.execute(text(query))
                rows = result.fetchall()

                return [
                    {
                        "path_id": row[0],
                        "tenant_id": row[1],
                        "virtual_path": row[2],
                        "backend_id": row[3],
                        "physical_path": row[4],
                        "file_type": row[5],
                        "size_bytes": row[6],
                        "content_hash": row[7],
                        "created_at": row[8],
                        "updated_at": row[9],
                        "status": json.loads(row[10]) if row[10] else None,
                        "priority": json.loads(row[11]) if row[11] else None,
                    }
                    for row in rows
                ]
        except Exception as e:
            raise MetadataError(f"Failed to get ready work: {e}") from e

    def get_pending_work(self, limit: int | None = None) -> builtins.list[dict[str, Any]]:
        """Get files with status='pending' ordered by priority.

        Uses the pending_work_items SQL view.

        Args:
            limit: Optional limit on number of results

        Returns:
            List of work item dicts
        """
        try:
            with self.SessionLocal() as session:
                query = "SELECT * FROM pending_work_items"
                if limit:
                    query += f" LIMIT {limit}"

                result = session.execute(text(query))
                rows = result.fetchall()

                return [
                    {
                        "path_id": row[0],
                        "tenant_id": row[1],
                        "virtual_path": row[2],
                        "backend_id": row[3],
                        "physical_path": row[4],
                        "file_type": row[5],
                        "size_bytes": row[6],
                        "content_hash": row[7],
                        "created_at": row[8],
                        "updated_at": row[9],
                        "status": json.loads(row[10]) if row[10] else None,
                        "priority": json.loads(row[11]) if row[11] else None,
                    }
                    for row in rows
                ]
        except Exception as e:
            raise MetadataError(f"Failed to get pending work: {e}") from e

    def get_blocked_work(self, limit: int | None = None) -> builtins.list[dict[str, Any]]:
        """Get files that are blocked by dependencies.

        Uses the blocked_work_items SQL view.

        Args:
            limit: Optional limit on number of results

        Returns:
            List of work item dicts with blocker_count
        """
        try:
            with self.SessionLocal() as session:
                query = "SELECT * FROM blocked_work_items"
                if limit:
                    query += f" LIMIT {limit}"

                result = session.execute(text(query))
                rows = result.fetchall()

                return [
                    {
                        "path_id": row[0],
                        "tenant_id": row[1],
                        "virtual_path": row[2],
                        "backend_id": row[3],
                        "physical_path": row[4],
                        "file_type": row[5],
                        "size_bytes": row[6],
                        "content_hash": row[7],
                        "created_at": row[8],
                        "updated_at": row[9],
                        "status": json.loads(row[10]) if row[10] else None,
                        "priority": json.loads(row[11]) if row[11] else None,
                        "blocker_count": row[12],
                    }
                    for row in rows
                ]
        except Exception as e:
            raise MetadataError(f"Failed to get blocked work: {e}") from e

    def get_in_progress_work(self, limit: int | None = None) -> builtins.list[dict[str, Any]]:
        """Get files currently being processed.

        Uses the in_progress_work SQL view.

        Args:
            limit: Optional limit on number of results

        Returns:
            List of work item dicts with worker_id and started_at
        """
        try:
            with self.SessionLocal() as session:
                query = "SELECT * FROM in_progress_work"
                if limit:
                    query += f" LIMIT {limit}"

                result = session.execute(text(query))
                rows = result.fetchall()

                return [
                    {
                        "path_id": row[0],
                        "tenant_id": row[1],
                        "virtual_path": row[2],
                        "backend_id": row[3],
                        "file_type": row[4],
                        "size_bytes": row[5],
                        "created_at": row[6],
                        "updated_at": row[7],
                        "status": json.loads(row[8]) if row[8] else None,
                        "worker_id": json.loads(row[9]) if row[9] else None,
                        "started_at": json.loads(row[10]) if row[10] else None,
                    }
                    for row in rows
                ]
        except Exception as e:
            raise MetadataError(f"Failed to get in-progress work: {e}") from e

    def get_work_by_priority(self, limit: int | None = None) -> builtins.list[dict[str, Any]]:
        """Get all work items ordered by priority.

        Uses the work_by_priority SQL view.

        Args:
            limit: Optional limit on number of results

        Returns:
            List of work item dicts
        """
        try:
            with self.SessionLocal() as session:
                query = "SELECT * FROM work_by_priority"
                if limit:
                    query += f" LIMIT {limit}"

                result = session.execute(text(query))
                rows = result.fetchall()

                return [
                    {
                        "path_id": row[0],
                        "tenant_id": row[1],
                        "virtual_path": row[2],
                        "backend_id": row[3],
                        "file_type": row[4],
                        "size_bytes": row[5],
                        "created_at": row[6],
                        "updated_at": row[7],
                        "status": json.loads(row[8]) if row[8] else None,
                        "priority": json.loads(row[9]) if row[9] else None,
                        "tags": json.loads(row[10]) if row[10] else None,
                    }
                    for row in rows
                ]
        except Exception as e:
            raise MetadataError(f"Failed to get work by priority: {e}") from e

    # Version tracking methods (v0.3.5)

    def get_version(self, path: str, version: int) -> FileMetadata | None:
        """Get a specific version of a file.

        Retrieves file metadata for a specific version from version history.
        The content_hash in the returned metadata can be used to fetch the
        actual content from CAS storage.

        Args:
            path: Virtual path
            version: Version number to retrieve

        Returns:
            FileMetadata for the specified version, or None if not found

        Example:
            >>> # Get version 2 of a file
            >>> metadata = store.get_version("/workspace/data.txt", version=2)
            >>> if metadata:
            ...     content_hash = metadata.etag
            ...     # Use content_hash to fetch from CAS
        """
        try:
            with self.SessionLocal() as session:
                # Get the file's path_id
                path_stmt = select(FilePathModel.path_id).where(
                    FilePathModel.virtual_path == path,
                    FilePathModel.deleted_at.is_(None),
                )
                path_id = session.scalar(path_stmt)

                if not path_id:
                    return None

                # Get the version from history
                version_stmt = select(VersionHistoryModel).where(
                    VersionHistoryModel.resource_type == "file",
                    VersionHistoryModel.resource_id == path_id,
                    VersionHistoryModel.version_number == version,
                )
                version_entry = session.scalar(version_stmt)

                if not version_entry:
                    return None

                # Build FileMetadata from version entry
                # Note: We don't have backend info in version history, so use current file's backend
                file_stmt = select(FilePathModel).where(FilePathModel.path_id == path_id)
                file_path = session.scalar(file_stmt)

                if not file_path:
                    return None

                return FileMetadata(
                    path=file_path.virtual_path,
                    backend_name=file_path.backend_id,
                    physical_path=version_entry.content_hash,  # CAS: hash is the physical path
                    size=version_entry.size_bytes,
                    etag=version_entry.content_hash,
                    mime_type=version_entry.mime_type,
                    created_at=version_entry.created_at,
                    modified_at=version_entry.created_at,
                    version=version_entry.version_number,
                    owner=file_path.owner,
                    group=file_path.group,
                    mode=file_path.mode,
                )
        except Exception as e:
            raise MetadataError(f"Failed to get version {version}: {e}", path=path) from e

    def list_versions(self, path: str) -> builtins.list[dict[str, Any]]:
        """List all versions of a file.

        Returns version history with metadata for each version.

        Args:
            path: Virtual path

        Returns:
            List of version info dicts ordered by version number (newest first)

        Example:
            >>> versions = store.list_versions("/workspace/SKILL.md")
            >>> for v in versions:
            ...     print(f"v{v['version']}: {v['size']} bytes, {v['created_at']}")
        """
        try:
            with self.SessionLocal() as session:
                # Get the file's path_id
                path_stmt = select(FilePathModel.path_id).where(
                    FilePathModel.virtual_path == path,
                    FilePathModel.deleted_at.is_(None),
                )
                path_id = session.scalar(path_stmt)

                if not path_id:
                    return []

                # Get all versions
                versions_stmt = (
                    select(VersionHistoryModel)
                    .where(
                        VersionHistoryModel.resource_type == "file",
                        VersionHistoryModel.resource_id == path_id,
                    )
                    .order_by(VersionHistoryModel.version_number.desc())
                )

                versions = []
                for v in session.scalars(versions_stmt):
                    versions.append(
                        {
                            "version": v.version_number,
                            "content_hash": v.content_hash,
                            "size": v.size_bytes,
                            "mime_type": v.mime_type,
                            "created_at": v.created_at,
                            "created_by": v.created_by,
                            "change_reason": v.change_reason,
                            "source_type": v.source_type,
                            "parent_version_id": v.parent_version_id,
                        }
                    )

                return versions
        except Exception as e:
            raise MetadataError(f"Failed to list versions: {e}", path=path) from e

    def rollback(self, path: str, version: int) -> None:
        """Rollback file to a previous version.

        Updates the file to point to an older version's content.
        Creates a new version entry marking this as a rollback.

        Args:
            path: Virtual path
            version: Version number to rollback to

        Example:
            >>> # Rollback to version 2
            >>> store.rollback("/workspace/data.txt", version=2)
        """
        try:
            with self.SessionLocal() as session:
                # Get current file
                file_stmt = select(FilePathModel).where(
                    FilePathModel.virtual_path == path,
                    FilePathModel.deleted_at.is_(None),
                )
                file_path = session.scalar(file_stmt)

                if not file_path:
                    raise MetadataError(f"File not found: {path}", path=path)

                # Get target version
                version_stmt = select(VersionHistoryModel).where(
                    VersionHistoryModel.resource_type == "file",
                    VersionHistoryModel.resource_id == file_path.path_id,
                    VersionHistoryModel.version_number == version,
                )
                target_version = session.scalar(version_stmt)

                if not target_version:
                    raise MetadataError(f"Version {version} not found for {path}", path=path)

                # Get current version entry for lineage
                current_version_stmt = select(VersionHistoryModel).where(
                    VersionHistoryModel.resource_type == "file",
                    VersionHistoryModel.resource_id == file_path.path_id,
                    VersionHistoryModel.version_number == file_path.current_version,
                )
                current_version_entry = session.scalar(current_version_stmt)

                # Update file to target version's content
                file_path.content_hash = target_version.content_hash
                file_path.size_bytes = target_version.size_bytes
                file_path.file_type = target_version.mime_type
                file_path.updated_at = datetime.now(UTC)
                file_path.current_version += 1  # Increment to new version

                # Create version history entry for the NEW version (rollback)
                rollback_version_entry = VersionHistoryModel(
                    version_id=str(uuid.uuid4()),
                    resource_type="file",
                    resource_id=file_path.path_id,
                    version_number=file_path.current_version,  # NEW version number
                    content_hash=target_version.content_hash,  # Points to old content
                    size_bytes=target_version.size_bytes,
                    mime_type=target_version.mime_type,
                    parent_version_id=current_version_entry.version_id
                    if current_version_entry
                    else None,
                    source_type="rollback",
                    change_reason=f"Rollback to version {version}",
                    created_at=datetime.now(UTC),
                )
                rollback_version_entry.validate()
                session.add(rollback_version_entry)

                session.commit()

            # Invalidate cache
            if self._cache_enabled and self._cache:
                self._cache.invalidate_path(path)
        except MetadataError:
            raise
        except Exception as e:
            raise MetadataError(f"Failed to rollback to version {version}: {e}", path=path) from e

    def get_version_diff(self, path: str, v1: int, v2: int) -> dict[str, Any]:
        """Get diff information between two versions.

        Returns metadata differences between versions.
        For content diff, retrieve both versions and compare.

        Args:
            path: Virtual path
            v1: First version number
            v2: Second version number

        Returns:
            Dict with diff information

        Example:
            >>> diff = store.get_version_diff("/workspace/file.txt", v1=1, v2=3)
            >>> print(f"Size changed: {diff['size_v1']} -> {diff['size_v2']}")
            >>> print(f"Content changed: {diff['content_changed']}")
        """
        try:
            with self.SessionLocal() as session:
                # Get path_id
                path_stmt = select(FilePathModel.path_id).where(
                    FilePathModel.virtual_path == path,
                    FilePathModel.deleted_at.is_(None),
                )
                path_id = session.scalar(path_stmt)

                if not path_id:
                    raise MetadataError(f"File not found: {path}", path=path)

                # Get both versions
                versions_stmt = select(VersionHistoryModel).where(
                    VersionHistoryModel.resource_type == "file",
                    VersionHistoryModel.resource_id == path_id,
                    VersionHistoryModel.version_number.in_([v1, v2]),
                )

                versions_dict = {v.version_number: v for v in session.scalars(versions_stmt)}

                if v1 not in versions_dict:
                    raise MetadataError(f"Version {v1} not found", path=path)
                if v2 not in versions_dict:
                    raise MetadataError(f"Version {v2} not found", path=path)

                version1 = versions_dict[v1]
                version2 = versions_dict[v2]

                return {
                    "path": path,
                    "v1": v1,
                    "v2": v2,
                    "content_hash_v1": version1.content_hash,
                    "content_hash_v2": version2.content_hash,
                    "content_changed": version1.content_hash != version2.content_hash,
                    "size_v1": version1.size_bytes,
                    "size_v2": version2.size_bytes,
                    "size_delta": version2.size_bytes - version1.size_bytes,
                    "created_at_v1": version1.created_at,
                    "created_at_v2": version2.created_at,
                    "mime_type_v1": version1.mime_type,
                    "mime_type_v2": version2.mime_type,
                }
        except MetadataError:
            raise
        except Exception as e:
            raise MetadataError(f"Failed to diff versions: {e}", path=path) from e

    def __enter__(self) -> SQLAlchemyMetadataStore:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Destructor to ensure database is closed."""
        from contextlib import suppress

        with suppress(Exception):
            self.close()
