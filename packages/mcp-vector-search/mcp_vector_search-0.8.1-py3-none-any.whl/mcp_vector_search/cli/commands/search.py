"""Search command for MCP Vector Search CLI."""

import asyncio
from pathlib import Path

import typer
from loguru import logger

from ...core.database import ChromaVectorDatabase
from ...core.embeddings import create_embedding_function
from ...core.exceptions import ProjectNotFoundError
from ...core.indexer import SemanticIndexer
from ...core.project import ProjectManager
from ...core.search import SemanticSearchEngine
from ..didyoumean import create_enhanced_typer
from ..output import (
    print_error,
    print_info,
    print_search_results,
    print_tip,
)

# Create search subcommand app with "did you mean" functionality
search_app = create_enhanced_typer(
    help="🔍 Search code semantically",
    invoke_without_command=True,
)


# Define search_main as the callback for the search command
# This makes `mcp-vector-search search "query"` work as main search
# and `mcp-vector-search search SUBCOMMAND` work for subcommands


@search_app.callback(invoke_without_command=True)
def search_main(
    ctx: typer.Context,
    query: str | None = typer.Argument(
        None, help="Search query or file path (for --similar)"
    ),
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Project root directory (auto-detected if not specified)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        rich_help_panel="🔧 Global Options",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of results to return",
        min=1,
        max=100,
        rich_help_panel="📊 Result Options",
    ),
    files: str | None = typer.Option(
        None,
        "--files",
        "-f",
        help="Filter by file patterns (e.g., '*.py' or 'src/*.js')",
        rich_help_panel="🔍 Filters",
    ),
    language: str | None = typer.Option(
        None,
        "--language",
        help="Filter by programming language (python, javascript, typescript)",
        rich_help_panel="🔍 Filters",
    ),
    function_name: str | None = typer.Option(
        None,
        "--function",
        help="Filter by function name",
        rich_help_panel="🔍 Filters",
    ),
    class_name: str | None = typer.Option(
        None,
        "--class",
        help="Filter by class name",
        rich_help_panel="🔍 Filters",
    ),
    similarity_threshold: float | None = typer.Option(
        None,
        "--threshold",
        "-t",
        help="Minimum similarity threshold (0.0 to 1.0)",
        min=0.0,
        max=1.0,
        rich_help_panel="🎯 Search Options",
    ),
    similar: bool = typer.Option(
        False,
        "--similar",
        help="Find code similar to the query (treats query as file path)",
        rich_help_panel="🎯 Search Options",
    ),
    context: bool = typer.Option(
        False,
        "--context",
        help="Search for code based on contextual description",
        rich_help_panel="🎯 Search Options",
    ),
    focus: str | None = typer.Option(
        None,
        "--focus",
        help="Focus areas for context search (comma-separated)",
        rich_help_panel="🎯 Search Options",
    ),
    no_content: bool = typer.Option(
        False,
        "--no-content",
        help="Don't show code content in results",
        rich_help_panel="📊 Result Options",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results in JSON format",
        rich_help_panel="📊 Result Options",
    ),
    export_format: str | None = typer.Option(
        None,
        "--export",
        help="Export results to file (json, csv, markdown, summary)",
        rich_help_panel="💾 Export Options",
    ),
    export_path: Path | None = typer.Option(
        None,
        "--export-path",
        help="Custom export file path",
        rich_help_panel="💾 Export Options",
    ),
) -> None:
    """🔍 Search your codebase semantically.

    Performs vector similarity search across your indexed code to find relevant
    functions, classes, and patterns based on semantic meaning, not just keywords.

    [bold cyan]Basic Search Examples:[/bold cyan]

    [green]Simple semantic search:[/green]
        $ mcp-vector-search search "authentication middleware"

    [green]Search with language filter:[/green]
        $ mcp-vector-search search "database connection" --language python

    [green]Limit results:[/green]
        $ mcp-vector-search search "error handling" --limit 5

    [bold cyan]Advanced Search:[/bold cyan]

    [green]Filter by file pattern:[/green]
        $ mcp-vector-search search "validation" --files "src/*.py"

    [green]Find similar code:[/green]
        $ mcp-vector-search search "src/auth.py" --similar

    [green]Context-based search:[/green]
        $ mcp-vector-search search "implement rate limiting" --context --focus security

    [bold cyan]Export Results:[/bold cyan]

    [green]Export to JSON:[/green]
        $ mcp-vector-search search "api endpoints" --export json

    [green]Export to markdown:[/green]
        $ mcp-vector-search search "utils" --export markdown

    [dim]💡 Tip: Use quotes for multi-word queries. Adjust --threshold for more/fewer results.[/dim]
    """
    # If no query provided and no subcommand invoked, exit (show help)
    if query is None:
        if ctx.invoked_subcommand is None:
            # No query and no subcommand - show help
            raise typer.Exit()
        else:
            # A subcommand was invoked - let it handle the request
            return

    try:
        project_root = project_root or ctx.obj.get("project_root") or Path.cwd()

        # Validate mutually exclusive options
        if similar and context:
            print_error("Cannot use both --similar and --context flags together")
            raise typer.Exit(1)

        # Route to appropriate search function
        if similar:
            # Similar search - treat query as file path
            file_path = Path(query)
            if not file_path.exists():
                print_error(f"File not found: {query}")
                raise typer.Exit(1)

            asyncio.run(
                run_similar_search(
                    project_root=project_root,
                    file_path=file_path,
                    function_name=function_name,
                    limit=limit,
                    similarity_threshold=similarity_threshold,
                    json_output=json_output,
                )
            )
        elif context:
            # Context search
            focus_areas = None
            if focus:
                focus_areas = [area.strip() for area in focus.split(",")]

            asyncio.run(
                run_context_search(
                    project_root=project_root,
                    description=query,
                    focus_areas=focus_areas,
                    limit=limit,
                    json_output=json_output,
                )
            )
        else:
            # Default semantic search
            asyncio.run(
                run_search(
                    project_root=project_root,
                    query=query,
                    limit=limit,
                    files=files,
                    language=language,
                    function_name=function_name,
                    class_name=class_name,
                    similarity_threshold=similarity_threshold,
                    show_content=not no_content,
                    json_output=json_output,
                    export_format=export_format,
                    export_path=export_path,
                )
            )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        print_error(f"Search failed: {e}")
        raise typer.Exit(1)


