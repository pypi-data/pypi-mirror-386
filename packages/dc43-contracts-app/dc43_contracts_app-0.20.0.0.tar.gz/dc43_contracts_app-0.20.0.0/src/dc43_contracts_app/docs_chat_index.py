from __future__ import annotations

"""CLI entry point for building the docs chat FAISS index offline."""

import argparse
import sys
from pathlib import Path
from typing import Iterable

from .config import ContractsAppConfig, DocsChatConfig, load_config
from .docs_chat import (
    DocsChatError,
    configure,
    describe_configuration,
    status,
    warm_up,
)
from .workspace import ContractsAppWorkspace


def _workspace_from_root(root: Path) -> ContractsAppWorkspace:
    root.mkdir(parents=True, exist_ok=True)
    workspace = ContractsAppWorkspace(
        root=root,
        contracts_dir=root / "contracts",
        data_dir=root / "data",
        records_dir=root / "records",
        datasets_file=root / "records" / "datasets.json",
        dq_status_dir=root / "records" / "dq_state" / "status",
        data_products_file=root / "records" / "data_products.json",
    )
    workspace.ensure()
    return workspace


def _apply_overrides(config: ContractsAppConfig, args: argparse.Namespace) -> DocsChatConfig:
    docs_chat = config.docs_chat
    docs_chat.enabled = True

    if args.docs_path:
        docs_chat.docs_path = Path(args.docs_path).expanduser()
    if args.code_paths is not None:
        docs_chat.code_paths = tuple(Path(item).expanduser() for item in args.code_paths)
    if args.disable_code:
        docs_chat.code_paths = ()
    if args.embedding_provider:
        docs_chat.embedding_provider = args.embedding_provider
    if args.embedding_model:
        docs_chat.embedding_model = args.embedding_model

    if args.workspace_root:
        config.workspace.root = Path(args.workspace_root).expanduser()

    return docs_chat


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-compute the dc43 documentation assistant index so deployments can "
            "reuse a cached FAISS store instead of embedding content on first run."
        )
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        help="Path to the contracts app TOML configuration (defaults to environment lookup)",
    )
    parser.add_argument(
        "--workspace-root",
        help="Directory where the workspace and docs-chat index will be stored",
    )
    parser.add_argument(
        "--docs-path",
        help="Override the documentation directory to index",
    )
    parser.add_argument(
        "--code-path",
        dest="code_paths",
        action="append",
        help="Repeatable flag specifying code directories to include in the index",
    )
    parser.add_argument(
        "--disable-code",
        action="store_true",
        help="Skip code indexing and only embed Markdown documentation",
    )
    parser.add_argument(
        "--embedding-provider",
        help="Embedding backend to use (for example 'openai' or 'huggingface')",
    )
    parser.add_argument(
        "--embedding-model",
        help="Embedding model identifier to use when rebuilding the index",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = load_config(args.config_path)
    docs_chat_config = _apply_overrides(config, args)

    workspace_root = config.workspace.root or Path.cwd() / "dc43_docs_chat"
    workspace = _workspace_from_root(workspace_root)

    configure(docs_chat_config, workspace)
    summary = describe_configuration()

    def _emit(detail: str) -> None:
        print(detail, file=sys.stdout, flush=True)

    _emit("Resolved docs chat configuration:")
    _emit(f"- Workspace: {summary.workspace_root}")
    _emit(f"- Documentation source: {summary.docs_root}")
    if summary.code_paths:
        _emit(f"- Code sources ({len(summary.code_paths)}):")
        for path in summary.code_paths:
            _emit(f"  • {path}")
    else:
        _emit("- Code sources: none")
    _emit(f"- Index directory: {summary.index_dir}")
    _emit(
        "- Embedding backend: "
        f"{summary.embedding_provider} ({summary.embedding_model})"
    )
    _emit(
        "- Chat provider: "
        f"{docs_chat_config.provider} ({docs_chat_config.model})"
    )

    status_payload = status()
    if not status_payload.ready:
        message = status_payload.message or (
            "The documentation assistant is not ready. Check your configuration and retry."
        )
        print(f"⚠️ {message}", file=sys.stderr, flush=True)
        return 1

    index_dir = summary.index_dir
    manifest_path = index_dir / "manifest.json"
    index_path = index_dir / "index.faiss"
    cache_preexisting = manifest_path.exists() and index_path.exists()

    try:
        warm_up(block=True, progress=_emit)
    except DocsChatError as exc:  # pragma: no cover - exercised in CLI smoke tests
        parser.error(str(exc))
        return 1

    cache_available = manifest_path.exists() and index_path.exists()

    _emit("")
    _emit("Warm-up result:")
    if cache_available:
        if cache_preexisting:
            _emit("- ✅ Documentation index ready (reused existing cache).")
        else:
            _emit("- ✅ Documentation index ready (generated new cache).")
    else:
        _emit("- ⚠️ Documentation index files were not created. Check permissions and retry.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
