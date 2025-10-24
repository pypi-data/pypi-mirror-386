"""Command-line helpers for inspecting and managing explainer plugins."""

from __future__ import annotations

import argparse
import pprint
from collections.abc import Iterable, Mapping
from typing import Any, Sequence

from .registry import (
    find_explanation_descriptor,
    find_interval_descriptor,
    find_plot_builder_descriptor,
    find_plot_renderer_descriptor,
    find_plot_style_descriptor,
    list_explanation_descriptors,
    list_interval_descriptors,
    list_plot_builder_descriptors,
    list_plot_renderer_descriptors,
    list_plot_style_descriptors,
    mark_explanation_trusted,
    mark_explanation_untrusted,
    mark_interval_trusted,
    mark_interval_untrusted,
    mark_plot_builder_trusted,
    mark_plot_builder_untrusted,
    mark_plot_renderer_trusted,
    mark_plot_renderer_untrusted,
)

_LIST_KIND_CHOICES = (
    "explanations",
    "intervals",
    "plot-builders",
    "plot-renderers",
    "plots",
    "all",
)
_SHOW_KIND_CHOICES = _LIST_KIND_CHOICES[:-1]
_TRUST_KIND_CHOICES = _LIST_KIND_CHOICES[:-2]

_SINGULAR_LABELS = {
    "explanations": "Explanation plugin",
    "intervals": "Interval plugin",
    "plot-builders": "Plot builder",
    "plot-renderers": "Plot renderer",
    "plots": "Plot style",
}