async def run_search(
    project_root: Path,
    query: str,
    limit: int = 10,
    files: str | None = None,
    language: str | None = None,
    function_name: str | None = None,
    class_name: str | None = None,
    similarity_threshold: float | None = None,
    show_content: bool = True,
    json_output: bool = False,
    export_format: str | None = None,
    export_path: Path | None = None,
) -> None:
    """Run semantic search."""
    # Load project configuration
    project_manager = ProjectManager(project_root)

    if not project_manager.is_initialized():
        raise ProjectNotFoundError(
            f"Project not initialized at {project_root}. Run 'mcp-vector-search init' first."
        )

    config = project_manager.load_config()

    # Setup database and search engine
    embedding_function, _ = create_embedding_function(config.embedding_model)
    database = ChromaVectorDatabase(
        persist_directory=config.index_path,
        embedding_function=embedding_function,
    )

    # Create indexer for version check
    indexer = SemanticIndexer(
        database=database,
        project_root=project_root,
        file_extensions=config.file_extensions,
    )

    # Check if reindex is needed due to version upgrade
    if config.auto_reindex_on_upgrade and indexer.needs_reindex_for_version():
        from ..output import console

        index_version = indexer.get_index_version()
        from ... import __version__

        if index_version:
            console.print(
                f"[yellow]⚠️  Index created with version {index_version} (current: {__version__})[/yellow]"
            )
        else:
            console.print(
                "[yellow]⚠️  Index version not found (legacy format detected)[/yellow]"
            )

        console.print(
            "[yellow]   Reindexing to take advantage of improvements...[/yellow]"
        )

        # Auto-reindex with progress
        try:
            indexed_count = await indexer.index_project(
                force_reindex=True, show_progress=False
            )
            console.print(
                f"[green]✓ Index updated to version {__version__} ({indexed_count} files reindexed)[/green]\n"
            )
        except Exception as e:
            console.print(f"[red]✗ Reindexing failed: {e}[/red]")
            console.print(
                "[yellow]  Continuing with existing index (may have outdated patterns)[/yellow]\n"
            )

    search_engine = SemanticSearchEngine(
        database=database,
        project_root=project_root,
        similarity_threshold=similarity_threshold or config.similarity_threshold,
    )

    # Build filters
    filters = {}
    if language:
        filters["language"] = language
    if function_name:
        filters["function_name"] = function_name
    if class_name:
        filters["class_name"] = class_name
    if files:
        # Simple file pattern matching (could be enhanced)
        filters["file_path"] = files

    try:
        async with database:
            results = await search_engine.search(
                query=query,
                limit=limit,
                filters=filters if filters else None,
                similarity_threshold=similarity_threshold,
                include_context=show_content,
            )

            # Handle export if requested
            if export_format:
                from ..export import SearchResultExporter, get_export_path

                exporter = SearchResultExporter()

                # Determine export path
                if export_path:
                    output_path = export_path
                else:
                    output_path = get_export_path(export_format, query, project_root)

                # Export based on format
                success = False
                if export_format == "json":
                    success = exporter.export_to_json(results, output_path, query)
                elif export_format == "csv":
                    success = exporter.export_to_csv(results, output_path, query)
                elif export_format == "markdown":
                    success = exporter.export_to_markdown(
                        results, output_path, query, show_content
                    )
                elif export_format == "summary":
                    success = exporter.export_summary_table(results, output_path, query)
                else:
                    from ..output import print_error

                    print_error(f"Unsupported export format: {export_format}")

                if not success:
                    return

            # Save to search history
            from ..history import SearchHistory

            history_manager = SearchHistory(project_root)
            history_manager.add_search(
                query=query,
                results_count=len(results),
                filters=filters if filters else None,
            )

            # Display results
            if json_output:
                from ..output import print_json

                results_data = [result.to_dict() for result in results]
                print_json(results_data, title="Search Results")
            else:
                print_search_results(
                    results=results,
                    query=query,
                    show_content=show_content,
                )

                # Add contextual tips based on results
                if results:
                    if len(results) >= limit:
                        print_tip(
                            f"More results may be available. Use [cyan]--limit {limit * 2}[/cyan] to see more."
                        )
                    if not export_format:
                        print_tip(
                            "Export results with [cyan]--export json[/cyan] or [cyan]--export markdown[/cyan]"
                        )
                else:
                    # No results - provide helpful suggestions
                    print_info("\n[bold]No results found. Try:[/bold]")
                    print_info("  • Use more general terms in your query")
                    print_info(
                        "  • Lower the similarity threshold with [cyan]--threshold 0.3[/cyan]"
                    )
                    print_info(
                        "  • Check if files are indexed with [cyan]mcp-vector-search status[/cyan]"
                    )

    except Exception as e:
        logger.error(f"Search execution failed: {e}")
        raise


