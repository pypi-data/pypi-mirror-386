"""Command-line interface for tenzir-changelog."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, TypedDict, Literal, cast

import click
from click.core import ParameterSource
from rich.console import RenderableType, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.rule import Rule

from packaging.version import InvalidVersion, Version

from .config import (
    Config,
    EXPORT_STYLE_COMPACT,
    default_config_path,
    load_config,
    save_config,
)
from .entries import (
    ENTRY_TYPES,
    Entry,
    entry_directory,
    iter_entries,
    sort_entries_desc,
    write_entry,
)
from .releases import (
    ReleaseManifest,
    NOTES_FILENAME,
    build_entry_release_index,
    collect_release_entries,
    iter_release_manifests,
    load_release_entry,
    release_directory,
    serialize_release_manifest,
    unused_entries,
    used_entry_ids,
    write_release_manifest,
)
from .validate import run_validation
from .utils import (
    INFO_PREFIX,
    configure_logging,
    console,
    extract_excerpt,
    log_debug,
    log_error,
    log_info,
    log_success,
    slugify,
    emit_output,
)

__all__ = ["cli", "INFO_PREFIX"]

ENTRY_TYPE_STYLES = {
    "breaking": "bold red",
    "feature": "green",
    "bugfix": "red",
    "change": "blue",
}
ENTRY_TYPE_EMOJIS = {
    "breaking": "💥",
    "feature": "🚀",
    "bugfix": "🐞",
    "change": "🔧",
}


def _print_renderable(renderable: RenderableType) -> None:
    """Emit a Rich renderable to the console without logging prefixes."""
    console.print(renderable)


def _format_section_title(entry_type: str, include_emoji: bool) -> str:
    """Return the section title with an optional type emoji prefix."""
    section_title = TYPE_SECTION_TITLES.get(entry_type, entry_type.title())
    if not include_emoji:
        return section_title
    emoji = ENTRY_TYPE_EMOJIS.get(entry_type)
    if not emoji:
        return section_title
    return f"{emoji} {section_title}"


def _command_help_text(
    summary: str,
    command_name: str,
    verb: str,
    row_hint: str,
    version_hint: str,
    indent: str = "    ",
) -> str:
    """Build consistent help text for commands that accept identifiers."""
    verb_title = verb.capitalize()
    body = textwrap.dedent(
        f"""\
        IDENTIFIERS can be:

        \b
        - {row_hint}
        - Entry IDs, partial or full (e.g., configure,
          configure-export-style-defaults)
        - Version numbers (e.g., v0.2.0) {version_hint}

        Examples:

        \b
          tenzir-changelog {command_name} 1           # {verb_title} entry #1
          tenzir-changelog {command_name} 1 2 3       # {verb_title} entries #1, #2, and #3
          tenzir-changelog {command_name} configure   # {verb_title} entry matching 'configure'
          tenzir-changelog {command_name} v0.2.0      # {verb_title} all entries in v0.2.0
        """
    ).strip()
    lines = [summary, ""]
    for segment in body.splitlines():
        lines.append(f"{indent}{segment}" if segment else "")
    return "\n".join(lines)


ENTRY_TYPE_CHOICES = (
    ("breaking", "0"),
    ("feature", "1"),
    ("bugfix", "2"),
    ("change", "3"),
)
ENTRY_TYPE_SHORTCUTS = {
    "breaking changes": "breaking",
    "breaking": "breaking",
    "break": "breaking",
    "bc": "breaking",
    "br": "breaking",
    "0": "breaking",
    "feature": "feature",
    "f": "feature",
    "1": "feature",
    "bugfix": "bugfix",
    "b": "bugfix",
    "2": "bugfix",
    "change": "change",
    "c": "change",
    "3": "change",
}
DEFAULT_ENTRY_TYPE = "feature"
TYPE_SECTION_TITLES = {
    "breaking": "Breaking changes",
    "feature": "Features",
    "change": "Changes",
    "bugfix": "Bug fixes",
}
ENTRY_EXPORT_ORDER = ("breaking", "feature", "change", "bugfix")
UNRELEASED_IDENTIFIER = "unreleased"
DASH_IDENTIFIER = "-"
DEFAULT_PROJECT_ID = "changelog"


IdentifierKind = Literal["row", "entry", "release", "unreleased"]


@dataclass
class IdentifierResolution:
    """Mapping from an identifier to matching entries."""

    kind: IdentifierKind
    entries: list[Entry]
    identifier: str
    manifest: Optional[ReleaseManifest] = None


OverflowMethod = Literal["fold", "crop", "ellipsis", "ignore"]
JustifyMethod = Literal["default", "left", "center", "right", "full"]


class ColumnSpec(TypedDict, total=False):
    """Configuration for rendering a Rich table column."""

    max_width: int
    overflow: OverflowMethod
    no_wrap: bool
    min_width: int


def _parse_pr_numbers(metadata: Mapping[str, Any]) -> list[int]:
    """Normalize PR metadata into a list of integers."""

    value = metadata.get("prs")
    if value is None:
        return []

    if isinstance(value, (str, int)):
        candidates = [value]
    else:
        try:
            candidates = list(value)
        except TypeError:
            candidates = [value]

    pr_numbers: list[int] = []
    for candidate in candidates:
        try:
            pr_numbers.append(int(str(candidate).strip()))
        except (TypeError, ValueError):
            continue
    return pr_numbers


def _entries_table_layout(console_width: int) -> tuple[list[str], dict[str, ColumnSpec]]:
    """Return the visible columns and their specs for the current terminal width."""

    width = max(console_width, 60)
    if width < 70:
        columns = ["num", "date", "title", "type"]
        specs: dict[str, ColumnSpec] = {
            "num": {"max_width": 3, "no_wrap": True},
            "title": {"min_width": 20, "max_width": 32, "overflow": "ellipsis", "no_wrap": True},
            "type": {"min_width": 3, "max_width": 4, "no_wrap": True},
        }
    elif width < 78:
        columns = ["num", "date", "version", "title", "type"]
        specs = {
            "num": {"max_width": 3, "no_wrap": True},
            "version": {"max_width": 8, "no_wrap": True},
            "title": {"min_width": 18, "max_width": 30, "overflow": "ellipsis", "no_wrap": True},
            "type": {"min_width": 3, "max_width": 4, "no_wrap": True},
        }
    elif width < 88:
        columns = ["num", "date", "version", "title", "type", "prs"]
        specs = {
            "num": {"max_width": 3, "no_wrap": True},
            "version": {"max_width": 9, "no_wrap": True},
            "title": {"min_width": 18, "max_width": 28, "overflow": "ellipsis", "no_wrap": True},
            "prs": {"max_width": 12, "no_wrap": True},
            "type": {"min_width": 3, "max_width": 4, "no_wrap": True},
        }
    elif width < 110:
        columns = ["num", "date", "version", "title", "type", "prs", "authors"]
        specs = {
            "num": {"max_width": 3, "no_wrap": True},
            "version": {"max_width": 9, "no_wrap": True},
            "title": {"min_width": 18, "max_width": 26, "overflow": "ellipsis", "no_wrap": True},
            "prs": {"max_width": 12, "no_wrap": True},
            "authors": {
                "min_width": 10,
                "max_width": 14,
                "overflow": "ellipsis",
                "no_wrap": True,
            },
            "type": {"min_width": 3, "max_width": 4, "no_wrap": True},
        }
    elif width < 140:
        columns = ["num", "date", "version", "title", "type", "prs", "authors", "id"]
        specs = {
            "num": {"max_width": 3, "no_wrap": True},
            "version": {"max_width": 10, "no_wrap": True},
            "title": {"min_width": 18, "max_width": 32, "overflow": "ellipsis", "no_wrap": True},
            "prs": {"max_width": 12, "no_wrap": True},
            "authors": {
                "min_width": 10,
                "max_width": 16,
                "overflow": "ellipsis",
                "no_wrap": True,
            },
            "id": {"min_width": 16, "max_width": 22, "overflow": "ellipsis", "no_wrap": True},
            "type": {"min_width": 3, "max_width": 4, "no_wrap": True},
        }
    else:
        columns = ["num", "date", "version", "title", "type", "prs", "authors", "id"]
        specs = {
            "num": {"max_width": 3, "no_wrap": True},
            "version": {"max_width": 12, "no_wrap": True},
            "title": {"min_width": 20, "max_width": 40, "overflow": "fold"},
            "prs": {"max_width": 14, "no_wrap": True},
            "authors": {"min_width": 14, "max_width": 20, "overflow": "fold"},
            "id": {"min_width": 18, "max_width": 28, "overflow": "fold"},
            "type": {"min_width": 3, "max_width": 4, "no_wrap": True},
        }
    return columns, specs


def _ellipsis_cell(
    value: str,
    column: str,
    specs: dict[str, ColumnSpec],
    *,
    style: str | None = None,
) -> Text | str:
    """Return a Text cell with ellipsis truncation when requested."""

    spec = specs.get(column)
    if not spec:
        return value
    overflow_mode = spec.get("overflow")
    if overflow_mode != "ellipsis":
        return value
    width = spec.get("max_width") or spec.get("min_width")
    if not width:
        return value
    text = Text(str(value), style=style or "")
    plain = text.plain
    if len(plain) > width:
        text = Text(plain[: width - 1] + "…", style=style or "")
    text.no_wrap = True
    return text


def _add_table_column(
    table: Table,
    header: str,
    column_key: str,
    specs: dict[str, ColumnSpec],
    *,
    style: str | None = None,
    justify: JustifyMethod = "left",
    overflow_default: OverflowMethod = "fold",
    no_wrap_default: bool = False,
) -> None:
    spec = specs.get(column_key)
    min_width = spec.get("min_width") if spec and "min_width" in spec else None
    max_width = spec.get("max_width") if spec and "max_width" in spec else None
    overflow = overflow_default
    if spec and "overflow" in spec:
        overflow = spec["overflow"]
    no_wrap = no_wrap_default
    if spec and "no_wrap" in spec:
        no_wrap = spec["no_wrap"]
    table.add_column(
        header,
        style=style,
        justify=justify,
        overflow=overflow,
        min_width=min_width,
        max_width=max_width,
        no_wrap=no_wrap,
    )


@dataclass
class CLIContext:
    """Shared command context."""

    project_root: Path
    config_path: Path
    _config: Optional[Config] = None

    def ensure_config(self, *, create_if_missing: bool = False) -> Config:
        if self._config is None:
            config_path = self.config_path
            project_root = config_path.parent
            self.project_root = project_root
            if not config_path.exists():
                if not create_if_missing:
                    log_info(f"no tenzir-changelog project detected at {project_root}.")
                    log_info("run 'tenzir-changelog add' from your project root or provide --root.")
                    raise click.exceptions.Exit(1)
                config = _initialize_project_scaffold(
                    project_root=project_root,
                    config_path=config_path,
                )
                self._config = config
            else:
                self._config = load_config(config_path)
        entry_directory(self.project_root).mkdir(parents=True, exist_ok=True)
        release_directory(self.project_root).mkdir(parents=True, exist_ok=True)
        return self._config

    def reset_config(self, config: Config) -> None:
        self._config = config


def _default_project_id(project_root: Path) -> str:
    slug = slugify(project_root.name)
    return slug or DEFAULT_PROJECT_ID


def _default_project_name(project_id: str) -> str:
    words = project_id.replace("-", " ").strip()
    return words.title() if words else "Changelog"


def _initialize_project_scaffold(*, project_root: Path, config_path: Path) -> Config:
    project_id = _default_project_id(project_root)
    project_name = _default_project_name(project_id)
    config = Config(id=project_id, name=project_name)
    save_config(config, config_path)
    entry_directory(project_root).mkdir(parents=True, exist_ok=True)
    release_directory(project_root).mkdir(parents=True, exist_ok=True)
    log_success(f"initialized changelog project at {project_root}")
    return config


def _resolve_project_root(value: Path) -> Path:
    return value.resolve()


def _normalize_optional(value: Optional[str]) -> Optional[str]:
    """Convert Click sentinel values to None."""

    if value is None:
        return None
    value_class = value.__class__.__name__
    if value_class == "Sentinel":
        return None
    return value


def _prompt_project(existing: Optional[str], project_root: Path) -> str:
    """Prompt for the primary project slug."""
    default_value = existing or slugify(project_root.name)
    project = click.prompt(
        "Project name (used in entry metadata)",
        default=default_value,
        show_default=True,
    ).strip()
    if not project:
        raise click.ClickException("Project name cannot be empty.")
    return slugify(project)


def _mask_comment_block(text: str) -> str:
    """Strip comment lines (starting with '#') from editor input."""
    lines = []
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--root",
    type=click.Path(path_type=Path, exists=True, file_okay=False),
    default=Path("."),
    help="Project root containing config and changelog files.",
)
@click.option(
    "--config",
    type=click.Path(path_type=Path, dir_okay=False),
    help="Path to an explicit changelog config YAML file.",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable debug logging.",
)
@click.pass_context
def cli(ctx: click.Context, root: Path, config: Optional[Path], debug: bool) -> None:
    """Manage changelog entries and release manifests."""
    configure_logging(debug)
    root = _resolve_project_root(root)
    config_path = config.resolve() if config else default_config_path(root)
    log_debug(f"resolved project root: {root}")
    log_debug(f"using config path: {config_path}")
    ctx.obj = CLIContext(project_root=root, config_path=config_path)

    if ctx.invoked_subcommand is None:
        ctx.invoke(show_entries)


def _filter_entries_by_project(
    entries: Iterable[Entry], projects: set[str], default_project: str
) -> list[Entry]:
    if not projects:
        return list(entries)
    filtered: list[Entry] = []
    for entry in entries:
        entry_project = entry.project or default_project
        if entry_project and entry_project in projects:
            filtered.append(entry)
    return filtered


def _build_release_sort_order(project_root: Path) -> dict[str, int]:
    """Return a mapping from release version to display order rank."""
    manifests = list(iter_release_manifests(project_root))
    manifests.sort(key=lambda manifest: (manifest.created, manifest.version), reverse=True)
    return {manifest.version: index for index, manifest in enumerate(manifests)}


def _sort_entries_for_display(
    entries: Iterable[Entry],
    release_index: dict[str, list[str]],
    release_order: dict[str, int],
) -> list[Entry]:
    """Sort entries by release recency first, then date."""
    entries_list = list(entries)
    fallback_rank = len(release_order) + 1

    def sort_key(entry: Entry) -> tuple[int, int, int, str]:
        versions = release_index.get(entry.entry_id) or []
        if versions:
            ranks = [release_order.get(version, fallback_rank) for version in versions]
            release_rank = min(ranks) + 1
        else:
            release_rank = 0  # unreleased entries first
        created = entry.created_at or date.min
        created_ord = created.toordinal()
        return (release_rank, -created_ord, -entry.sequence, entry.entry_id)

    return sorted(entries_list, key=sort_key)


def _entry_release_group(
    entry: Entry,
    release_index: dict[str, list[str]],
    release_order: dict[str, int] | None,
) -> str | None:
    """Return the primary release identifier for grouping."""
    versions = release_index.get(entry.entry_id) or []
    if not versions:
        return None
    if release_order:
        fallback_rank = len(release_order) + 1
        ranked_versions = sorted(
            versions, key=lambda version: release_order.get(version, fallback_rank)
        )
        return ranked_versions[0]
    return sorted(versions)[0]


def _collect_unused_entries_for_release(project_root: Path, config: Config) -> list[Entry]:
    all_entries = list(iter_entries(project_root))
    used = used_entry_ids(project_root)
    unused = unused_entries(all_entries, used)
    filtered = [entry for entry in unused if entry.project is None or entry.project == config.id]
    return filtered


def _render_project_header(config: Config) -> None:
    legend = "  ".join(
        f"{ENTRY_TYPE_EMOJIS.get(entry_type, '•')} {entry_type}"
        for entry_type in ENTRY_EXPORT_ORDER
    )
    header = Text.assemble(
        ("Name: ", "bold"),
        config.name or "—",
        ("\nID: ", "bold"),
        config.id or "—",
        ("\nRepository: ", "bold"),
        config.repository or "—",
        ("\nTypes: ", "bold"),
        legend or "—",
    )
    _print_renderable(Panel.fit(header, title="Project"))


def _render_entries(
    entries: Iterable[Entry],
    release_index: dict[str, list[str]],
    config: Config,
    show_banner: bool = False,
    release_order: dict[str, int] | None = None,
    *,
    include_emoji: bool = True,
) -> None:
    if show_banner:
        _render_project_header(config)

    visible_columns, column_specs = _entries_table_layout(console.size.width)
    table_width = max(console.size.width, 40)
    table = Table(show_lines=False, expand=False, width=table_width, pad_edge=False)
    if "num" in visible_columns:
        _add_table_column(
            table,
            "#",
            "num",
            column_specs,
            style="dim",
            justify="right",
            overflow_default="fold",
            no_wrap_default=True,
        )
    if "date" in visible_columns:
        _add_table_column(
            table,
            "Date",
            "date",
            column_specs,
            style="yellow",
            overflow_default="fold",
            no_wrap_default=True,
        )
    if "version" in visible_columns:
        _add_table_column(
            table,
            "Version",
            "version",
            column_specs,
            style="cyan",
            justify="center",
            overflow_default="fold",
            no_wrap_default=True,
        )
    if "title" in visible_columns:
        _add_table_column(
            table,
            "Title",
            "title",
            column_specs,
            style="bold",
            overflow_default="fold",
        )
    if "type" in visible_columns:
        _add_table_column(
            table,
            "Type",
            "type",
            column_specs,
            style="magenta",
            justify="center",
            overflow_default="ellipsis",
            no_wrap_default=True,
        )
    if "prs" in visible_columns:
        _add_table_column(
            table,
            "PRs",
            "prs",
            column_specs,
            style="yellow",
            overflow_default="fold",
            no_wrap_default=True,
        )
    if "authors" in visible_columns:
        _add_table_column(
            table,
            "Authors",
            "authors",
            column_specs,
            style="blue",
            overflow_default="fold",
        )
    if "id" in visible_columns:
        _add_table_column(
            table,
            "ID",
            "id",
            column_specs,
            style="cyan",
            overflow_default="ellipsis",
            no_wrap_default=True,
        )

    has_rows = False
    if release_order is not None:
        sorted_entries = _sort_entries_for_display(entries, release_index, release_order)
        release_groups = [
            _entry_release_group(entry, release_index, release_order) for entry in sorted_entries
        ]
    else:
        sorted_entries = sort_entries_desc(list(entries))
        release_groups = [None] * len(sorted_entries)

    for row_num, entry in enumerate(sorted_entries, start=1):
        metadata = entry.metadata
        created_display = entry.created_at.isoformat() if entry.created_at else "—"
        type_value = metadata.get("type", "change")
        versions = release_index.get(entry.entry_id)
        version_display = ", ".join(versions) if versions else "—"
        if include_emoji:
            glyph = ENTRY_TYPE_EMOJIS.get(type_value, "•")
        else:
            glyph = type_value[:1].upper() if type_value else "?"
        type_display = Text(glyph, style=ENTRY_TYPE_STYLES.get(type_value, ""))
        row: list[RenderableType] = []
        if "num" in visible_columns:
            row.append(str(row_num))
        if "date" in visible_columns:
            row.append(created_display)
        if "version" in visible_columns:
            row.append(version_display)
        if "title" in visible_columns:
            row.append(_ellipsis_cell(metadata.get("title", "Untitled"), "title", column_specs))
        if "type" in visible_columns:
            row.append(type_display)
        if "prs" in visible_columns:
            pr_numbers = _parse_pr_numbers(metadata)
            pr_display = ", ".join(f"#{pr}" for pr in pr_numbers) if pr_numbers else "—"
            row.append(_ellipsis_cell(pr_display, "prs", column_specs))
        if "authors" in visible_columns:
            row.append(
                _ellipsis_cell(
                    ", ".join(metadata.get("authors") or []) or "—",
                    "authors",
                    column_specs,
                )
            )
        if "id" in visible_columns:
            row.append(_ellipsis_cell(entry.entry_id, "id", column_specs, style="cyan"))
        end_section = False
        if release_order is not None and row_num - 1 < len(sorted_entries) - 1:
            current_group = release_groups[row_num - 1]
            next_group = release_groups[row_num]
            if current_group != next_group:
                end_section = True

        table.add_row(*row, end_section=end_section)
        has_rows = True

    if has_rows:
        _print_renderable(table)
    else:
        log_info("no entries found.")


def _render_release(
    manifest: ReleaseManifest,
    project_root: Path,
    *,
    project_id: str,
) -> None:
    _print_renderable(Rule(f"Release {manifest.version}"))
    header = Text.assemble(
        ("Title: ", "bold"),
        manifest.title or manifest.version or "—",
        ("\nDescription: ", "bold"),
        manifest.description or "—",
        ("\nCreated: ", "bold"),
        manifest.created.isoformat(),
        ("\nProject: ", "bold"),
        project_id or "—",
    )
    _print_renderable(header)

    if manifest.intro:
        _print_renderable(
            Panel(
                manifest.intro,
                title="Introduction",
                subtitle="Markdown",
                expand=False,
            )
        )

    all_entries = {entry.entry_id: entry for entry in iter_entries(project_root)}
    table = Table(title="Included Entries")
    table.add_column("Order")
    table.add_column("Entry ID", style="cyan")
    table.add_column("Title")
    table.add_column("Type", style="magenta")
    for index, entry_id in enumerate(manifest.entries, 1):
        entry = all_entries.get(entry_id)
        if entry is None:
            entry = load_release_entry(project_root, manifest, entry_id)
        if entry:
            table.add_row(
                str(index),
                entry_id,
                entry.metadata.get("title", "Untitled"),
                entry.metadata.get("type", "change"),
            )
        else:
            table.add_row(str(index), entry_id, "[red]Missing entry[/red]", "—")
    _print_renderable(table)


def _render_single_entry(
    entry: Entry,
    release_versions: list[str],
    *,
    include_emoji: bool = True,
) -> None:
    """Display a single changelog entry with formatted output."""
    # Build title with emoji and type color
    type_color = ENTRY_TYPE_STYLES.get(entry.type, "white")

    title = Text()
    if include_emoji:
        type_emoji = ENTRY_TYPE_EMOJIS.get(entry.type, "•")
        title.append(f"{type_emoji} ", style="bold")
    title.append(entry.title, style=f"bold {type_color}")

    # Build metadata section
    metadata_parts = []
    metadata_parts.append(f"Entry ID:  [cyan]{entry.entry_id}[/cyan]")
    metadata_parts.append(f"Type:      [{type_color}]{entry.type}[/{type_color}]")

    if entry.created_at:
        metadata_parts.append(f"Created:   {entry.created_at}")

    authors = entry.metadata.get("authors")
    if authors:
        authors_str = ", ".join(f"@{a}" for a in authors)
        metadata_parts.append(f"Authors:   {authors_str}")

    # Include pull-request references when available.
    pr_numbers = _parse_pr_numbers(entry.metadata)
    if pr_numbers:
        prs_str = ", ".join(f"#{pr}" for pr in pr_numbers)
        metadata_parts.append(f"PRs:       {prs_str}")

    # Status: released or unreleased
    if release_versions:
        versions_str = ", ".join(release_versions)
        metadata_parts.append(f"Status:    [green]Released in {versions_str}[/green]")
    else:
        metadata_parts.append("Status:    [yellow]Unreleased[/yellow]")

    metadata_text = Text.from_markup("\n".join(metadata_parts))

    # Build the markdown body
    body_content: RenderableType
    if entry.body.strip():
        body_content = Markdown(entry.body.strip(), code_theme="ansi_light")
    else:
        body_content = Text("No description provided.", style="dim")

    # Create a divider that fits inside the panel
    # Panel has 2 characters for borders and 2 for padding (left/right)
    divider_width = max(40, console.width - 4)
    divider = Text("─" * divider_width, style="dim")

    # Combine all sections with dividers
    content = Group(
        metadata_text,
        divider,
        body_content,
    )

    # Display everything in a single panel with the title
    _print_renderable(Panel(content, title=title, title_align="left", expand=True))


def _show_entries_table(
    ctx: CLIContext,
    identifiers: tuple[str, ...],
    project_filter: tuple[str, ...],
    banner: bool,
    *,
    include_emoji: bool,
) -> None:
    config = ctx.ensure_config()
    project_root = ctx.project_root
    projects = set(project_filter)

    # Collect all entries (unreleased and released)
    entries = list(iter_entries(project_root))
    entry_map = {entry.entry_id: entry for entry in entries}
    released_entries = collect_release_entries(project_root)
    for entry_id, entry in released_entries.items():
        if entry_id not in entry_map:
            entry_map[entry_id] = entry

    # Build release index
    release_index = build_entry_release_index(project_root, project=config.id)
    release_order = _build_release_sort_order(project_root)

    # Sort entries to match display order
    sorted_entries = _sort_entries_for_display(entry_map.values(), release_index, release_order)

    # Filter by identifiers if provided
    if identifiers:
        resolutions = _resolve_identifiers_sequence(
            identifiers,
            project_root=project_root,
            config=config,
            sorted_entries=sorted_entries,
            entry_map=entry_map,
        )
        if len(resolutions) == 1 and resolutions[0].kind == "release":
            manifest = resolutions[0].manifest
            if manifest is None:
                raise click.ClickException(f"Release '{resolutions[0].identifier}' not found.")
            _render_release(manifest, project_root, project_id=config.id)
            return
        filtered_entries: list[Entry] = []
        for resolution in resolutions:
            filtered_entries.extend(resolution.entries)
        entries = filtered_entries
    else:
        entries = sorted_entries

    entries = _filter_entries_by_project(entries, projects, config.id)
    render_release_order = release_order if not identifiers else None
    _render_entries(
        entries,
        release_index,
        config,
        show_banner=banner,
        release_order=render_release_order,
        include_emoji=include_emoji,
    )


def _load_release_entries_for_display(
    project_root: Path,
    release_version: str,
    entry_map: dict[str, Entry],
) -> tuple[ReleaseManifest, list[Entry]]:
    normalized_version = release_version.strip()
    manifests = [
        manifest
        for manifest in iter_release_manifests(project_root)
        if manifest.version == normalized_version
    ]
    if not manifests:
        raise click.ClickException(f"Release '{release_version}' not found.")
    manifest = manifests[0]
    missing_entries: list[str] = []
    release_entries: list[Entry] = []
    for entry_id in manifest.entries:
        entry = entry_map.get(entry_id)
        if entry is None:
            entry = load_release_entry(project_root, manifest, entry_id)
        if entry is None:
            missing_entries.append(entry_id)
            continue
        entry_map[entry_id] = entry
        release_entries.append(entry)
    if missing_entries:
        missing_list = ", ".join(sorted(missing_entries))
        raise click.ClickException(
            f"Release '{manifest.version}' is missing entry files for: {missing_list}"
        )
    return manifest, release_entries


def _resolve_identifier(
    identifier: str,
    *,
    project_root: Path,
    config: Config,
    sorted_entries: list[Entry],
    entry_map: dict[str, Entry],
    allowed_kinds: Optional[Iterable[IdentifierKind]] = None,
) -> IdentifierResolution:
    allowed = (
        set(allowed_kinds)
        if allowed_kinds is not None
        else {
            "row",
            "entry",
            "release",
            "unreleased",
        }
    )
    token = identifier.strip()
    if not token:
        raise click.ClickException("Identifier cannot be empty.")

    lowered = token.lower()
    if lowered in {UNRELEASED_IDENTIFIER, DASH_IDENTIFIER}:
        if "unreleased" not in allowed:
            raise click.ClickException(
                "The 'unreleased' identifier is not supported by this command."
            )
        entries = sort_entries_desc(_collect_unused_entries_for_release(project_root, config))
        return IdentifierResolution(kind="unreleased", entries=entries, identifier=token)

    try:
        row_num = int(token)
    except ValueError:
        row_num = None

    if row_num is not None:
        if "row" not in allowed:
            raise click.ClickException("Row numbers are not supported by this command.")
        if 1 <= row_num <= len(sorted_entries):
            return IdentifierResolution(
                kind="row",
                entries=[sorted_entries[row_num - 1]],
                identifier=token,
            )
        raise click.ClickException(
            f"Row number {row_num} is out of range. Valid range: 1-{len(sorted_entries)}"
        )

    if token.startswith(("v", "V")):
        if "release" not in allowed:
            raise click.ClickException(
                f"Release identifiers such as '{token}' are not supported by this command."
            )
        manifest, release_entries = _load_release_entries_for_display(
            project_root, token, entry_map
        )
        return IdentifierResolution(
            kind="release",
            entries=release_entries,
            identifier=manifest.version,
            manifest=manifest,
        )

    exact_match = entry_map.get(token)
    if exact_match:
        return IdentifierResolution(kind="entry", entries=[exact_match], identifier=token)

    matches = [(entry_id, entry) for entry_id, entry in entry_map.items() if token in entry_id]
    if not matches:
        raise click.ClickException(
            f"No entry found matching '{token}'. Use 'tenzir-changelog show' to see all entries."
        )
    if len(matches) > 1:
        match_ids = [entry_id for entry_id, _ in matches]
        raise click.ClickException(
            f"Multiple entries match '{token}':\n  "
            + "\n  ".join(match_ids)
            + "\n\nPlease be more specific or use a row number."
        )

    entry_id, entry = matches[0]
    return IdentifierResolution(kind="entry", entries=[entry], identifier=entry_id)


def _resolve_identifiers_sequence(
    identifiers: Iterable[str],
    *,
    project_root: Path,
    config: Config,
    sorted_entries: list[Entry],
    entry_map: dict[str, Entry],
    allowed_kinds: Optional[Iterable[IdentifierKind]] = None,
) -> list[IdentifierResolution]:
    """Resolve a list of identifiers into their matching entries."""

    return [
        _resolve_identifier(
            identifier,
            project_root=project_root,
            config=config,
            sorted_entries=sorted_entries,
            entry_map=entry_map,
            allowed_kinds=allowed_kinds,
        )
        for identifier in identifiers
    ]


ShowView = Literal["table", "card", "markdown", "json"]


def _gather_entry_context(
    project_root: Path,
) -> tuple[dict[str, Entry], dict[str, list[str]], dict[str, int], list[Entry]]:
    entries = list(iter_entries(project_root))
    entry_map = {entry.entry_id: entry for entry in entries}
    released_entries = collect_release_entries(project_root)
    for entry_id, entry in released_entries.items():
        entry_map.setdefault(entry_id, entry)
    release_index_all = build_entry_release_index(project_root, project=None)
    release_order = _build_release_sort_order(project_root)
    sorted_entries = _sort_entries_for_display(entry_map.values(), release_index_all, release_order)
    return entry_map, release_index_all, release_order, sorted_entries


def _show_entries_card(
    ctx: CLIContext,
    identifiers: tuple[str, ...],
    *,
    include_emoji: bool,
) -> None:
    if not identifiers:
        raise click.ClickException(
            "Provide at least one identifier such as a row number, entry ID, release version, or the 'unreleased' token."
        )

    config = ctx.ensure_config()
    project_root = ctx.project_root
    entry_map, release_index_all, _, sorted_entries = _gather_entry_context(project_root)
    resolutions = _resolve_identifiers_sequence(
        identifiers,
        project_root=project_root,
        config=config,
        sorted_entries=sorted_entries,
        entry_map=entry_map,
    )

    release_index = release_index_all
    for resolution in resolutions:
        if resolution.kind == "unreleased" and not resolution.entries:
            console.print("[yellow]No unreleased entries found.[/yellow]")
            continue
        for entry in resolution.entries:
            versions = release_index.get(entry.entry_id, [])
            if resolution.kind == "release" and resolution.manifest:
                version = resolution.manifest.version
                if version and version not in versions:
                    versions = versions + [version]
            _render_single_entry(entry, versions, include_emoji=include_emoji)


def _show_entries_export(
    ctx: CLIContext,
    identifiers: tuple[str, ...],
    *,
    view: ShowView,
    compact: Optional[bool],
    include_emoji: bool,
) -> None:
    if not identifiers:
        raise click.ClickException("Provide at least one identifier for markdown or json output.")

    config = ctx.ensure_config()
    project_root = ctx.project_root
    entry_map, _, _, sorted_entries = _gather_entry_context(project_root)
    resolutions = _resolve_identifiers_sequence(
        identifiers,
        project_root=project_root,
        config=config,
        sorted_entries=sorted_entries,
        entry_map=entry_map,
    )

    compact_flag = config.export_style == EXPORT_STYLE_COMPACT if compact is None else compact
    release_index_export = build_entry_release_index(project_root, project=config.id)
    manifest_for_export: ReleaseManifest | None = None

    if len(resolutions) == 1 and resolutions[0].kind == "release":
        manifest = resolutions[0].manifest
        if manifest is not None and manifest.description:
            manifest_for_export = replace(manifest, description="")
        else:
            manifest_for_export = manifest

    ordered_entries: dict[str, Entry] = {}
    for resolution in resolutions:
        for entry in resolution.entries:
            if entry.entry_id not in ordered_entries:
                ordered_entries[entry.entry_id] = entry
    export_entries = sort_entries_desc(list(ordered_entries.values()))
    if not export_entries:
        raise click.ClickException("No entries matched the provided identifier for export.")

    if len(resolutions) == 1 and resolutions[0].kind == "unreleased":
        fallback_heading = "Unreleased Changes"
        fallback_created = None
    elif manifest_for_export is not None:
        fallback_heading = (
            resolutions[0].manifest.title
            if resolutions[0].manifest and resolutions[0].manifest.title
            else resolutions[0].identifier
        )
        fallback_created = None
    else:
        if len(resolutions) == 1 and resolutions[0].kind in {"entry", "row"}:
            entry = export_entries[0]
            fallback_heading = f"Entry {entry.entry_id}"
            fallback_created = entry.created_at
        else:
            fallback_heading = "Selected Entries"
            dates = [entry.created_at for entry in export_entries if entry.created_at]
            fallback_created = min(dates) if dates else None

    if view == "markdown":
        if compact_flag:
            content = _export_markdown_compact(
                manifest_for_export,
                export_entries,
                config,
                release_index_export,
                include_emoji=include_emoji,
                fallback_heading=fallback_heading,
            )
        else:
            content = _export_markdown_release(
                manifest_for_export,
                export_entries,
                config,
                release_index_export,
                include_emoji=include_emoji,
                fallback_heading=fallback_heading,
            )
        emit_output(content, newline=False)
    else:
        payload = _export_json_payload(
            manifest_for_export,
            export_entries,
            config,
            release_index_export,
            compact=compact_flag,
            fallback_heading=fallback_heading,
            fallback_created=fallback_created,
        )
        emit_output(json.dumps(payload, indent=2))


@cli.command("show")
@click.argument("identifiers", nargs=-1, required=False)
@click.option(
    "-t",
    "--table",
    "view_flags",
    flag_value="table",
    help="Display entries in a table view (default).",
    multiple=True,
)
@click.option(
    "-c",
    "--card",
    "view_flags",
    flag_value="card",
    help="Display entries as detailed cards.",
    multiple=True,
)
@click.option(
    "-m",
    "--markdown",
    "view_flags",
    flag_value="markdown",
    help="Export entries as Markdown.",
    multiple=True,
)
@click.option(
    "-j",
    "--json",
    "view_flags",
    flag_value="json",
    help="Export entries as JSON.",
    multiple=True,
)
@click.option("--project", "project_filter", multiple=True, help="Filter by project key.")
@click.option("--banner", is_flag=True, help="Display a project banner above entries.")
@click.option(
    "--compact",
    "compact",
    flag_value=True,
    default=None,
    help="Use the compact layout for Markdown and JSON output.",
)
@click.option(
    "--no-compact",
    "compact",
    flag_value=False,
    help="Disable the compact layout for Markdown and JSON output.",
)
@click.option(
    "--no-emoji",
    is_flag=True,
    help="Disable type emoji in entry output.",
)
@click.pass_obj
def show_entries(
    ctx: CLIContext,
    identifiers: tuple[str, ...],
    view_flags: tuple[str, ...],
    project_filter: tuple[str, ...],
    banner: bool,
    compact: Optional[bool],
    no_emoji: bool,
) -> None:
    """Display changelog entries in tables, cards, or export formats."""

    view_choice = view_flags[-1] if view_flags else "table"
    if view_choice not in {"table", "card", "markdown", "json"}:
        raise click.ClickException(f"Unsupported view '{view_choice}'.")
    view = cast(ShowView, view_choice)
    include_emoji = not no_emoji

    if view == "table":
        if compact is not None:
            raise click.ClickException(
                "--compact/--no-compact only apply to markdown and json views."
            )
        _show_entries_table(
            ctx,
            identifiers,
            project_filter,
            banner,
            include_emoji=include_emoji,
        )
        return

    if project_filter or banner:
        raise click.ClickException("--project/--banner are only available in table view.")

    if view == "card":
        if compact is not None:
            raise click.ClickException(
                "--compact/--no-compact only apply to markdown and json views."
            )
        _show_entries_card(ctx, identifiers, include_emoji=include_emoji)
        return

    if view in {"markdown", "json"}:
        _show_entries_export(
            ctx,
            identifiers,
            view=view,
            compact=compact,
            include_emoji=include_emoji,
        )
        return

    raise click.ClickException(f"Unsupported view '{view}'.")


SHOW_COMMAND_SUMMARY = "Display changelog entries in tables, cards, or exports."
show_help = _command_help_text(
    summary=SHOW_COMMAND_SUMMARY,
    command_name="show",
    verb="show",
    row_hint="Row numbers (e.g., 1, 2, 3), 'unreleased', or '-'",
    version_hint="to show all entries in that release or export it",
)
show_entries.__doc__ = show_help
show_entries.help = show_help
show_entries.short_help = SHOW_COMMAND_SUMMARY


def _prompt_entry_body(initial: str = "") -> str:
    edited = click.edit(
        textwrap.dedent(
            """\
            # Write the entry body below. Lines starting with '#' are ignored.
            # Save and close the editor to finish. Leave empty to skip.
            """
        )
        + ("\n" + initial if initial else "\n")
    )
    if edited is None:
        return ""
    return _mask_comment_block(edited)


def _prompt_text(label: str, **kwargs: Any) -> str:
    prompt_suffix = kwargs.pop("prompt_suffix", ": ")
    result = click.prompt(click.style(label, bold=True), prompt_suffix=prompt_suffix, **kwargs)
    return str(result)


def _prompt_optional(prompt: str, default: Optional[str] = None) -> Optional[str]:
    value = _prompt_text(
        prompt,
        default=default or "",
        show_default=bool(default),
    )
    return value.strip() or None


def _normalize_entry_type(value: str) -> Optional[str]:
    value = value.strip().lower()
    if not value:
        return DEFAULT_ENTRY_TYPE
    return ENTRY_TYPE_SHORTCUTS.get(value)


def _prompt_entry_type(default: str = DEFAULT_ENTRY_TYPE) -> str:
    prompt_text = Text("Type: ", style="bold")
    for idx, (name, key) in enumerate(ENTRY_TYPE_CHOICES):
        prompt_text.append(name)
        prompt_text.append(" [")
        prompt_text.append(key, style="bold cyan")
        prompt_text.append("]")
        if idx < len(ENTRY_TYPE_CHOICES) - 1:
            prompt_text.append(", ")
    console.print(prompt_text)

    while True:
        key = click.getchar()
        if key in {"\r", "\n"}:
            selection = default
            break
        normalized = _normalize_entry_type(key)
        if normalized:
            selection = normalized
            break
    console.print(Text(f"  {selection}", style=ENTRY_TYPE_STYLES.get(selection, "")))
    return selection


def _entry_to_dict(
    entry: Entry,
    config: Config,
    version: str | None = None,
    *,
    compact: bool = False,
) -> dict[str, object]:
    metadata = entry.metadata
    prs_list = _parse_pr_numbers(metadata)
    entry_type = metadata.get("type", DEFAULT_ENTRY_TYPE)
    title = metadata.get("title", "Untitled")
    data = {
        "id": entry.entry_id,
        "title": title,
        "type": entry_type,
        "created": entry.created_at.isoformat() if entry.created_at else None,
        "project": entry.project or config.id,
        "prs": prs_list,
        "authors": metadata.get("authors") or [],
        "version": version,
        "body": entry.body,
    }
    if compact:
        data["excerpt"] = extract_excerpt(entry.body)
    return data


def _join_with_conjunction(items: list[str]) -> str:
    items = [item for item in items if item]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _collect_author_pr_text(entry: Entry, config: Config) -> tuple[str, str]:
    metadata = entry.metadata
    authors = metadata.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    authors = [author.strip() for author in authors if author and author.strip()]

    author_handles = [f"@{author}" for author in authors]
    author_text = _join_with_conjunction(author_handles)

    prs = _parse_pr_numbers(metadata)

    repo = config.repository
    pr_links: list[str] = []
    for pr in prs:
        label = f"#{pr}"
        if repo:
            pr_links.append(f"[{label}](https://github.com/{repo}/pull/{pr})")
        else:
            pr_links.append(label)

    pr_text = _join_with_conjunction(pr_links)
    return author_text, pr_text


def _format_author_line(entry: Entry, config: Config) -> str:
    author_text, pr_text = _collect_author_pr_text(entry, config)

    if not author_text and not pr_text:
        return ""

    parts = []
    if author_text:
        parts.append(f"By {author_text}")
    if pr_text:
        parts.append(f"in {pr_text}")
    return "*" + " ".join(parts) + ".*"


@cli.command("add")
@click.option("--title", help="Title for the changelog entry.")
@click.option(
    "--type",
    "entry_type",
    help="Entry type.",
)
@click.option(
    "--project",
    "project_override",
    help="Assign the entry to a project (must match the configured project).",
)
@click.option("--author", "authors", multiple=True, help="GitHub username of an author.")
@click.option(
    "--pr",
    "prs",
    multiple=True,
    type=str,
    help="Related pull request number (repeat for multiple).",
)
@click.option(
    "--description",
    help="Short body text for the entry (skips opening an editor).",
)
@click.pass_obj
def add(
    ctx: CLIContext,
    title: Optional[str],
    entry_type: Optional[str],
    project_override: Optional[str],
    authors: tuple[str, ...],
    prs: tuple[str, ...],
    description: Optional[str],
) -> None:
    """Create a new changelog entry."""
    config = ctx.ensure_config(create_if_missing=True)
    project_root = ctx.project_root

    title = title or _prompt_text("Title")
    if entry_type:
        normalized_type = _normalize_entry_type(entry_type)
        if normalized_type is None:
            raise click.ClickException(
                f"Unknown entry type '{entry_type}'. Expected one of: {', '.join(ENTRY_TYPES)}"
            )
        entry_type = normalized_type
    else:
        entry_type = _prompt_entry_type()

    project_value = (project_override or "").strip() or config.id
    if project_value != config.id:
        raise click.ClickException(f"Unknown project '{project_value}'. Expected '{config.id}'.")

    if authors:
        authors_list = [author.strip() for author in authors if author.strip()]
    else:
        author_value = _prompt_optional("Authors (comma separated)", default="")
        authors_list = (
            [item.strip() for item in author_value.split(",") if item.strip()]
            if author_value
            else []
        )

    body = description or _prompt_entry_body()

    pr_numbers: list[int] = []
    for pr_value in prs:
        pr_value = pr_value.strip()
        if not pr_value:
            continue
        try:
            pr_numbers.append(int(pr_value))
        except ValueError as exc:
            raise click.ClickException(f"PR value '{pr_value}' must be numeric.") from exc

    metadata: dict[str, Any] = {
        "title": title,
        "type": entry_type,
        "project": project_value,
        "authors": authors_list or None,
    }
    if pr_numbers:
        metadata["prs"] = pr_numbers

    path = write_entry(project_root, metadata, body, default_project=config.id)
    log_success(f"entry created: {path.relative_to(project_root)}")


def _render_release_notes(
    entries: list[Entry],
    config: Config,
    *,
    include_emoji: bool = True,
) -> str:
    """Render Markdown sections for the provided entries."""

    if not entries:
        return ""

    entries_by_type: dict[str, list[Entry]] = {}
    for entry in entries:
        entry_type = entry.metadata.get("type", DEFAULT_ENTRY_TYPE)
        entries_by_type.setdefault(entry_type, []).append(entry)

    lines: list[str] = []
    for type_key in ENTRY_EXPORT_ORDER:
        type_entries = entries_by_type.get(type_key) or []
        if not type_entries:
            continue
        section_title = _format_section_title(type_key, include_emoji)
        lines.append(f"## {section_title}")
        lines.append("")
        for entry in type_entries:
            title = entry.metadata.get("title", "Untitled")
            lines.append(f"### {title}")
            lines.append("")
            body = entry.body.strip()
            if body:
                lines.append(body)
                lines.append("")
            author_line = _format_author_line(entry, config)
            if author_line:
                lines.append(author_line)
                lines.append("")

    return "\n".join(lines).strip()


def _render_release_notes_compact(
    entries: list[Entry],
    config: Config,
    *,
    include_emoji: bool = True,
) -> str:
    """Render compact Markdown bullet list for the provided entries."""

    if not entries:
        return ""

    entries_by_type: dict[str, list[Entry]] = {}
    for entry in entries:
        entry_type = entry.metadata.get("type", DEFAULT_ENTRY_TYPE)
        entries_by_type.setdefault(entry_type, []).append(entry)

    lines: list[str] = []
    for type_key in ENTRY_EXPORT_ORDER:
        type_entries = entries_by_type.get(type_key) or []
        if not type_entries:
            continue
        section_title = _format_section_title(type_key, include_emoji)
        lines.append(f"## {section_title}")
        lines.append("")
        for entry in type_entries:
            excerpt = extract_excerpt(entry.body)
            bullet_text = excerpt or entry.metadata.get("title", "Untitled")
            bullet = f"- {bullet_text}"
            author_text, pr_text = _collect_author_pr_text(entry, config)
            suffix_parts: list[str] = []
            if author_text:
                suffix_parts.append(f"by {author_text}")
            if pr_text:
                suffix_parts.append(f"in {pr_text}")
            if suffix_parts:
                bullet = f"{bullet} ({' '.join(suffix_parts)})"
            lines.append(bullet)
        lines.append("")

    return "\n".join(lines).strip()


def _compose_release_document(
    description: Optional[str],
    intro: Optional[str],
    release_notes: str,
) -> str:
    parts: list[str] = []
    if description:
        desc = description.strip()
        if desc:
            parts.append(desc)
    if intro:
        intro_text = intro.strip()
        if intro_text:
            parts.append(intro_text)
    notes = release_notes.strip()
    if notes:
        parts.append(notes)
    return "\n\n".join(parts).strip()


def _release_entry_sort_key(entry: Entry) -> tuple[str, str]:
    title_value = entry.metadata.get("title", "")
    return (title_value.lower(), entry.entry_id)


def _find_release_manifest(project_root: Path, version: str) -> Optional[ReleaseManifest]:
    normalized_version = version.strip()
    for manifest in iter_release_manifests(project_root):
        if manifest.version == normalized_version:
            return manifest
    return None


def _github_release_exists(repository: str, version: str, gh_path: str) -> bool:
    command = [gh_path, "release", "view", version, "--repo", repository]
    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except FileNotFoundError as exc:  # pragma: no cover - handled earlier
        raise click.ClickException("The 'gh' CLI is required but was not found in PATH.") from exc
    except subprocess.CalledProcessError:
        return False


def _latest_semver(project_root: Path) -> tuple[Version, str] | None:
    versions: list[tuple[Version, str]] = []
    for manifest in iter_release_manifests(project_root):
        label = manifest.version
        prefix = ""
        value = label
        if label.startswith(("v", "V")):
            prefix = label[0]
            value = label[1:]
        try:
            parsed = Version(value)
        except InvalidVersion:
            continue
        versions.append((parsed, prefix))
    if not versions:
        return None
    versions.sort(key=lambda item: item[0])
    return versions[-1]


def _bump_version_value(base: Version, bump: str) -> Version:
    major, minor, micro = (list(base.release) + [0, 0, 0])[:3]
    if bump == "major":
        major += 1
        minor = 0
        micro = 0
    elif bump == "minor":
        minor += 1
        micro = 0
    else:
        micro += 1
    return Version(f"{major}.{minor}.{micro}")


def _resolve_release_version(
    project_root: Path,
    explicit: Optional[str],
    bump: Optional[str],
) -> str:
    if explicit and bump:
        raise click.ClickException("Provide either a version argument or a bump flag, not both.")
    if explicit:
        value = explicit.strip()
        if not value:
            raise click.ClickException("Release version cannot be empty.")
        return value
    if not bump:
        raise click.ClickException(
            "Provide a version argument or specify one of --patch/--minor/--major."
        )
    latest = _latest_semver(project_root)
    if latest is None:
        raise click.ClickException(
            "No existing release found to bump from. Supply an explicit version instead."
        )
    base_version, prefix = latest
    next_version = _bump_version_value(base_version, bump)
    prefix_value = prefix or ""
    return f"{prefix_value}{next_version}"


@cli.group("release")
@click.pass_obj
def release_group(ctx: CLIContext) -> None:
    """Manage release manifests, notes, and publishing."""
    ctx.ensure_config()


@release_group.command("create")
@click.argument("version", required=False)
@click.option("--title", help="Display title for the release.")
@click.option("--description", help="Short release description.")
@click.option(
    "--date",
    "release_date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Release date (YYYY-MM-DD). Defaults to today or existing release date.",
)
@click.option(
    "--intro-file",
    type=click.Path(path_type=Path, dir_okay=False),
    help="Markdown file containing introductory notes for the release.",
)
@click.option(
    "--compact/--no-compact",
    default=None,
    help="Render release notes in the compact format.",
)
@click.option(
    "--yes",
    "assume_yes",
    is_flag=True,
    help="Apply detected changes without prompting.",
)
@click.option(
    "--patch",
    "version_bump",
    flag_value="patch",
    default=None,
    help="Bump the patch segment from the latest release.",
)
@click.option(
    "--minor",
    "version_bump",
    flag_value="minor",
    help="Bump the minor segment from the latest release.",
)
@click.option(
    "--major",
    "version_bump",
    flag_value="major",
    help="Bump the major segment from the latest release.",
)
@click.pass_obj
def release_create_cmd(
    ctx: CLIContext,
    version: Optional[str],
    title: Optional[str],
    description: Optional[str],
    release_date: Optional[datetime],
    intro_file: Optional[Path],
    compact: Optional[bool],
    assume_yes: bool,
    version_bump: Optional[str],
) -> None:
    """Create or update a release manifest from unused entries."""
    config = ctx.ensure_config()
    project_root = ctx.project_root

    version = _resolve_release_version(project_root, version, version_bump)

    click_ctx = click.get_current_context()
    existing_manifest = _find_release_manifest(project_root, version)
    if version_bump and existing_manifest is not None:
        raise click.ClickException(
            f"Release '{version}' already exists. Supply a different bump flag or explicit version."
        )
    compact_source = click_ctx.get_parameter_source("compact")
    if compact_source == ParameterSource.DEFAULT:
        compact_flag = config.export_style == EXPORT_STYLE_COMPACT
    else:
        compact_flag = bool(compact)
    release_dir = release_directory(project_root) / version
    manifest_path = release_dir / "manifest.yaml"
    notes_path = release_dir / NOTES_FILENAME

    existing_entries: list[Entry] = []
    existing_entry_ids: set[str] = set()
    if existing_manifest:
        for entry_id in existing_manifest.entries:
            entry = load_release_entry(project_root, existing_manifest, entry_id)
            if entry is None:
                raise click.ClickException(
                    f"Release '{version}' is missing entry file for '{entry_id}'. "
                    "Recreate or repair the release before appending new entries."
                )
            existing_entries.append(entry)
            existing_entry_ids.add(entry.entry_id)

    unused_entries = _collect_unused_entries_for_release(project_root, config)
    if not unused_entries and not existing_entries:
        raise click.ClickException("No unused entries available for release creation.")

    new_entries = [entry for entry in unused_entries if entry.entry_id not in existing_entry_ids]

    combined_entries: dict[str, Entry] = {entry.entry_id: entry for entry in existing_entries}
    for entry in new_entries:
        combined_entries[entry.entry_id] = entry

    entries_sorted = sorted(combined_entries.values(), key=_release_entry_sort_key)
    if not entries_sorted:
        raise click.ClickException("No entries available to include in the release.")

    table = Table(title=f"Entries for {version}")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Status")
    new_entry_ids = {entry.entry_id for entry in new_entries}
    for entry in entries_sorted:
        status = "New" if entry.entry_id in new_entry_ids else "Existing"
        status_style = "green" if status == "New" else "dim"
        table.add_row(
            entry.entry_id,
            entry.metadata.get("title", "Untitled"),
            entry.metadata.get("type", "change"),
            f"[{status_style}]{status}[/{status_style}]",
        )
    _print_renderable(table)

    title_source = click_ctx.get_parameter_source("title")

    release_title = (
        title
        if title_source != ParameterSource.DEFAULT
        else existing_manifest.title
        if existing_manifest
        else f"{config.name} {version}"
    )
    description_value = (
        description.strip()
        if description is not None
        else (existing_manifest.description if existing_manifest else "")
    )

    manifest_intro: Optional[str]
    if intro_file:
        manifest_intro = intro_file.read_text(encoding="utf-8").strip()
    elif existing_manifest:
        manifest_intro = existing_manifest.intro
    else:
        manifest_intro = None

    release_dt = (
        release_date.date()
        if release_date is not None
        else existing_manifest.created
        if existing_manifest
        else date.today()
    )

    release_notes_standard = _render_release_notes(entries_sorted, config, include_emoji=True)
    release_notes_compact = _render_release_notes_compact(
        entries_sorted, config, include_emoji=True
    )

    if compact_source == ParameterSource.DEFAULT:
        prefer_compact = config.export_style == EXPORT_STYLE_COMPACT
        existing_notes_payload = (
            notes_path.read_text(encoding="utf-8") if notes_path.exists() else None
        )
        if existing_notes_payload is not None:
            normalized_existing = existing_notes_payload.rstrip("\n")
            doc_standard = _compose_release_document(
                description_value if description_value else None,
                manifest_intro,
                release_notes_standard,
            ).rstrip("\n")
            doc_compact = _compose_release_document(
                description_value if description_value else None,
                manifest_intro,
                release_notes_compact,
            ).rstrip("\n")
            if normalized_existing == doc_compact:
                prefer_compact = True
            elif normalized_existing == doc_standard:
                prefer_compact = False
        compact_flag = prefer_compact
    else:
        compact_flag = bool(compact)
        existing_notes_payload = (
            notes_path.read_text(encoding="utf-8") if notes_path.exists() else None
        )

    release_notes = release_notes_compact if compact_flag else release_notes_standard

    manifest = ReleaseManifest(
        version=version,
        created=release_dt,
        entries=[entry.entry_id for entry in entries_sorted],
        title=release_title or "",
        description=description_value or "",
        intro=manifest_intro or None,
    )

    readme_content = _compose_release_document(
        manifest.description,
        manifest.intro,
        release_notes,
    )

    manifest_payload = serialize_release_manifest(manifest)
    manifest_exists = manifest_path.exists()
    existing_manifest_payload = (
        manifest_path.read_text(encoding="utf-8") if manifest_exists else None
    )

    def _normalize_block(value: Optional[str]) -> str:
        return (value or "").rstrip("\n")

    changes_required = False
    change_reasons: list[str] = []
    if not release_dir.exists():
        changes_required = True
        change_reasons.append("create release directory")
    if new_entries:
        changes_required = True
        change_reasons.append(f"append {len(new_entries)} new entries")
    if _normalize_block(manifest_payload) != _normalize_block(existing_manifest_payload):
        changes_required = True
        change_reasons.append("update manifest metadata")
    if _normalize_block(readme_content) != _normalize_block(existing_notes_payload):
        changes_required = True
        change_reasons.append("refresh release notes")

    if not changes_required:
        log_success(f"release '{version}' is already up to date.")
        return

    if not assume_yes:
        log_info(f"detected changes for release '{version}':")
        for reason in change_reasons:
            log_info(f"change: {reason}")
        log_info("re-run with --yes to apply these updates.")
        raise SystemExit(1)

    release_dir.mkdir(parents=True, exist_ok=True)
    release_entries_dir = release_dir / "entries"
    release_entries_dir.mkdir(parents=True, exist_ok=True)

    for entry in new_entries:
        source_path = entry.path
        destination_path = release_entries_dir / source_path.name
        if not source_path.exists():
            raise click.ClickException(
                f"Cannot move entry '{entry.entry_id}' because {source_path} is missing."
            )
        if destination_path.exists():
            continue
        source_path.rename(destination_path)

    manifest_path_result = write_release_manifest(
        project_root,
        manifest,
        readme_content,
        overwrite=manifest_exists,
    )

    log_success(f"release manifest written: {manifest_path_result.relative_to(project_root)}")
    if new_entries:
        relative_release_dir = release_entries_dir.relative_to(project_root)
        log_success(f"appended {len(new_entries)} entries to: {relative_release_dir}")
    else:
        log_success(f"updated release metadata for {version}.")


@release_group.command("notes")
@click.argument("identifier")
@click.option(
    "-m",
    "format_choice",
    flag_value="markdown",
    default="markdown",
    help="Render notes as Markdown (default).",
)
@click.option(
    "-j",
    "format_choice",
    flag_value="json",
    help="Render notes as JSON.",
)
@click.option(
    "--compact/--no-compact",
    default=None,
    help="Use the compact layout when rendering Markdown.",
)
@click.option(
    "--no-emoji",
    is_flag=True,
    help="Disable type emoji in Markdown output.",
)
@click.pass_obj
def release_notes_cmd(
    ctx: CLIContext,
    identifier: str,
    format_choice: str,
    compact: Optional[bool],
    no_emoji: bool,
) -> None:
    """Display release notes for a release or the unreleased bucket."""
    config = ctx.ensure_config()
    project_root = ctx.project_root

    if not identifier.strip():
        raise click.ClickException("Provide a release version or '-' for unreleased notes.")

    entry_map, _, _, sorted_entries = _gather_entry_context(project_root)
    resolutions = _resolve_identifiers_sequence(
        [identifier],
        project_root=project_root,
        config=config,
        sorted_entries=sorted_entries,
        entry_map=entry_map,
        allowed_kinds={"release", "unreleased"},
    )
    resolution = resolutions[0]
    manifest = resolution.manifest if resolution.kind == "release" else None

    include_emoji = not no_emoji
    click_ctx = click.get_current_context()
    compact_source = click_ctx.get_parameter_source("compact")
    compact_flag = (
        config.export_style == EXPORT_STYLE_COMPACT
        if compact_source == ParameterSource.DEFAULT
        else bool(compact)
    )
    view = format_choice or "markdown"

    entries_for_output = sorted(resolution.entries, key=_release_entry_sort_key)
    release_index_export = build_entry_release_index(project_root, project=config.id)

    if resolution.kind == "release" and manifest is None:
        raise click.ClickException(f"Release '{identifier}' not found.")

    if view == "json":
        fallback_heading = manifest.title if manifest and manifest.title else resolution.identifier
        fallback_created = manifest.created if manifest else None
        payload = _export_json_payload(
            manifest,
            entries_for_output,
            config,
            release_index_export,
            compact=compact_flag,
            fallback_heading=fallback_heading,
            fallback_created=fallback_created,
        )
        emit_output(json.dumps(payload, indent=2))
        return

    if resolution.kind == "release":
        release_body = (
            _render_release_notes_compact(entries_for_output, config, include_emoji=include_emoji)
            if compact_flag
            else _render_release_notes(entries_for_output, config, include_emoji=include_emoji)
        )
        output = _compose_release_document(
            manifest.description if manifest else "",
            manifest.intro if manifest else None,
            release_body,
        )
    else:
        fallback_heading = "Unreleased Changes"
        release_body = (
            _export_markdown_compact(
                None,
                entries_for_output,
                config,
                release_index_export,
                include_emoji=include_emoji,
                fallback_heading=fallback_heading,
            )
            if compact_flag
            else _export_markdown_release(
                None,
                entries_for_output,
                config,
                release_index_export,
                include_emoji=include_emoji,
                fallback_heading=fallback_heading,
            )
        )
        output = release_body.rstrip("\n")

    emit_output(output)


@release_group.command("publish")
@click.argument("version")
@click.option(
    "--draft/--no-draft",
    default=False,
    help="Create the GitHub release as a draft.",
)
@click.option(
    "--prerelease/--no-prerelease",
    default=False,
    help="Mark the GitHub release as a prerelease.",
)
@click.option(
    "--yes",
    "assume_yes",
    is_flag=True,
    help="Publish without confirmation prompts.",
)
@click.pass_obj
def release_publish_cmd(
    ctx: CLIContext,
    version: str,
    draft: bool,
    prerelease: bool,
    assume_yes: bool,
) -> None:
    """Publish a release to GitHub using the gh CLI."""
    config = ctx.ensure_config()
    project_root = ctx.project_root

    if not config.repository:
        raise click.ClickException(
            "Set the 'repository' field in config.yaml before publishing releases."
        )

    gh_path = shutil.which("gh")
    if gh_path is None:
        raise click.ClickException("The 'gh' CLI is required but was not found in PATH.")

    manifest = _find_release_manifest(project_root, version)
    if manifest is None:
        raise click.ClickException(f"Release '{version}' not found.")

    release_dir = release_directory(project_root) / manifest.version
    notes_path = release_dir / NOTES_FILENAME
    if not notes_path.exists():
        relative_notes = notes_path.relative_to(project_root)
        raise click.ClickException(
            f"Release notes missing at {relative_notes}. Run 'tenzir-changelog release create {manifest.version} --yes' first."
        )

    notes_content = notes_path.read_text(encoding="utf-8").strip()
    if not notes_content:
        raise click.ClickException("Release notes are empty; aborting publish.")

    release_exists = _github_release_exists(config.repository, manifest.version, gh_path)
    if release_exists:
        command = [
            gh_path,
            "release",
            "edit",
            manifest.version,
            "--repo",
            config.repository,
            "--notes-file",
            str(notes_path),
        ]
        if manifest.title:
            command.extend(["--title", manifest.title])
        confirmation_action = "gh release edit"
    else:
        command = [
            gh_path,
            "release",
            "create",
            manifest.version,
            "--repo",
            config.repository,
            "--notes-file",
            str(notes_path),
        ]
        if manifest.title:
            command.extend(["--title", manifest.title])
        if draft:
            command.append("--draft")
        if prerelease:
            command.append("--prerelease")
        confirmation_action = "gh release create"

    if not assume_yes:
        prompt = (
            f"Publish {manifest.version} to GitHub repository {config.repository}? "
            f"This will run '{confirmation_action}'."
        )
        log_info(prompt.lower())
        if not click.confirm(prompt, default=True):
            log_info("aborted release publish.")
            return

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(
            f"'gh' exited with status {exc.returncode}. See output for details."
        ) from exc

    log_success(f"published {manifest.version} to GitHub repository {config.repository}.")


@cli.command("validate")
@click.pass_obj
def validate_cmd(ctx: CLIContext) -> None:
    """Validate entries and release manifests."""
    config = ctx.ensure_config()
    issues = run_validation(ctx.project_root, config)
    if not issues:
        log_success("all changelog files look good")
        return

    for issue in issues:
        severity_label = issue.severity.lower()
        log_error(f"{severity_label} issue at {issue.path}: {issue.message}")
    raise SystemExit(1)


def _export_markdown_release(
    manifest: Optional[ReleaseManifest],
    entries: list[Entry],
    config: Config,
    release_index: dict[str, list[str]],
    *,
    include_emoji: bool = True,
    fallback_heading: str = "Unreleased Changes",
) -> str:
    lines: list[str] = []
    if manifest:
        if manifest.description:
            lines.append(manifest.description.strip())
            lines.append("")
    else:
        heading = fallback_heading or "Unreleased Changes"
        lines.append(f"# {heading}")
        lines.append("")

    if not entries:
        lines.append("No changes found.")
        return "\n".join(lines).strip() + "\n"

    entries_by_type: dict[str, list[Entry]] = {}
    for entry in entries:
        entry_type = entry.metadata.get("type", DEFAULT_ENTRY_TYPE)
        entries_by_type.setdefault(entry_type, []).append(entry)

    for type_key in ENTRY_EXPORT_ORDER:
        type_entries = entries_by_type.get(type_key) or []
        if not type_entries:
            continue
        section_title = _format_section_title(type_key, include_emoji)
        lines.append(f"## {section_title}")
        lines.append("")
        for entry in type_entries:
            metadata = entry.metadata
            title = metadata.get("title", "Untitled")
            lines.append(f"### {title}")
            lines.append("")
            body = entry.body.strip()
            if body:
                lines.append(body)
                lines.append("")
            author_line = _format_author_line(entry, config)
            if author_line:
                lines.append(author_line)
                lines.append("")

    return "\n".join(lines).strip() + "\n"


def _export_markdown_compact(
    manifest: Optional[ReleaseManifest],
    entries: list[Entry],
    config: Config,
    release_index: dict[str, list[str]],
    *,
    include_emoji: bool = True,
    fallback_heading: str = "Unreleased Changes",
) -> str:
    lines: list[str] = []
    if manifest:
        if manifest.description:
            lines.append(manifest.description.strip())
            lines.append("")
    else:
        heading = fallback_heading or "Unreleased Changes"
        lines.append(f"# {heading}")
        lines.append("")

    if not entries:
        lines.append("No changes found.")
        return "\n".join(lines).strip() + "\n"

    entries_by_type: dict[str, list[Entry]] = {}
    for entry in entries:
        entry_type = entry.metadata.get("type", DEFAULT_ENTRY_TYPE)
        entries_by_type.setdefault(entry_type, []).append(entry)

    for type_key in ENTRY_EXPORT_ORDER:
        type_entries = entries_by_type.get(type_key) or []
        if not type_entries:
            continue
        section_title = _format_section_title(type_key, include_emoji)
        lines.append(f"## {section_title}")
        lines.append("")
        for entry in type_entries:
            metadata = entry.metadata
            excerpt = extract_excerpt(entry.body)
            bullet_text = excerpt or metadata.get("title", "Untitled")
            bullet = f"- {bullet_text}"
            author_text, pr_text = _collect_author_pr_text(entry, config)
            suffix_parts: list[str] = []
            if author_text:
                suffix_parts.append(f"by {author_text}")
            if pr_text:
                suffix_parts.append(f"in {pr_text}")
            if suffix_parts:
                bullet = f"{bullet} ({' '.join(suffix_parts)})"
            lines.append(bullet)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _export_json_payload(
    manifest: Optional[ReleaseManifest],
    entries: list[Entry],
    config: Config,
    release_index: dict[str, list[str]],
    *,
    compact: bool = False,
    fallback_heading: str = "Unreleased Changes",
    fallback_created: date | None = None,
) -> dict[str, object]:
    entries_by_type: dict[str, list[Entry]] = {}
    for entry in entries:
        entry_type = entry.metadata.get("type", DEFAULT_ENTRY_TYPE)
        entries_by_type.setdefault(entry_type, []).append(entry)
    ordered_entries: list[Entry] = []
    for type_key in ENTRY_EXPORT_ORDER:
        ordered_entries.extend(entries_by_type.pop(type_key, []))
    for remaining in entries_by_type.values():
        ordered_entries.extend(remaining)

    data: dict[str, object] = {}
    if manifest:
        data.update(
            {
                "version": manifest.version,
                "title": manifest.title or manifest.version,
                "description": manifest.description or None,
                "project": config.id,
                "created": manifest.created.isoformat(),
            }
        )
    else:
        created_value = fallback_created or date.today()
        data.update(
            {
                "version": None,
                "title": fallback_heading if fallback_heading else None,
                "description": None,
                "project": config.id,
                "created": created_value.isoformat(),
            }
        )
    payload_entries = []
    for entry in ordered_entries:
        version_candidates = release_index.get(entry.entry_id, []) or []
        version_value: str | None
        if manifest and manifest.version:
            version_value = manifest.version
        else:
            version_value = next(iter(version_candidates), None)
        payload_entries.append(_entry_to_dict(entry, config, version_value, compact=compact))
    data["entries"] = payload_entries
    if compact:
        data["compact"] = True
    return data


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for console_scripts."""
    argv = argv if argv is not None else sys.argv[1:]

    # If no command is specified, default to 'show'
    # Check if any arg is a known command
    has_command = any(arg in cli.commands for arg in argv)
    if not has_command:
        # No command found, inject 'show' at the end (after options like --root)
        argv = list(argv) + ["show"]

    try:
        cli.main(args=list(argv), prog_name="tenzir-changelog", standalone_mode=False)
    except click.ClickException as exc:
        exc.show(file=sys.stderr)
        exit_code = getattr(exc, "exit_code", 1)
        return exit_code if isinstance(exit_code, int) else 1
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 0
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
