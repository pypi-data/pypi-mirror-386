from __future__ import annotations

import argparse
from typing import Optional

from ..types import ProgramTokens, TNFRGraph

__all__: tuple[str, ...]


def main(argv: Optional[list[str]] = None) -> int: ...


def add_common_args(parser: argparse.ArgumentParser) -> None: ...


def add_grammar_args(parser: argparse.ArgumentParser) -> None: ...


def add_grammar_selector_args(parser: argparse.ArgumentParser) -> None: ...


def add_history_export_args(parser: argparse.ArgumentParser) -> None: ...


def add_canon_toggle(parser: argparse.ArgumentParser) -> None: ...


def build_basic_graph(args: argparse.Namespace) -> TNFRGraph: ...


def apply_cli_config(G: TNFRGraph, args: argparse.Namespace) -> None: ...


def register_callbacks_and_observer(G: TNFRGraph) -> None: ...


def resolve_program(
    args: argparse.Namespace, default: Optional[ProgramTokens] = None
) -> Optional[ProgramTokens]: ...


def run_program(
    G: Optional[TNFRGraph],
    program: Optional[ProgramTokens],
    args: argparse.Namespace,
) -> TNFRGraph: ...
