"""Nexus CLI Skills Commands - Manage reusable AI agent skills.

The Skills System provides vendor-neutral skill management with:
- SKILL.md format with YAML frontmatter
- Three-tier hierarchy (agent > tenant > system)
- Dependency resolution with DAG and cycle detection
- Vendor-neutral export to .zip packages
- Skill lifecycle management (create, fork, publish)
- Usage analytics and governance
"""

from __future__ import annotations

import sys

import click
from rich.table import Table

from nexus.cli.utils import (
    BackendConfig,
    add_backend_options,
    console,
    get_filesystem,
    handle_error,
)


def register_commands(cli: click.Group) -> None:
    """Register skills commands with the main CLI group.

    Args:
        cli: The main Click group to register commands with
    """
    cli.add_command(skills)


@click.group(name="skills")
def skills() -> None:
    """Skills System - Manage reusable AI agent skills.

    The Skills System provides vendor-neutral skill management with:
    - SKILL.md format with YAML frontmatter
    - Three-tier hierarchy (agent > tenant > system)
    - Dependency resolution with DAG and cycle detection
    - Vendor-neutral export to .zip packages
    - Skill lifecycle management (create, fork, publish)
    - Usage analytics and governance

    Examples:
        nexus skills list
        nexus skills create my-skill --description "My custom skill"
        nexus skills fork analyze-code my-analyzer
        nexus skills publish my-skill
        nexus skills export my-skill --output ./my-skill.zip --format claude
    """
    pass


@skills.command(name="list")
@click.option("--tenant", is_flag=True, help="Show tenant-wide skills")
@click.option("--system", is_flag=True, help="Show system skills")
@click.option("--tier", type=click.Choice(["agent", "tenant", "system"]), help="Filter by tier")
@add_backend_options
def skills_list(
    tenant: bool,
    system: bool,
    tier: str | None,
    backend_config: BackendConfig,
) -> None:
    """List all skills.

    Examples:
        nexus skills list
        nexus skills list --tenant
        nexus skills list --system
        nexus skills list --tier agent
    """
    try:
        import asyncio

        from nexus.skills import SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)

        # Determine tier filter
        if tier:
            tier_filter = tier
        elif tenant:
            tier_filter = "tenant"
        elif system:
            tier_filter = "system"
        else:
            tier_filter = None

        registry = SkillRegistry(nx)

        async def list_skills_async() -> None:
            # Discover skills
            await registry.discover()

            # Get skills list with metadata
            skills_metadata_raw = registry.list_skills(tier=tier_filter, include_metadata=True)

            # Type hint the return value
            from nexus.skills.models import SkillMetadata

            skills_metadata: list[SkillMetadata] = skills_metadata_raw  # type: ignore[assignment]

            if not skills_metadata:
                console.print("[yellow]No skills found[/yellow]")
                return

            # Display skills in table
            table = Table(title=f"Skills ({len(skills_metadata)} found)")
            table.add_column("Name", style="cyan", no_wrap=False)
            table.add_column("Description", style="green")
            table.add_column("Version", style="yellow")
            table.add_column("Tier", style="magenta")

            for metadata in skills_metadata:
                table.add_row(
                    metadata.name,
                    metadata.description or "N/A",
                    metadata.version or "N/A",
                    metadata.tier or "N/A",
                )

            console.print(table)

        asyncio.run(list_skills_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="create")
@click.argument("name", type=str)
@click.option("--description", required=True, help="Skill description")
@click.option("--template", default="basic", help="Template to use (basic, data-analysis, etc.)")
@click.option(
    "--tier", type=click.Choice(["agent", "tenant", "system"]), default="agent", help="Target tier"
)
@click.option("--author", help="Author name")
@add_backend_options
def skills_create(
    name: str,
    description: str,
    template: str,
    tier: str,
    author: str | None,
    backend_config: BackendConfig,
) -> None:
    """Create a new skill from template.

    Examples:
        nexus skills create my-skill --description "My custom skill"
        nexus skills create data-viz --description "Data visualization" --template data-analysis
        nexus skills create analyzer --description "Code analyzer" --author Alice
    """
    try:
        import asyncio

        from nexus.skills import SkillManager, SkillRegistry

        # Get filesystem with permission enforcement disabled for skills operations
        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        manager = SkillManager(nx, registry)

        async def create_skill_async() -> None:
            skill_path = await manager.create_skill(
                name=name,
                description=description,
                template=template,
                tier=tier,
                author=author,
            )

            console.print(f"[green]✓[/green] Created skill [cyan]{name}[/cyan]")
            console.print(f"  Path: [dim]{skill_path}[/dim]")
            console.print(f"  Tier: [yellow]{tier}[/yellow]")
            console.print(f"  Template: [yellow]{template}[/yellow]")

        asyncio.run(create_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="fork")
