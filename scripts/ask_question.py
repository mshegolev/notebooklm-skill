#!/usr/bin/env python3
"""
Simple NotebookLM Question Interface
Uses notebooklm-py API client for direct communication with NotebookLM.
"""

import argparse
import re
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from auth_manager import AuthManager
from notebook_manager import NotebookLibrary
from client import run_async, get_client

# Follow-up reminder to encourage Claude to ask more questions
FOLLOW_UP_REMINDER = (
    "\n\nEXTREMELY IMPORTANT: Is that ALL you need to know? "
    "You can always ask another question! Think about it carefully: "
    "before you reply to the user, review their original request and this answer. "
    "If anything is still unclear or missing, ask me another comprehensive question "
    "that includes all necessary context."
)


def extract_notebook_id(url: str) -> str:
    """Extract notebook ID from a NotebookLM URL.

    Args:
        url: NotebookLM URL like https://notebooklm.google.com/notebook/NOTEBOOK_ID

    Returns:
        The notebook ID string
    """
    match = re.search(r'/notebook/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract notebook ID from URL: {url}")


def ask_notebooklm(question: str, notebook_url: str) -> str:
    """
    Ask a question to NotebookLM via API.

    Args:
        question: Question to ask
        notebook_url: NotebookLM notebook URL

    Returns:
        Answer text from NotebookLM
    """
    auth = AuthManager()

    if not auth.is_authenticated():
        print("Not authenticated. Run: python scripts/run.py auth_manager.py setup")
        return None

    print(f"Asking: {question}")
    print(f"Notebook: {notebook_url}")

    try:
        remote_id = extract_notebook_id(notebook_url)
    except ValueError as e:
        print(f"Error: {e}")
        return None

    async def _ask():
        async with await get_client() as client:
            result = await client.chat.ask(remote_id, question)
            return result.answer

    try:
        print("  Sending question...")
        answer = run_async(_ask())

        if not answer:
            print("  Empty response from NotebookLM")
            return None

        print("  Got answer!")
        return answer + FOLLOW_UP_REMINDER

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description='Ask NotebookLM a question')

    parser.add_argument('--question', required=True, help='Question to ask')
    parser.add_argument('--notebook-url', help='NotebookLM notebook URL')
    parser.add_argument('--notebook-id', help='Notebook ID from library')

    args = parser.parse_args()

    # Resolve notebook URL
    notebook_url = args.notebook_url

    if not notebook_url and args.notebook_id:
        library = NotebookLibrary()
        notebook = library.get_notebook(args.notebook_id)
        if notebook:
            notebook_url = notebook['url']
        else:
            print(f"Notebook '{args.notebook_id}' not found")
            return 1

    if not notebook_url:
        # Check for active notebook first
        library = NotebookLibrary()
        active = library.get_active_notebook()
        if active:
            notebook_url = active['url']
            print(f"Using active notebook: {active['name']}")
        else:
            # Show available notebooks
            notebooks = library.list_notebooks()
            if notebooks:
                print("\nAvailable notebooks:")
                for nb in notebooks:
                    mark = " [ACTIVE]" if nb.get('id') == library.active_notebook_id else ""
                    print(f"  {nb['id']}: {nb['name']}{mark}")
                print("\nSpecify with --notebook-id or set active:")
                print("python scripts/run.py notebook_manager.py activate --id ID")
            else:
                print("No notebooks in library. Add one first:")
                print("python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS")
            return 1

    # Ask the question
    answer = ask_notebooklm(
        question=args.question,
        notebook_url=notebook_url
    )

    if answer:
        print("\n" + "=" * 60)
        print(f"Question: {args.question}")
        print("=" * 60)
        print()
        print(answer)
        print()
        print("=" * 60)
        return 0
    else:
        print("\nFailed to get answer")
        return 1


if __name__ == "__main__":
    sys.exit(main())
