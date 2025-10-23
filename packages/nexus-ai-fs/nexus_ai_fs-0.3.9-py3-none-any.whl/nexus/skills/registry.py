"""Skill registry with progressive disclosure and lazy loading."""

import logging
from collections import defaultdict
from pathlib import Path

from nexus.core.exceptions import ValidationError
from nexus.skills.models import Skill, SkillMetadata
from nexus.skills.parser import SkillParseError, SkillParser
from nexus.skills.protocols import NexusFilesystem

logger = logging.getLogger(__name__)


class SkillNotFoundError(ValidationError):
    """Raised when a skill is not found in the registry."""

    pass


class SkillDependencyError(ValidationError):
    """Raised when skill dependencies cannot be resolved."""

    pass


class SkillRegistry:
    """Registry for managing skills with progressive disclosure and lazy loading.

    Features:
    - Progressive disclosure: Load metadata during discovery, full content on-demand
    - Lazy loading: Only load skills when actually needed
    - Three-tier hierarchy: agent > tenant > system (priority order)
    - Dependency resolution: Automatic DAG resolution with cycle detection
    - Caching: In-memory cache for loaded skills

    Example:
        >>> from nexus import connect
        >>> nx = connect()
        >>> registry = SkillRegistry(nx)
        >>> await registry.discover()  # Loads metadata only
        >>> skill = await registry.get_skill("analyze-code")  # Loads full content
        >>> deps = await registry.resolve_dependencies("analyze-code")
    """

    # Tier directories (relative to root)
    TIER_PATHS = {
        "agent": "/workspace/.nexus/skills/",
        "tenant": "/shared/skills/",
        "system": "/system/skills/",
    }

    # Tier priority (higher = checked first)
    TIER_PRIORITY = {
        "agent": 3,
        "tenant": 2,
        "system": 1,
    }

    def __init__(self, filesystem: NexusFilesystem | None = None):
        """Initialize skill registry.

        Args:
            filesystem: Optional filesystem instance (defaults to local FS)
        """
        self._filesystem = filesystem
        self._parser = SkillParser()

        # Metadata index: skill_name -> SkillMetadata
        # Loaded during discovery (lightweight)
        self._metadata_index: dict[str, SkillMetadata] = {}

        # Full skill cache: skill_name -> Skill
        # Loaded on-demand (heavy)
        self._skill_cache: dict[str, Skill] = {}

        # Tier index: tier -> list of skill names
        self._tier_index: dict[str, list[str]] = defaultdict(list)

    async def discover(self, tiers: list[str] | None = None) -> int:
        """Discover skills from filesystem (metadata only).

        Progressive disclosure: Only loads metadata during discovery.
        Full content is loaded on-demand when get_skill() is called.

        Args:
            tiers: Optional list of tiers to discover from (default: all)

        Returns:
            Number of skills discovered

        Example:
            >>> registry = SkillRegistry(nx)
            >>> count = await registry.discover()  # Discover from all tiers
            >>> count = await registry.discover(["agent", "tenant"])  # Specific tiers
        """
        if tiers is None:
            tiers = list(self.TIER_PATHS.keys())

        discovered_count = 0

        # Discover from each tier (in priority order)
        for tier in sorted(tiers, key=lambda t: self.TIER_PRIORITY.get(t, 0), reverse=True):
            tier_path = self.TIER_PATHS.get(tier)
            if not tier_path:
                logger.warning(f"Unknown tier: {tier}")
                continue

            count = await self._discover_tier(tier, tier_path)
            discovered_count += count

        logger.info(f"Discovered {discovered_count} skills from {len(tiers)} tiers")
        return discovered_count

    async def _discover_tier(self, tier: str, tier_path: str) -> int:
        """Discover skills from a single tier.

        Args:
            tier: Tier name (agent, tenant, system)
            tier_path: Path to tier directory

        Returns:
            Number of skills discovered from this tier
        """
        if self._filesystem:
            # Use NexusFS
            # Note: In NexusFS, directories may not be explicitly created,
            # so we check is_directory() first (which works for implicit dirs)
            # and fall back to trying to list the directory
            try:
                is_dir = self._filesystem.is_directory(tier_path)
            except Exception:
                # Directory check failed, try to list anyway
                is_dir = False

            if not is_dir:
                # Try to list the directory - if it has files, it exists
                try:
                    # list() returns list[str] when details=False
                    files_raw = self._filesystem.list(tier_path, recursive=True, details=False)
                    files_list: list[str] = files_raw  # type: ignore[assignment]
                    if not files_list:
                        logger.debug(f"Tier path has no files: {tier_path}")
                        return 0
                    skill_files = [
                        f
                        for f in files_list
                        if isinstance(f, str) and Path(f).name.upper() == "SKILL.MD"
                    ]
                except Exception as e:
                    # Directory doesn't exist or can't be listed
                    logger.debug(f"Tier path does not exist or cannot be listed: {tier_path} ({e})")
                    return 0
            else:
                # Directory exists, list it
                try:
                    # list() returns list[str] when details=False
                    files_raw = self._filesystem.list(tier_path, recursive=True, details=False)
                    str_files: list[str] = files_raw  # type: ignore[assignment]
                    skill_files = [
                        f
                        for f in str_files
                        if isinstance(f, str) and Path(f).name.upper() == "SKILL.MD"
                    ]
                except Exception as e:
                    logger.error(f"Failed to list tier directory {tier_path}: {e}")
                    return 0
        else:
            # Use local filesystem
            tier_dir = Path(tier_path)
            if not tier_dir.exists():
                logger.debug(f"Tier path does not exist: {tier_path}")
                return 0

            if not tier_dir.is_dir():
                logger.warning(f"Tier path is not a directory: {tier_path}")
                return 0

            # Find all SKILL.md files
            skill_files = [str(p) for p in tier_dir.rglob("SKILL.md")]

        count = 0
        for skill_file in skill_files:
            try:
                # Parse metadata only (progressive disclosure)
                metadata = self._parse_metadata(skill_file, tier)

                # Index by name (tier priority: agent > tenant > system)
                existing = self._metadata_index.get(metadata.name)
                if existing:
                    # Check tier priority
                    existing_priority = self.TIER_PRIORITY.get(existing.tier or "", 0)
                    new_priority = self.TIER_PRIORITY.get(tier, 0)

                    if new_priority <= existing_priority:
                        logger.debug(
                            f"Skipping skill '{metadata.name}' from {tier} "
                            f"(already loaded from {existing.tier})"
                        )
                        continue

                    logger.info(
                        f"Overriding skill '{metadata.name}' from {existing.tier} "
                        f"with {tier} version"
                    )

                self._metadata_index[metadata.name] = metadata
                self._tier_index[tier].append(metadata.name)
                count += 1

                logger.debug(f"Discovered skill '{metadata.name}' from {tier}: {skill_file}")

            except SkillParseError as e:
                logger.warning(f"Failed to parse skill {skill_file}: {e}")
                continue

        return count

    def _parse_metadata(self, file_path: str, tier: str) -> SkillMetadata:
        """Parse skill metadata from file.

        Args:
            file_path: Path to SKILL.md file
            tier: Tier name

        Returns:
            SkillMetadata object
        """
        if self._filesystem:
            # Use NexusFS to read content and parse directly
            raw_content = self._filesystem.read(file_path)
            # Type narrowing: when return_metadata=False (default), result is bytes
            assert isinstance(raw_content, bytes), "Expected bytes from read()"
            content = raw_content.decode("utf-8")
            return self._parser.parse_metadata_from_content(content, file_path, tier)
        else:
            # Use local filesystem
            return self._parser.parse_metadata_only(file_path, tier)

    async def get_skill(self, name: str, load_dependencies: bool = False) -> Skill:
        """Get a skill by name (loads full content on-demand).

        Lazy loading: Loads full content only when requested.

        Args:
            name: Skill name
            load_dependencies: If True, also load all dependencies

        Returns:
            Complete Skill object (metadata + content)

        Raises:
            SkillNotFoundError: If skill not found

        Example:
            >>> skill = await registry.get_skill("analyze-code")
            >>> print(skill.content)  # Full markdown content
        """
        # Check cache first
        if name in self._skill_cache:
            logger.debug(f"Skill '{name}' loaded from cache")
            return self._skill_cache[name]

        # Check metadata index
        if name not in self._metadata_index:
            raise SkillNotFoundError(f"Skill not found: {name}")

        metadata = self._metadata_index[name]

        # Load full content
        try:
            if self._filesystem:
                raw_content = self._filesystem.read(metadata.file_path or "")
                # Type narrowing: when return_metadata=False (default), result is bytes
                assert isinstance(raw_content, bytes), "Expected bytes from read()"
                content = raw_content.decode("utf-8")
                skill = self._parser.parse_content(content, metadata.file_path, metadata.tier)
            else:
                skill = self._parser.parse_file(metadata.file_path or "", metadata.tier)

            # Cache the loaded skill
            self._skill_cache[name] = skill

            logger.debug(f"Loaded skill '{name}' from {metadata.file_path}")

            # Optionally load dependencies
            if load_dependencies:
                await self._load_dependencies(skill)

            return skill

        except Exception as e:
            raise SkillNotFoundError(
                f"Failed to load skill '{name}': {e}", path=metadata.file_path
            ) from e

    async def _load_dependencies(self, skill: Skill) -> None:
        """Load all dependencies for a skill.

        Args:
            skill: Skill to load dependencies for
        """
        for dep_name in skill.metadata.requires:
            if dep_name not in self._skill_cache:
                try:
                    await self.get_skill(dep_name, load_dependencies=True)
                except SkillNotFoundError:
                    logger.warning(
                        f"Dependency '{dep_name}' not found for skill '{skill.metadata.name}'"
                    )

    async def resolve_dependencies(self, name: str) -> list[str]:
        """Resolve all dependencies for a skill (DAG resolution).

        Returns skills in dependency order (dependencies first).

        Args:
            name: Skill name

        Returns:
            List of skill names in dependency order

        Raises:
            SkillNotFoundError: If skill or dependency not found
            SkillDependencyError: If circular dependency detected

        Example:
            >>> deps = await registry.resolve_dependencies("analyze-code")
            >>> # ['base-parser', 'ast-analyzer', 'analyze-code']
        """
        visited: set[str] = set()
        result: list[str] = []
        stack: set[str] = set()  # For cycle detection

        async def visit(skill_name: str) -> None:
            if skill_name in stack:
                # Circular dependency
                cycle = " -> ".join(list(stack) + [skill_name])
                raise SkillDependencyError(
                    f"Circular dependency detected: {cycle}",
                    path=skill_name,
                )

            if skill_name in visited:
                return

            # Check if skill exists
            if skill_name not in self._metadata_index:
                raise SkillNotFoundError(f"Skill not found: {skill_name}")

            metadata = self._metadata_index[skill_name]

            # Mark as visiting (for cycle detection)
            stack.add(skill_name)

            # Visit dependencies first
            for dep in metadata.requires:
                await visit(dep)

            # Mark as visited
            stack.remove(skill_name)
            visited.add(skill_name)
            result.append(skill_name)

        await visit(name)
        return result

    def list_skills(
        self, tier: str | None = None, include_metadata: bool = False
    ) -> list[str] | list[SkillMetadata]:
        """List available skills.

        Args:
            tier: Optional tier filter (agent, tenant, system)
            include_metadata: If True, return SkillMetadata instead of names

        Returns:
            List of skill names or SkillMetadata objects

        Example:
            >>> names = registry.list_skills()  # All skills
            >>> names = registry.list_skills(tier="agent")  # Agent skills only
            >>> metadata = registry.list_skills(include_metadata=True)
        """
        skill_names = self._tier_index.get(tier, []) if tier else list(self._metadata_index.keys())

        if include_metadata:
            return [self._metadata_index[name] for name in skill_names]
        else:
            return skill_names

    def get_metadata(self, name: str) -> SkillMetadata:
        """Get skill metadata without loading full content.

        Args:
            name: Skill name

        Returns:
            SkillMetadata object

        Raises:
            SkillNotFoundError: If skill not found

        Example:
            >>> metadata = registry.get_metadata("analyze-code")
            >>> print(metadata.description)  # Quick access to metadata
        """
        if name not in self._metadata_index:
            raise SkillNotFoundError(f"Skill not found: {name}")

        return self._metadata_index[name]

    def clear_cache(self) -> None:
        """Clear the skill cache.

        Useful for testing or reloading skills after changes.
        Metadata index is preserved.
        """
        self._skill_cache.clear()
        logger.info("Cleared skill cache")

    def clear(self) -> None:
        """Clear all registered skills and caches.

        Useful for testing or complete reloading.
        """
        self._metadata_index.clear()
        self._skill_cache.clear()
        self._tier_index.clear()
        logger.info("Cleared all skills from registry")

    def __repr__(self) -> str:
        """String representation of the registry."""
        skill_count = len(self._metadata_index)
        cached_count = len(self._skill_cache)
        return (
            f"SkillRegistry(skills={skill_count}, "
            f"cached={cached_count}, "
            f"tiers={list(self._tier_index.keys())})"
        )