def search_similar_cmd(
    ctx: typer.Context,
    file_path: Path = typer.Argument(
        ...,
        help="Reference file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Project root directory (auto-detected if not specified)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    function_name: str | None = typer.Option(
        None,
        "--function",
        "-f",
        help="Specific function name to find similar code for",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of results",
        min=1,
        max=100,
    ),
    similarity_threshold: float | None = typer.Option(
        None,
        "--threshold",
        "-t",
        help="Minimum similarity threshold",
        min=0.0,
        max=1.0,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results in JSON format",
    ),
) -> None:
    """Find code similar to a specific file or function.

    Examples:
        mcp-vector-search search similar src/auth.py
        mcp-vector-search search similar src/utils.py --function validate_email
    """
    try:
        project_root = project_root or ctx.obj.get("project_root") or Path.cwd()

        asyncio.run(
            run_similar_search(
                project_root=project_root,
                file_path=file_path,
                function_name=function_name,
                limit=limit,
                similarity_threshold=similarity_threshold,
                json_output=json_output,
            )
        )

    except Exception as e:
        logger.error(f"Similar search failed: {e}")
        print_error(f"Similar search failed: {e}")
        raise typer.Exit(1)


async def run_similar_search(
    project_root: Path,
    file_path: Path,
    function_name: str | None = None,
    limit: int = 10,
    similarity_threshold: float | None = None,
    json_output: bool = False,
) -> None:
    """Run similar code search."""
    project_manager = ProjectManager(project_root)
    config = project_manager.load_config()

    embedding_function, _ = create_embedding_function(config.embedding_model)
    database = ChromaVectorDatabase(
        persist_directory=config.index_path,
        embedding_function=embedding_function,
    )

    search_engine = SemanticSearchEngine(
        database=database,
        project_root=project_root,
        similarity_threshold=similarity_threshold or config.similarity_threshold,
    )

    async with database:
        results = await search_engine.search_similar(
            file_path=file_path,
            function_name=function_name,
            limit=limit,
            similarity_threshold=similarity_threshold,
        )

        if json_output:
            from ..output import print_json

            results_data = [result.to_dict() for result in results]
            print_json(results_data, title="Similar Code Results")
        else:
            query_desc = f"{file_path}"
            if function_name:
                query_desc += f" → {function_name}()"

            print_search_results(
                results=results,
                query=f"Similar to: {query_desc}",
                show_content=True,
            )


def search_context_cmd(
    ctx: typer.Context,
    description: str = typer.Argument(..., help="Context description"),
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Project root directory (auto-detected if not specified)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    focus: str | None = typer.Option(
        None,
        "--focus",
        help="Comma-separated focus areas (e.g., 'security,authentication')",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of results",
        min=1,
        max=100,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results in JSON format",
    ),
) -> None:
    """Search for code based on contextual description.

    Examples:
        mcp-vector-search search context "implement rate limiting"
        mcp-vector-search search context "user authentication" --focus security,middleware
    """
    try:
        project_root = project_root or ctx.obj.get("project_root") or Path.cwd()

        focus_areas = None
        if focus:
            focus_areas = [area.strip() for area in focus.split(",")]

        asyncio.run(
            run_context_search(
                project_root=project_root,
                description=description,
                focus_areas=focus_areas,
                limit=limit,
                json_output=json_output,
            )
        )

    except Exception as e:
        logger.error(f"Context search failed: {e}")
        print_error(f"Context search failed: {e}")
        raise typer.Exit(1)


