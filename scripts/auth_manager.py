#!/usr/bin/env python3
"""
Authentication Manager for NotebookLM
Handles authentication via notebooklm-py library
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, PROXY_SERVER
from client import run_async, get_client


class AuthManager:
    """
    Manages authentication for NotebookLM via notebooklm-py.

    Authentication is handled by the notebooklm-py library which stores
    credentials in ~/.notebooklm/storage_state.json.
    """

    def __init__(self):
        """Initialize the authentication manager"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def is_authenticated(self) -> bool:
        """Check if valid authentication exists"""
        from notebooklm.paths import get_storage_path
        storage_path = get_storage_path()
        if not storage_path.exists():
            return False

        # Check if state file is not too old (7 days)
        age_days = (time.time() - storage_path.stat().st_mtime) / 86400
        if age_days > 7:
            print(f"Warning: Auth state is {age_days:.1f} days old, may need re-authentication")

        return True

    def get_auth_info(self) -> dict:
        """Get authentication information"""
        from notebooklm.paths import get_storage_path
        storage_path = get_storage_path()

        info = {
            'authenticated': self.is_authenticated(),
            'storage_path': str(storage_path),
            'storage_exists': storage_path.exists()
        }

        if storage_path.exists():
            age_hours = (time.time() - storage_path.stat().st_mtime) / 3600
            info['state_age_hours'] = age_hours

        return info

    def setup_auth(self) -> bool:
        """
        Perform interactive authentication setup.

        Opens a browser window (with proxy) for Google login,
        then saves the storage state for notebooklm-py.

        Returns:
            True if authentication successful
        """
        print("Starting authentication setup...")
        print("A browser window will open for Google login.")
        if PROXY_SERVER:
            print(f"Using proxy: {PROXY_SERVER}")

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Playwright not installed. Run:")
            print("  pip install 'notebooklm-py[browser]'")
            print("  playwright install chromium")
            return False

        from notebooklm.paths import get_storage_path, get_browser_profile_dir

        storage_path = get_storage_path()
        browser_profile = get_browser_profile_dir()
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        browser_profile.mkdir(parents=True, exist_ok=True)

        import re

        try:
            with sync_playwright() as p:
                launch_args = {
                    "user_data_dir": str(browser_profile),
                    "channel": "chrome",
                    "headless": False,
                    "no_viewport": True,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--no-first-run",
                        "--no-default-browser-check",
                    ],
                    "ignore_default_args": ["--enable-automation"],
                }
                if PROXY_SERVER:
                    launch_args["proxy"] = {"server": PROXY_SERVER}

                context = p.chromium.launch_persistent_context(**launch_args)

                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")

                # Check if already authenticated
                if re.match(r"^https://notebooklm\.google\.com/", page.url) and "accounts.google.com" not in page.url:
                    print("Already authenticated!")
                else:
                    print("\nWaiting for Google login in browser window...")
                    print("Complete login and wait for NotebookLM homepage to load.")
                    print("(Timeout: 10 minutes)")
                    # Wait for redirect to NotebookLM (up to 10 minutes)
                    # Use domcontentloaded - Google SPA may never fire 'load'
                    page.wait_for_url(
                        re.compile(r"^https://notebooklm\.google\.com/"),
                        timeout=600000,
                        wait_until="domcontentloaded"
                    )
                    print("Login detected!")

                # Save storage state
                context.storage_state(path=str(storage_path))
                context.close()

            print(f"Authentication saved to: {storage_path}")
            return True

        except Exception as e:
            print(f"Error during auth setup: {e}")
            return False

    def validate_auth(self) -> bool:
        """
        Validate that stored authentication works by listing notebooks.

        Returns:
            True if authentication is valid
        """
        if not self.is_authenticated():
            return False

        print("Validating authentication...")

        async def _validate():
            async with await get_client() as client:
                await client.notebooks.list()
                return True

        try:
            run_async(_validate())
            print("Authentication is valid")
            return True
        except Exception as e:
            print(f"Validation failed: {e}")
            return False

    def clear_auth(self) -> bool:
        """
        Clear all authentication data

        Returns:
            True if cleared successfully
        """
        print("Clearing authentication data...")
        from notebooklm.paths import get_storage_path, get_browser_profile_dir
        import shutil

        try:
            storage_path = get_storage_path()
            if storage_path.exists():
                storage_path.unlink()
                print("Removed storage state")

            browser_profile = get_browser_profile_dir()
            if browser_profile.exists():
                shutil.rmtree(browser_profile)
                print("Cleared browser profile")

            return True
        except Exception as e:
            print(f"Error clearing auth: {e}")
            return False

    def re_auth(self) -> bool:
        """
        Perform re-authentication (clear and setup)

        Returns:
            True if successful
        """
        print("Starting re-authentication...")
        self.clear_auth()
        return self.setup_auth()


def main():
    """Command-line interface for authentication management"""
    parser = argparse.ArgumentParser(description='Manage NotebookLM authentication')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Setup command
    subparsers.add_parser('setup', help='Setup authentication (opens browser)')

    # Status command
    subparsers.add_parser('status', help='Check authentication status')

    # Validate command
    subparsers.add_parser('validate', help='Validate authentication')

    # Clear command
    subparsers.add_parser('clear', help='Clear authentication')

    # Re-auth command
    subparsers.add_parser('reauth', help='Re-authenticate (clear + setup)')

    args = parser.parse_args()

    # Initialize manager
    auth = AuthManager()

    # Execute command
    if args.command == 'setup':
        if auth.setup_auth():
            print("\nAuthentication setup complete!")
            print("You can now use ask_question.py to query NotebookLM")
        else:
            print("\nAuthentication setup failed")
            exit(1)

    elif args.command == 'status':
        info = auth.get_auth_info()
        print("\nAuthentication Status:")
        print(f"  Authenticated: {'Yes' if info['authenticated'] else 'No'}")
        if info.get('state_age_hours'):
            print(f"  State age: {info['state_age_hours']:.1f} hours")
        print(f"  Storage: {info['storage_path']}")

    elif args.command == 'validate':
        if auth.validate_auth():
            print("Authentication is valid and working")
        else:
            print("Authentication is invalid or expired")
            print("Run: auth_manager.py setup")

    elif args.command == 'clear':
        if auth.clear_auth():
            print("Authentication cleared")

    elif args.command == 'reauth':
        if auth.re_auth():
            print("\nRe-authentication complete!")
        else:
            print("\nRe-authentication failed")
            exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
