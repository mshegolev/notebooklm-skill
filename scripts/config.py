"""
Configuration for NotebookLM Skill
Centralizes constants and paths
"""

from pathlib import Path

# Paths
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
LIBRARY_FILE = DATA_DIR / "library.json"

# Proxy Configuration
PROXY_SERVER = "socks5://localhost:11111"

# Timeouts
QUERY_TIMEOUT_SECONDS = 120