@click.argument("source_skill", type=str)
@click.argument("target_skill", type=str)
@click.option(
    "--tier", type=click.Choice(["agent", "tenant", "system"]), default="agent", help="Target tier"
)
@click.option("--author", help="Author name for the fork")
@add_backend_options
def skills_fork(
    source_skill: str,
    target_skill: str,
    tier: str,
    author: str | None,
    backend_config: BackendConfig,
) -> None:
    """Fork an existing skill.

    Examples:
        nexus skills fork analyze-code my-analyzer
        nexus skills fork data-analysis custom-analysis --author Bob
    """
    try:
        import asyncio

        from nexus.skills import SkillManager, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        manager = SkillManager(nx, registry)

        async def fork_skill_async() -> None:
            await registry.discover()

            forked_path = await manager.fork_skill(
                source_name=source_skill,
                target_name=target_skill,
                tier=tier,
                author=author,
            )

            console.print(
                f"[green]✓[/green] Forked skill [cyan]{source_skill}[/cyan] → [cyan]{target_skill}[/cyan]"
            )
            console.print(f"  Path: [dim]{forked_path}[/dim]")
            console.print(f"  Tier: [yellow]{tier}[/yellow]")

        asyncio.run(fork_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="publish")
@click.argument("skill_name", type=str)
@click.option(
    "--from-tier",
    type=click.Choice(["agent", "tenant", "system"]),
    default="agent",
    help="Source tier",
)
@click.option(
    "--to-tier",
    type=click.Choice(["agent", "tenant", "system"]),
    default="tenant",
    help="Target tier",
)
@add_backend_options
def skills_publish(
    skill_name: str,
    from_tier: str,
    to_tier: str,
    backend_config: BackendConfig,
) -> None:
    """Publish skill to tenant or system library.

    Examples:
        nexus skills publish my-skill
        nexus skills publish shared-skill --from-tier tenant --to-tier system
    """
    try:
        import asyncio

        from nexus.skills import SkillManager, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        manager = SkillManager(nx, registry)

        async def publish_skill_async() -> None:
            published_path = await manager.publish_skill(
                name=skill_name,
                source_tier=from_tier,
                target_tier=to_tier,
            )

            console.print(f"[green]✓[/green] Published skill [cyan]{skill_name}[/cyan]")
            console.print(f"  From: [yellow]{from_tier}[/yellow] → To: [yellow]{to_tier}[/yellow]")
            console.print(f"  Path: [dim]{published_path}[/dim]")

        asyncio.run(publish_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="search")
@click.argument("query", type=str)
@click.option("--tier", type=click.Choice(["agent", "tenant", "system"]), help="Filter by tier")
@click.option("--limit", default=10, type=int, help="Maximum results")
@add_backend_options
def skills_search(
    query: str,
    tier: str | None,
    limit: int,
    backend_config: BackendConfig,
) -> None:
    """Search skills by description.

    Examples:
        nexus skills search "data analysis"
        nexus skills search "code" --tier tenant --limit 5
    """
    try:
        import asyncio

        from nexus.skills import SkillManager, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        manager = SkillManager(nx, registry)

        async def search_skills_async() -> None:
            results = await manager.search_skills(query=query, tier=tier, limit=limit)

            if not results:
                console.print(f"[yellow]No skills match query:[/yellow] {query}")
                return

            console.print(
                f"[green]Found {len(results)} skills matching[/green] [cyan]{query}[/cyan]\n"
            )

            table = Table(title=f"Search Results for '{query}'")
            table.add_column("Skill Name", style="cyan")
            table.add_column("Relevance Score", justify="right", style="yellow")

            for skill_name, score in results:
                table.add_row(skill_name, f"{score:.2f}")

            console.print(table)

        asyncio.run(search_skills_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="info")
