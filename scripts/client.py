"""
Async-to-sync bridge for notebooklm-py client.
Provides helper functions to use the async NotebookLMClient in sync code.
Injects proxy configuration into the HTTP client.
"""

import asyncio
import os

from notebooklm import NotebookLMClient
from config import PROXY_SERVER


def _ensure_proxy_env():
    """Set proxy environment variables for httpx (trust_env=True by default)."""
    if PROXY_SERVER:
        os.environ.setdefault("ALL_PROXY", PROXY_SERVER)
        os.environ.setdefault("HTTPS_PROXY", PROXY_SERVER)


def run_async(coro):
    """Run an async coroutine synchronously."""
    _ensure_proxy_env()
    return asyncio.run(coro)


async def get_client(storage_path=None):
    """Create a NotebookLMClient from stored authentication.

    Proxy is injected into the underlying httpx client automatically
    via ALL_PROXY/HTTPS_PROXY env vars (httpx trust_env=True).

    Args:
        storage_path: Optional path to storage_state.json.
                      If None, uses default ~/.notebooklm/storage_state.json.

    Returns:
        NotebookLMClient instance (must be used as async context manager).
    """
    _ensure_proxy_env()
    return await NotebookLMClient.from_storage(path=storage_path)