def _string_tuple(value: Any) -> Sequence[str]:
    """Normalize arbitrary metadata values into a tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Iterable):
        result: list[str] = []
        for item in value:
            if item:
                result.append(str(item))
        return tuple(result)
    return ()


def _emit_header(title: str) -> None:
    """Print a section header for CLI output."""
    print(title)
    print("=" * len(title))


def _format_common_metadata(metadata: Mapping[str, Any]) -> str:
    """Render a concise key summary for plugin metadata dictionaries."""
    name = metadata.get("name", "<unnamed>")
    schema = metadata.get("schema_version", "?")
    return f"name={name}, schema_version={schema}"


def _emit_explanation_descriptor(descriptor) -> None:
    """Display an explanation plugin descriptor in human-readable form."""
    meta = descriptor.metadata
    modes = ", ".join(_string_tuple(meta.get("modes"))) or "-"
    tasks = ", ".join(_string_tuple(meta.get("tasks"))) or "-"
    interval = ", ".join(_string_tuple(meta.get("interval_dependency"))) or "-"
    plot = ", ".join(_string_tuple(meta.get("plot_dependency"))) or "-"
    fallbacks = ", ".join(_string_tuple(meta.get("fallbacks")))
    trust_state = "trusted" if descriptor.trusted else "untrusted"
    print(f"  - {descriptor.identifier} ({trust_state}; {_format_common_metadata(meta)})")
    print(f"    modes={modes}; tasks={tasks}")
    print(f"    interval_dependency={interval}; plot_dependency={plot}")
    if fallbacks:
        print(f"    fallbacks={fallbacks}")


def _emit_interval_descriptor(descriptor) -> None:
    """Display an interval calibrator descriptor for the CLI."""
    meta = descriptor.metadata
    modes = ", ".join(_string_tuple(meta.get("modes"))) or "-"
    deps = ", ".join(_string_tuple(meta.get("dependencies"))) or "-"
    trust_state = "trusted" if descriptor.trusted else "untrusted"
    print(f"  - {descriptor.identifier} ({trust_state}; {_format_common_metadata(meta)})")
    print(f"    modes={modes}; dependencies={deps}")


def _emit_plot_descriptor(descriptor) -> None:
    """Display a plot style descriptor along with fallback details."""
    meta = descriptor.metadata
    builder = meta.get("builder_id", "-")
    renderer = meta.get("renderer_id", "-")
    fallbacks = ", ".join(_string_tuple(meta.get("fallbacks"))) or "-"
    print(f"  - {descriptor.identifier} (style)")
    print(f"    builder={builder}; renderer={renderer}; fallbacks={fallbacks}")
    extras: list[str] = []
    if "is_default" in meta:
        extras.append(f"is_default={'yes' if meta.get('is_default') else 'no'}")
    if "legacy_compatible" in meta:
        extras.append(f"legacy_compatible={'yes' if meta.get('legacy_compatible') else 'no'}")
    default_for = ", ".join(_string_tuple(meta.get("default_for"))) or ""
    if default_for:
        extras.append(f"default_for={default_for}")
    if extras:
        print(f"    {'; '.join(extras)}")


def _emit_plot_builder_descriptor(descriptor) -> None:
    """Display a plot builder descriptor with trust context."""

    meta = descriptor.metadata
    trust_state = "trusted" if descriptor.trusted else "untrusted"
    style = meta.get("style", "-")
    capabilities = ", ".join(_string_tuple(meta.get("capabilities"))) or "-"
    outputs = ", ".join(_string_tuple(meta.get("output_formats"))) or "-"
    dependencies = ", ".join(_string_tuple(meta.get("dependencies"))) or "-"
    print(f"  - {descriptor.identifier} ({trust_state}; {_format_common_metadata(meta)})")
    print(f"    style={style}; capabilities={capabilities}")
    print(f"    output_formats={outputs}; dependencies={dependencies}")
    if "legacy_compatible" in meta:
        legacy = "yes" if meta.get("legacy_compatible") else "no"
        print(f"    legacy_compatible={legacy}")


def _emit_plot_renderer_descriptor(descriptor) -> None:
    """Display a plot renderer descriptor with trust context."""

    meta = descriptor.metadata
    trust_state = "trusted" if descriptor.trusted else "untrusted"
    capabilities = ", ".join(_string_tuple(meta.get("capabilities"))) or "-"
    outputs = ", ".join(_string_tuple(meta.get("output_formats"))) or "-"
    dependencies = ", ".join(_string_tuple(meta.get("dependencies"))) or "-"
    interactive = "yes" if meta.get("supports_interactive") else "no"
    print(f"  - {descriptor.identifier} ({trust_state}; {_format_common_metadata(meta)})")
    print(f"    capabilities={capabilities}; output_formats={outputs}")
    print(f"    supports_interactive={interactive}; dependencies={dependencies}")


def _cmd_list(args: argparse.Namespace) -> int:
    """Handle the `plugins list` subcommand."""
    kind = args.kind
    trusted_only = args.trusted_only

    if kind in ("explanations", "all"):
        descriptors = list_explanation_descriptors(trusted_only=trusted_only)
        _emit_header("Explanation plugins")
        if not descriptors:
            print("  <none>")
        else:
            for descriptor in descriptors:
                _emit_explanation_descriptor(descriptor)
        if kind == "all":
            print()

    if kind in ("intervals", "all"):
        descriptors = list_interval_descriptors(trusted_only=trusted_only)
        _emit_header("Interval calibrators")
        if not descriptors:
            print("  <none>")
        else:
            for descriptor in descriptors:
                _emit_interval_descriptor(descriptor)
        if kind == "all":
            print()

    if kind in ("plot-builders", "all"):
        descriptors = list_plot_builder_descriptors(trusted_only=trusted_only)
        _emit_header("Plot builders")
        if not descriptors:
            print("  <none>")
        else:
            for descriptor in descriptors:
                _emit_plot_builder_descriptor(descriptor)
        if kind == "all":
            print()

    if kind in ("plot-renderers", "all"):
        descriptors = list_plot_renderer_descriptors(trusted_only=trusted_only)
        _emit_header("Plot renderers")
        if not descriptors:
            print("  <none>")
        else:
            for descriptor in descriptors:
                _emit_plot_renderer_descriptor(descriptor)
        if kind == "all":
            print()

    if kind in ("plots", "all"):
        descriptors = list_plot_style_descriptors()
        _emit_header("Plot styles")
        if not descriptors:
            print("  <none>")
        else:
            for descriptor in descriptors:
                _emit_plot_descriptor(descriptor)

    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    """Handle the `plugins show` subcommand."""
    identifier = args.identifier
    kind = args.kind
    if kind == "explanations":
        descriptor = find_explanation_descriptor(identifier)
    elif kind == "intervals":
        descriptor = find_interval_descriptor(identifier)
    elif kind == "plot-builders":
        descriptor = find_plot_builder_descriptor(identifier)
    elif kind == "plot-renderers":
        descriptor = find_plot_renderer_descriptor(identifier)
    else:
        descriptor = find_plot_style_descriptor(identifier)

    if descriptor is None:
        label = _SINGULAR_LABELS.get(kind, kind.capitalize())
        print(f"{label} '{identifier}' is not registered")
        return 1

    meta = dict(descriptor.metadata)
    print(f"Identifier : {descriptor.identifier}")
    if hasattr(descriptor, "trusted"):
        print(f"Trusted    : {'yes' if descriptor.trusted else 'no'}")
    print("Metadata   :")
    print(pprint.pformat(meta, sort_dicts=True))
    return 0


def _cmd_trust(args: argparse.Namespace) -> int:
    """Handle the `plugins trust|untrust` subcommand."""
    identifier = args.identifier
    kind = args.kind
    action = args.action

    if kind == "explanations":
        marker = mark_explanation_trusted if action == "trust" else mark_explanation_untrusted
    elif kind == "intervals":
        marker = mark_interval_trusted if action == "trust" else mark_interval_untrusted
    elif kind == "plot-builders":
        marker = mark_plot_builder_trusted if action == "trust" else mark_plot_builder_untrusted
    else:
        marker = mark_plot_renderer_trusted if action == "trust" else mark_plot_renderer_untrusted

    try:
        descriptor = marker(identifier)
    except KeyError as exc:  # pragma: no cover - exercised via CLI tests
        message = exc.args[0] if exc.args else str(exc)
        print(message)
        return 1

    state = "trusted" if action == "trust" else "untrusted"
    print(f"Marked '{descriptor.identifier}' as {state}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the plugin CLI entry point and return the exit code."""
    parser = argparse.ArgumentParser(
        description="Inspect and manage calibrated_explanations plugin metadata",
    )
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List registered plugins")
    list_parser.add_argument(
        "kind",
        choices=_LIST_KIND_CHOICES,
        nargs="?",
        default="explanations",
        help="Plugin category to list",
    )
    list_parser.add_argument(
        "--trusted-only",
        action="store_true",
        help="Only display plugins marked as trusted",
    )
    list_parser.set_defaults(func=_cmd_list)

    show_parser = subparsers.add_parser("show", help="Show metadata for a plugin")
    show_parser.add_argument("identifier", help="Plugin identifier to inspect")
    show_parser.add_argument(
        "--kind",
        choices=_SHOW_KIND_CHOICES,
        default="explanations",
        help="Plugin category to inspect",
    )
    show_parser.set_defaults(func=_cmd_show)

    trust_parser = subparsers.add_parser(
        "trust",
        help="Mark a plugin as trusted",
    )
    trust_parser.add_argument("identifier", help="Plugin identifier")
    trust_parser.add_argument(
        "--kind",
        choices=_TRUST_KIND_CHOICES,
        default="explanations",
        help="Plugin category to mark as trusted",
    )
    trust_parser.set_defaults(func=_cmd_trust, action="trust")

    untrust_parser = subparsers.add_parser(
        "untrust",
        help="Remove a plugin from the trusted set",
    )
    untrust_parser.add_argument("identifier", help="Plugin identifier")
    untrust_parser.add_argument(
        "--kind",
        choices=_TRUST_KIND_CHOICES,
        default="explanations",
        help="Plugin category to mark as untrusted",
    )
    untrust_parser.set_defaults(func=_cmd_trust, action="untrust")

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits with sys.exit(2) on invalid args; catch and return code
        # but first print help if no command was provided
        if not getattr(exc, "code", None) or exc.code != 0:
            parser.print_help()
        return exc.code
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import sys

    sys.exit(main())