@click.argument("skill_name", type=str)
@add_backend_options
def skills_info(
    skill_name: str,
    backend_config: BackendConfig,
) -> None:
    """Show detailed skill information.

    Examples:
        nexus skills info analyze-code
        nexus skills info data-analysis
    """
    try:
        import asyncio

        from nexus.skills import SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)

        async def show_info_async() -> None:
            await registry.discover()

            # Get metadata first
            metadata = registry.get_metadata(skill_name)

            # Load full skill to ensure it exists and cache it
            await registry.get_skill(skill_name)

            # Display skill information
            table = Table(title=f"Skill Information: {skill_name}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Name", metadata.name)
            table.add_row("Description", metadata.description or "N/A")
            table.add_row("Version", metadata.version or "N/A")
            table.add_row("Author", metadata.author or "N/A")
            table.add_row("Tier", metadata.tier or "N/A")
            table.add_row("File Path", metadata.file_path or "N/A")

            if metadata.created_at:
                table.add_row("Created", metadata.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            if metadata.modified_at:
                table.add_row("Modified", metadata.modified_at.strftime("%Y-%m-%d %H:%M:%S"))

            # Show dependencies
            if metadata.requires:
                deps_str = ", ".join(metadata.requires)
                table.add_row("Dependencies", deps_str)

            console.print(table)

            # Show dependencies resolved
            if metadata.requires:
                console.print("\n[bold]Dependency Resolution:[/bold]")
                resolved = await registry.resolve_dependencies(skill_name)
                console.print(f"  Resolved order: [cyan]{' → '.join(resolved)}[/cyan]")

        asyncio.run(show_info_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="export")
@click.argument("skill_name", type=str)
@click.option("--output", "-o", type=click.Path(), required=True, help="Output .zip file path")
@click.option(
    "--format",
    type=click.Choice(["generic", "claude", "openai"]),
    default="generic",
    help="Export format",
)
@click.option("--no-deps", is_flag=True, help="Exclude dependencies from export")
@add_backend_options
def skills_export(
    skill_name: str,
    output: str,
    format: str,
    no_deps: bool,
    backend_config: BackendConfig,
) -> None:
    """Export skill to .zip package.

    Examples:
        nexus skills export my-skill --output ./my-skill.zip
        nexus skills export analyze-code --output ./export.zip --format claude
        nexus skills export my-skill --output ./export.zip --no-deps
    """
    try:
        import asyncio

        from nexus.skills import SkillExporter, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        exporter = SkillExporter(registry)

        async def export_skill_async() -> None:
            await registry.discover()

            include_deps = not no_deps

            with console.status(
                f"[yellow]Exporting skill {skill_name}...[/yellow]", spinner="dots"
            ):
                await exporter.export_skill(
                    name=skill_name,
                    output_path=output,
                    format=format,
                    include_dependencies=include_deps,
                )

            console.print(f"[green]✓[/green] Exported skill [cyan]{skill_name}[/cyan]")
            console.print(f"  Output: [cyan]{output}[/cyan]")
            console.print(f"  Format: [yellow]{format}[/yellow]")
            console.print(
                f"  Dependencies: [yellow]{'Included' if include_deps else 'Excluded'}[/yellow]"
            )

        asyncio.run(export_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="validate")
@click.argument("skill_name", type=str)
@click.option(
    "--format",
    type=click.Choice(["generic", "claude", "openai"]),
    default="generic",
    help="Validation format",
)
@add_backend_options
def skills_validate(
    skill_name: str,
    format: str,
    backend_config: BackendConfig,
) -> None:
    """Validate skill format and size limits.

    Examples:
        nexus skills validate my-skill
        nexus skills validate analyze-code --format claude
    """
    try:
        import asyncio

        from nexus.skills import SkillExporter, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        exporter = SkillExporter(registry)

        async def validate_skill_async() -> None:
            await registry.discover()

            valid, message, size_bytes = await exporter.validate_export(
                name=skill_name,
                format=format,
                include_dependencies=True,
            )

            def format_size(size: int) -> str:
                """Format size in human-readable format."""
                size_float = float(size)
                for unit in ["B", "KB", "MB", "GB"]:
                    if size_float < 1024.0:
                        return f"{size_float:.2f} {unit}"
                    size_float /= 1024.0
                return f"{size_float:.2f} TB"

            if valid:
                console.print(
                    f"[green]✓[/green] Skill [cyan]{skill_name}[/cyan] is valid for export"
                )
                console.print(f"  Format: [yellow]{format}[/yellow]")
                console.print(f"  Total size: [cyan]{format_size(size_bytes)}[/cyan]")
                console.print(f"  Message: [dim]{message}[/dim]")
            else:
                console.print(f"[red]✗[/red] Skill [cyan]{skill_name}[/cyan] validation failed")
                console.print(f"  Format: [yellow]{format}[/yellow]")
                console.print(f"  Total size: [cyan]{format_size(size_bytes)}[/cyan]")
                console.print(f"  Error: [red]{message}[/red]")
                sys.exit(1)

        asyncio.run(validate_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="size")
@click.argument("skill_name", type=str)
@click.option("--human", "-h", is_flag=True, help="Human-readable output")
@add_backend_options
def skills_size(
    skill_name: str,
    human: bool,
    backend_config: BackendConfig,
) -> None:
    """Calculate total size of skill and dependencies.

    Examples:
        nexus skills size my-skill
        nexus skills size analyze-code --human
    """
    try:
        import asyncio

        from nexus.skills import SkillExporter, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        exporter = SkillExporter(registry)

        async def calculate_size_async() -> None:
            await registry.discover()

            _, _, size_bytes = await exporter.validate_export(
                name=skill_name,
                format="generic",
                include_dependencies=True,
            )

            def format_size(size: int) -> str:
                """Format size in human-readable format."""
                if not human:
                    return f"{size:,} bytes"

                size_float = float(size)
                for unit in ["B", "KB", "MB", "GB"]:
                    if size_float < 1024.0:
                        return f"{size_float:.2f} {unit}"
                    size_float /= 1024.0
                return f"{size_float:.2f} TB"

            console.print(f"[bold cyan]Size of {skill_name} (with dependencies):[/bold cyan]")
            console.print(f"  Total size: [green]{format_size(size_bytes)}[/green]")

        asyncio.run(calculate_size_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="deps")
@click.argument("skill_name", type=str)
@click.option("--visual/--no-visual", default=True, help="Show visual tree (default: True)")
@add_backend_options
def skills_deps(
    skill_name: str,
    visual: bool,
    backend_config: BackendConfig,
) -> None:
    """Show skill dependencies as a visual tree.

    Examples:
        nexus skills deps my-skill
        nexus skills deps analyze-code --no-visual
    """
    try:
        import asyncio

        from nexus.skills import SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)

        async def show_deps_async() -> None:
            await registry.discover()

            # Get the skill to verify it exists
            skill = await registry.get_skill(skill_name)

            if visual:
                # Build visual dependency tree
                from rich.tree import Tree

                tree = Tree(f"[bold cyan]{skill_name}[/bold cyan]", guide_style="dim")

                async def add_dependencies(
                    parent_tree: Tree, skill_name: str, visited: set[str]
                ) -> None:
                    """Recursively add dependencies to tree."""
                    if skill_name in visited:
                        parent_tree.add(f"[dim]{skill_name} (circular reference)[/dim]")
                        return

                    visited.add(skill_name)

                    try:
                        skill_obj = await registry.get_skill(skill_name)
                        deps = skill_obj.metadata.requires or []

                        for dep in deps:
                            dep_metadata = registry.get_metadata(dep)
                            dep_desc = dep_metadata.description or "No description"

                            # Truncate description
                            if len(dep_desc) > 50:
                                dep_desc = dep_desc[:47] + "..."

                            dep_node = parent_tree.add(
                                f"[green]{dep}[/green] - [dim]{dep_desc}[/dim]"
                            )

                            # Recursively add dependencies
                            await add_dependencies(dep_node, dep, visited.copy())
                    except Exception as e:
                        parent_tree.add(f"[red]{skill_name} (error: {e})[/red]")

                # Add dependencies to the tree
                visited: set[str] = set()
                deps = skill.metadata.requires or []

                if not deps:
                    tree.add("[yellow]No dependencies[/yellow]")
                else:
                    for dep in deps:
                        dep_metadata = registry.get_metadata(dep)
                        dep_desc = dep_metadata.description or "No description"

                        if len(dep_desc) > 50:
                            dep_desc = dep_desc[:47] + "..."

                        dep_node = tree.add(f"[green]{dep}[/green] - [dim]{dep_desc}[/dim]")

                        # Recursively add sub-dependencies
                        await add_dependencies(dep_node, dep, visited.copy())

                console.print()
                console.print(tree)
                console.print()

                # Show total dependency count
                all_deps = await registry.resolve_dependencies(skill_name)
                total_deps = len(all_deps) - 1  # Exclude the skill itself
                console.print(f"[dim]Total dependencies: {total_deps}[/dim]")

            else:
                # Simple list format
                deps = await registry.resolve_dependencies(skill_name)

                console.print(f"\n[bold cyan]Dependencies for {skill_name}:[/bold cyan]")

                if len(deps) == 1:
                    console.print("  [yellow]No dependencies[/yellow]")
                else:
                    console.print("  [dim]Resolution order:[/dim]")
                    for i, dep in enumerate(deps):
                        if dep == skill_name:
                            console.print(f"  {i + 1}. [bold cyan]{dep}[/bold cyan] (self)")
                        else:
                            dep_metadata = registry.get_metadata(dep)
                            console.print(f"  {i + 1}. [green]{dep}[/green]")
                            if dep_metadata.description:
                                console.print(f"      [dim]{dep_metadata.description}[/dim]")

        asyncio.run(show_deps_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="diff")
