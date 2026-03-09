#!/usr/bin/env python3
"""
Source Management for NotebookLM
Manages uploading and listing sources in NotebookLM notebooks.
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from client import run_async, get_client
from notebook_manager import NotebookLibrary, extract_notebook_id


def resolve_remote_id(args) -> str:
    """Resolve the remote notebook ID from args or active notebook.

    Args:
        args: Parsed argparse args with optional notebook_id/notebook_url

    Returns:
        Remote notebook ID string
    """
    # Direct remote ID
    if getattr(args, 'notebook_id', None):
        return args.notebook_id

    # From URL
    if getattr(args, 'notebook_url', None):
        remote_id = extract_notebook_id(args.notebook_url)
        if remote_id:
            return remote_id
        raise ValueError(f"Could not extract notebook ID from URL: {args.notebook_url}")

    # From active notebook
    library = NotebookLibrary()
    active = library.get_active_notebook()
    if active and active.get('remote_id'):
        print(f"Using active notebook: {active['name']}")
        return active['remote_id']

    raise ValueError(
        "No notebook specified. Use --notebook-id, --notebook-url, "
        "or set an active notebook with: notebook_manager.py activate --id ID"
    )


def cmd_add(args):
    """Add a source to a notebook."""
    try:
        remote_id = resolve_remote_id(args)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    source_type = args.type
    value = args.value

    async def _add():
        async with await get_client() as client:
            if source_type == 'url' or source_type == 'youtube':
                print(f"Adding URL source: {value}")
                source = await client.sources.add_url(remote_id, value, wait=True)
            elif source_type == 'file':
                file_path = Path(value)
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {value}")
                print(f"Adding file source: {value}")
                source = await client.sources.add_file(remote_id, file_path, wait=True)
            elif source_type == 'text':
                title = getattr(args, 'title', None) or 'Text Source'
                print(f"Adding text source: {title}")
                source = await client.sources.add_text(remote_id, title, value, wait=True)
            else:
                raise ValueError(f"Unknown source type: {source_type}")

            return source

    try:
        source = run_async(_add())
        print(f"Source added successfully!")
        print(f"  ID: {source.id}")
        print(f"  Title: {source.title}")
        print(f"  Type: {source.kind}")
        return 0
    except Exception as e:
        print(f"Error adding source: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_list(args):
    """List sources in a notebook."""
    try:
        remote_id = resolve_remote_id(args)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    async def _list():
        async with await get_client() as client:
            return await client.sources.list(remote_id)

    try:
        sources = run_async(_list())
        if sources:
            print(f"\nSources ({len(sources)}):")
            for src in sources:
                print(f"\n  {src.title or '(untitled)'}")
                print(f"     ID: {src.id}")
                print(f"     Type: {src.kind}")
                if src.url:
                    print(f"     URL: {src.url}")
        else:
            print("No sources in this notebook.")
        return 0
    except Exception as e:
        print(f"Error listing sources: {e}")
        return 1


def cmd_delete(args):
    """Delete a source from a notebook."""
    try:
        remote_id = resolve_remote_id(args)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    async def _delete():
        async with await get_client() as client:
            return await client.sources.delete(remote_id, args.source_id)

    try:
        result = run_async(_delete())
        if result:
            print(f"Source deleted: {args.source_id}")
        else:
            print(f"Failed to delete source: {args.source_id}")
        return 0
    except Exception as e:
        print(f"Error deleting source: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description='Manage NotebookLM sources')

    # Common notebook arguments
    notebook_args = argparse.ArgumentParser(add_help=False)
    notebook_args.add_argument('--notebook-id', help='Remote notebook ID')
    notebook_args.add_argument('--notebook-url', help='NotebookLM notebook URL')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add command
    add_parser = subparsers.add_parser('add', parents=[notebook_args], help='Add a source')
    add_parser.add_argument('--type', required=True, choices=['url', 'file', 'text', 'youtube'],
                           help='Source type')
    add_parser.add_argument('--value', required=True, help='URL, file path, or text content')
    add_parser.add_argument('--title', help='Title for text sources')

    # List command
    subparsers.add_parser('list', parents=[notebook_args], help='List sources')

    # Delete command
    delete_parser = subparsers.add_parser('delete', parents=[notebook_args], help='Delete a source')
    delete_parser.add_argument('--source-id', required=True, help='Source ID to delete')

    args = parser.parse_args()

    if args.command == 'add':
        return cmd_add(args)
    elif args.command == 'list':
        return cmd_list(args)
    elif args.command == 'delete':
        return cmd_delete(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
