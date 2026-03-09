#!/usr/bin/env python3
"""
Notebook Library Management for NotebookLM
Manages a library of NotebookLM notebooks with metadata
"""

import json
import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def extract_notebook_id(url: str) -> Optional[str]:
    """Extract notebook ID from a NotebookLM URL.

    Args:
        url: NotebookLM URL like https://notebooklm.google.com/notebook/NOTEBOOK_ID

    Returns:
        The notebook ID string, or None if not found
    """
    match = re.search(r'/notebook/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None


class NotebookLibrary:
    """Manages a collection of NotebookLM notebooks with metadata"""

    def __init__(self):
        """Initialize the notebook library"""
        # Store data within the skill directory
        skill_dir = Path(__file__).parent.parent
        self.data_dir = skill_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.library_file = self.data_dir / "library.json"
        self.notebooks: Dict[str, Dict[str, Any]] = {}
        self.active_notebook_id: Optional[str] = None

        # Load existing library
        self._load_library()

    def _load_library(self):
        """Load library from disk"""
        if self.library_file.exists():
            try:
                with open(self.library_file, 'r') as f:
                    data = json.load(f)
                    self.notebooks = data.get('notebooks', {})
                    self.active_notebook_id = data.get('active_notebook_id')

                    # Migration: auto-extract remote_id from URL for existing entries
                    migrated = False
                    for nb in self.notebooks.values():
                        if 'remote_id' not in nb and 'url' in nb:
                            remote_id = extract_notebook_id(nb['url'])
                            if remote_id:
                                nb['remote_id'] = remote_id
                                migrated = True
                        if 'sources' not in nb:
                            nb['sources'] = []
                            migrated = True

                    if migrated:
                        self._save_library()

                    print(f"Loaded library with {len(self.notebooks)} notebooks")
            except Exception as e:
                print(f"Error loading library: {e}")
                self.notebooks = {}
                self.active_notebook_id = None
        else:
            self._save_library()

    def _save_library(self):
        """Save library to disk"""
        try:
            data = {
                'notebooks': self.notebooks,
                'active_notebook_id': self.active_notebook_id,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.library_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving library: {e}")

    def add_notebook(
        self,
        url: str,
        name: str,
        description: str,
        topics: List[str],
        content_types: Optional[List[str]] = None,
        use_cases: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add a new notebook to the library"""
        # Generate ID from name
        notebook_id = name.lower().replace(' ', '-').replace('_', '-')

        # Check for duplicates
        if notebook_id in self.notebooks:
            raise ValueError(f"Notebook with ID '{notebook_id}' already exists")

        # Extract remote_id from URL
        remote_id = extract_notebook_id(url)

        # Create notebook object
        notebook = {
            'id': notebook_id,
            'url': url,
            'remote_id': remote_id,
            'name': name,
            'description': description,
            'topics': topics,
            'content_types': content_types or [],
            'use_cases': use_cases or [],
            'tags': tags or [],
            'sources': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'use_count': 0,
            'last_used': None
        }

        # Add to library
        self.notebooks[notebook_id] = notebook

        # Set as active if it's the first notebook
        if len(self.notebooks) == 1:
            self.active_notebook_id = notebook_id

        self._save_library()

        print(f"Added notebook: {name} ({notebook_id})")
        if remote_id:
            print(f"  Remote ID: {remote_id}")
        return notebook

    def remove_notebook(self, notebook_id: str) -> bool:
        """Remove a notebook from the library"""
        if notebook_id in self.notebooks:
            del self.notebooks[notebook_id]

            # Clear active if it was removed
            if self.active_notebook_id == notebook_id:
                self.active_notebook_id = None
                if self.notebooks:
                    self.active_notebook_id = list(self.notebooks.keys())[0]

            self._save_library()
            print(f"Removed notebook: {notebook_id}")
            return True

        print(f"Notebook not found: {notebook_id}")
        return False

    def update_notebook(
        self,
        notebook_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
        content_types: Optional[List[str]] = None,
        use_cases: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update notebook metadata"""
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook not found: {notebook_id}")

        notebook = self.notebooks[notebook_id]

        if name is not None:
            notebook['name'] = name
        if description is not None:
            notebook['description'] = description
        if topics is not None:
            notebook['topics'] = topics
        if content_types is not None:
            notebook['content_types'] = content_types
        if use_cases is not None:
            notebook['use_cases'] = use_cases
        if tags is not None:
            notebook['tags'] = tags
        if url is not None:
            notebook['url'] = url
            remote_id = extract_notebook_id(url)
            if remote_id:
                notebook['remote_id'] = remote_id

        notebook['updated_at'] = datetime.now().isoformat()

        self._save_library()
        print(f"Updated notebook: {notebook['name']}")
        return notebook

    def get_notebook(self, notebook_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific notebook by ID"""
        return self.notebooks.get(notebook_id)

    def list_notebooks(self) -> List[Dict[str, Any]]:
        """List all notebooks in the library"""
        return list(self.notebooks.values())

    def search_notebooks(self, query: str) -> List[Dict[str, Any]]:
        """Search notebooks by query"""
        query_lower = query.lower()
        results = []

        for notebook in self.notebooks.values():
            searchable = [
                notebook['name'].lower(),
                notebook['description'].lower(),
                ' '.join(notebook['topics']).lower(),
                ' '.join(notebook['tags']).lower(),
                ' '.join(notebook.get('use_cases', [])).lower()
            ]

            if any(query_lower in field for field in searchable):
                results.append(notebook)

        return results

    def select_notebook(self, notebook_id: str) -> Dict[str, Any]:
        """Set a notebook as active"""
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook not found: {notebook_id}")

        self.active_notebook_id = notebook_id
        self._save_library()

        notebook = self.notebooks[notebook_id]
        print(f"Activated notebook: {notebook['name']}")
        return notebook

    def get_active_notebook(self) -> Optional[Dict[str, Any]]:
        """Get the currently active notebook"""
        if self.active_notebook_id:
            return self.notebooks.get(self.active_notebook_id)
        return None

    def increment_use_count(self, notebook_id: str) -> Dict[str, Any]:
        """Increment usage counter for a notebook"""
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook not found: {notebook_id}")

        notebook = self.notebooks[notebook_id]
        notebook['use_count'] += 1
        notebook['last_used'] = datetime.now().isoformat()

        self._save_library()
        return notebook

    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics"""
        total_notebooks = len(self.notebooks)
        total_topics = set()
        total_use_count = 0

        for notebook in self.notebooks.values():
            total_topics.update(notebook['topics'])
            total_use_count += notebook['use_count']

        most_used = None
        if self.notebooks:
            most_used = max(
                self.notebooks.values(),
                key=lambda n: n['use_count']
            )

        return {
            'total_notebooks': total_notebooks,
            'total_topics': len(total_topics),
            'total_use_count': total_use_count,
            'active_notebook': self.get_active_notebook(),
            'most_used_notebook': most_used,
            'library_path': str(self.library_file)
        }


def main():
    """Command-line interface for notebook management"""
    parser = argparse.ArgumentParser(description='Manage NotebookLM library')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a notebook')
    add_parser.add_argument('--url', required=True, help='NotebookLM URL')
    add_parser.add_argument('--name', required=True, help='Display name')
    add_parser.add_argument('--description', required=True, help='Description')
    add_parser.add_argument('--topics', required=True, help='Comma-separated topics')
    add_parser.add_argument('--use-cases', help='Comma-separated use cases')
    add_parser.add_argument('--tags', help='Comma-separated tags')

    # List command
    subparsers.add_parser('list', help='List all notebooks')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search notebooks')
    search_parser.add_argument('--query', required=True, help='Search query')

    # Activate command
    activate_parser = subparsers.add_parser('activate', help='Set active notebook')
    activate_parser.add_argument('--id', required=True, help='Notebook ID')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a notebook')
    remove_parser.add_argument('--id', required=True, help='Notebook ID')

    # Stats command
    subparsers.add_parser('stats', help='Show library statistics')

    # Create command (creates notebook remotely via API)
    create_parser = subparsers.add_parser('create', help='Create a new notebook on NotebookLM')
    create_parser.add_argument('--name', required=True, help='Notebook title')
    create_parser.add_argument('--description', default='', help='Description')
    create_parser.add_argument('--topics', default='', help='Comma-separated topics')

    # Sync command (sync local library with remote)
    subparsers.add_parser('sync', help='Sync local library with remote notebooks')

    args = parser.parse_args()

    # Initialize library
    library = NotebookLibrary()

    # Execute command
    if args.command == 'add':
        topics = [t.strip() for t in args.topics.split(',')]
        use_cases = [u.strip() for u in args.use_cases.split(',')] if args.use_cases else None
        tags = [t.strip() for t in args.tags.split(',')] if args.tags else None

        notebook = library.add_notebook(
            url=args.url,
            name=args.name,
            description=args.description,
            topics=topics,
            use_cases=use_cases,
            tags=tags
        )
        print(json.dumps(notebook, indent=2))

    elif args.command == 'list':
        notebooks = library.list_notebooks()
        if notebooks:
            print("\nNotebook Library:")
            for notebook in notebooks:
                active = " [ACTIVE]" if notebook['id'] == library.active_notebook_id else ""
                print(f"\n  {notebook['name']}{active}")
                print(f"     ID: {notebook['id']}")
                if notebook.get('remote_id'):
                    print(f"     Remote ID: {notebook['remote_id']}")
                print(f"     Topics: {', '.join(notebook['topics'])}")
                print(f"     Sources: {len(notebook.get('sources', []))}")
                print(f"     Uses: {notebook['use_count']}")
        else:
            print("Library is empty. Add notebooks with: notebook_manager.py add")

    elif args.command == 'search':
        results = library.search_notebooks(args.query)
        if results:
            print(f"\nFound {len(results)} notebooks:")
            for notebook in results:
                print(f"\n  {notebook['name']} ({notebook['id']})")
                print(f"     {notebook['description']}")
        else:
            print(f"No notebooks found for: {args.query}")

    elif args.command == 'activate':
        notebook = library.select_notebook(args.id)
        print(f"Now using: {notebook['name']}")

    elif args.command == 'remove':
        if library.remove_notebook(args.id):
            print("Notebook removed from library")

    elif args.command == 'stats':
        stats = library.get_stats()
        print("\nLibrary Statistics:")
        print(f"  Total notebooks: {stats['total_notebooks']}")
        print(f"  Total topics: {stats['total_topics']}")
        print(f"  Total uses: {stats['total_use_count']}")
        if stats['active_notebook']:
            print(f"  Active: {stats['active_notebook']['name']}")
        if stats['most_used_notebook']:
            print(f"  Most used: {stats['most_used_notebook']['name']} ({stats['most_used_notebook']['use_count']} uses)")
        print(f"  Library path: {stats['library_path']}")

    elif args.command == 'create':
        from client import run_async, get_client

        async def _create():
            async with await get_client() as client:
                nb = await client.notebooks.create(args.name)
                return nb

        try:
            remote_nb = run_async(_create())
            url = f"https://notebooklm.google.com/notebook/{remote_nb.id}"
            topics = [t.strip() for t in args.topics.split(',')] if args.topics else ['general']
            notebook = library.add_notebook(
                url=url,
                name=args.name,
                description=args.description or f"Notebook: {args.name}",
                topics=topics
            )
            print(f"Created notebook remotely: {remote_nb.title}")
            print(f"  URL: {url}")
        except Exception as e:
            print(f"Error creating notebook: {e}")

    elif args.command == 'sync':
        from client import run_async, get_client

        async def _sync():
            async with await get_client() as client:
                return await client.notebooks.list()

        try:
            remote_notebooks = run_async(_sync())
            print(f"\nRemote notebooks ({len(remote_notebooks)}):")
            for rnb in remote_notebooks:
                print(f"  {rnb.title} (id: {rnb.id}, sources: {rnb.sources_count})")

                # Check if already in local library
                found = False
                for local_nb in library.notebooks.values():
                    if local_nb.get('remote_id') == rnb.id:
                        found = True
                        break

                if not found:
                    print(f"    -> Not in local library. Add with:")
                    url = f"https://notebooklm.google.com/notebook/{rnb.id}"
                    print(f"       notebook_manager.py add --url \"{url}\" --name \"{rnb.title}\" --description \"...\" --topics \"...\"")
        except Exception as e:
            print(f"Error syncing: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