async def run_context_search(
    project_root: Path,
    description: str,
    focus_areas: list[str] | None = None,
    limit: int = 10,
    json_output: bool = False,
) -> None:
    """Run contextual search."""
    project_manager = ProjectManager(project_root)
    config = project_manager.load_config()

    embedding_function, _ = create_embedding_function(config.embedding_model)
    database = ChromaVectorDatabase(
        persist_directory=config.index_path,
        embedding_function=embedding_function,
    )

    search_engine = SemanticSearchEngine(
        database=database,
        project_root=project_root,
        similarity_threshold=config.similarity_threshold,
    )

    async with database:
        results = await search_engine.search_by_context(
            context_description=description,
            focus_areas=focus_areas,
            limit=limit,
        )

        if json_output:
            from ..output import print_json

            results_data = [result.to_dict() for result in results]
            print_json(results_data, title="Context Search Results")
        else:
            query_desc = description
            if focus_areas:
                query_desc += f" (focus: {', '.join(focus_areas)})"

            print_search_results(
                results=results,
                query=query_desc,
                show_content=True,
            )


# ============================================================================
# SEARCH SUBCOMMANDS
# ============================================================================


@search_app.command("interactive")
def interactive_search(
    ctx: typer.Context,
    project_root: Path | None = typer.Option(
        None, "--project-root", "-p", help="Project root directory"
    ),
) -> None:
    """🎯 Start an interactive search session.

    Provides a rich terminal interface for searching your codebase with real-time
    filtering, query refinement, and result navigation.

    Examples:
        mcp-vector-search search interactive
        mcp-vector-search search interactive --project-root /path/to/project
    """
    import asyncio

    from ..interactive import start_interactive_search
    from ..output import console

    root = project_root or ctx.obj.get("project_root") or Path.cwd()

    try:
        asyncio.run(start_interactive_search(root))
    except KeyboardInterrupt:
        console.print("\n[yellow]Interactive search cancelled[/yellow]")
    except Exception as e:
        print_error(f"Interactive search failed: {e}")
        raise typer.Exit(1)


@search_app.command("history")
def show_history(
    ctx: typer.Context,
    limit: int = typer.Option(20, "--limit", "-l", help="Number of entries to show"),
    project_root: Path | None = typer.Option(
        None, "--project-root", "-p", help="Project root directory"
    ),
) -> None:
    """📜 Show search history.

    Displays your recent search queries with timestamps and result counts.
    Use this to revisit previous searches or track your search patterns.

    Examples:
        mcp-vector-search search history
        mcp-vector-search search history --limit 50
    """
    from ..history import show_search_history

    root = project_root or ctx.obj.get("project_root") or Path.cwd()
    show_search_history(root, limit)


@search_app.command("favorites")
def show_favorites_cmd(
    ctx: typer.Context,
    action: str | None = typer.Argument(None, help="Action: list, add, remove"),
    query: str | None = typer.Argument(None, help="Query to add/remove"),
    description: str | None = typer.Option(
        None, "--desc", help="Description for favorite"
    ),
    project_root: Path | None = typer.Option(
        None, "--project-root", "-p", help="Project root directory"
    ),
) -> None:
    """⭐ Manage favorite queries.

    List, add, or remove favorite search queries for quick access.

    Examples:
        mcp-vector-search search favorites                # List all favorites
        mcp-vector-search search favorites list           # List all favorites
        mcp-vector-search search favorites add "auth"     # Add favorite
        mcp-vector-search search favorites remove "auth"  # Remove favorite
    """
    from ..history import SearchHistory, show_favorites

    root = project_root or ctx.obj.get("project_root") or Path.cwd()
    history_manager = SearchHistory(root)

    # Default to list if no action provided
    if not action or action == "list":
        show_favorites(root)
    elif action == "add":
        if not query:
            print_error("Query is required for 'add' action")
            raise typer.Exit(1)
        history_manager.add_favorite(query, description)
    elif action == "remove":
        if not query:
            print_error("Query is required for 'remove' action")
            raise typer.Exit(1)
        history_manager.remove_favorite(query)
    else:
        print_error(f"Unknown action: {action}. Use: list, add, or remove")
        raise typer.Exit(1)


# Add main command to search_app (allows: mcp-vector-search search main "query")
search_app.command("main")(search_main)


if __name__ == "__main__":
    search_app()