@click.argument("skill1", type=str)
@click.argument("skill2", type=str)
@click.option("--context", "-c", default=3, type=int, help="Context lines (default: 3)")
@add_backend_options
def skills_diff(
    skill1: str,
    skill2: str,
    context: int,
    backend_config: BackendConfig,
) -> None:
    """Show differences between two skills.

    Examples:
        nexus skills diff my-skill-v1 my-skill-v2
        nexus skills diff analyze-code my-analyzer --context 5
    """
    try:
        import asyncio
        import difflib

        from rich.syntax import Syntax

        from nexus.skills import SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)

        async def show_diff_async() -> None:
            await registry.discover()

            # Load both skills
            skill_obj1 = await registry.get_skill(skill1)
            skill_obj2 = await registry.get_skill(skill2)

            # Reconstruct SKILL.md content for both
            from nexus.skills.exporter import SkillExporter

            exporter = SkillExporter(registry)

            content1 = exporter._reconstruct_skill_md(skill_obj1)
            content2 = exporter._reconstruct_skill_md(skill_obj2)

            # Generate unified diff
            diff = difflib.unified_diff(
                content1.splitlines(keepends=True),
                content2.splitlines(keepends=True),
                fromfile=f"{skill1}/SKILL.md",
                tofile=f"{skill2}/SKILL.md",
                n=context,
            )

            diff_text = "".join(diff)

            if not diff_text:
                console.print(f"[yellow]No differences between {skill1} and {skill2}[/yellow]")
                return

            # Display diff with syntax highlighting
            console.print(f"\n[bold]Diff: {skill1} vs {skill2}[/bold]\n")

            # Use Syntax for colored diff output
            syntax = Syntax(
                diff_text,
                "diff",
                theme="monokai",
                line_numbers=True,
                word_wrap=False,
            )
            console.print(syntax)

            # Show summary statistics
            lines = diff_text.split("\n")
            additions = sum(
                1 for line in lines if line.startswith("+") and not line.startswith("+++")
            )
            deletions = sum(
                1 for line in lines if line.startswith("-") and not line.startswith("---")
            )

            console.print(
                f"\n[dim]Summary: [green]+{additions}[/green] additions, [red]-{deletions}[/red] deletions[/dim]"
            )

        asyncio.run(show_diff_async())
        nx.close()

    except Exception as e:
        handle_error(e)
