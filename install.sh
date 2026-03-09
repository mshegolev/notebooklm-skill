#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
VENDOR_DIR="$SCRIPT_DIR/vendor/notebooklm-py"
UPSTREAM_REPO="https://github.com/teng-lin/notebooklm-py.git"
CREDS_DIR="$HOME/.notebooklm"
CREDS_FILE="$CREDS_DIR/storage_state.json"

UPGRADE=false
if [ "$1" = "--upgrade" ] || [ "$1" = "-u" ]; then
    UPGRADE=true
fi

echo "=== NotebookLM Skill - Environment Setup ==="

# 1. Check existing credentials
if [ -f "$CREDS_FILE" ]; then
    echo "Credentials found: $CREDS_FILE (will be preserved)"
else
    echo "No credentials found. Run 'python scripts/run.py auth_manager.py setup' after install."
fi

# 2. Create venv if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# 3. Activate venv
source "$VENV_DIR/bin/activate"

# 4. Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# 5. Install/upgrade dependencies
if [ "$UPGRADE" = true ]; then
    echo "Pulling latest notebooklm-py from upstream..."
    TEMP_DIR=$(mktemp -d)
    git clone --depth 1 "$UPSTREAM_REPO" "$TEMP_DIR" 2>&1
    rm -rf "$VENDOR_DIR/src" "$VENDOR_DIR/pyproject.toml"
    cp -r "$TEMP_DIR/src" "$TEMP_DIR/pyproject.toml" "$TEMP_DIR/LICENSE" "$TEMP_DIR/CHANGELOG.md" "$VENDOR_DIR/"
    rm -rf "$TEMP_DIR"
    echo "Vendor updated. Reinstalling..."
fi

if [ -f "$REQUIREMENTS" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r "$REQUIREMENTS"
else
    echo "WARNING: requirements.txt not found at $REQUIREMENTS"
    exit 1
fi

# 6. Install Chromium for Playwright
echo "Installing Chromium for Playwright..."
python -m playwright install chromium || {
    echo "WARNING: Failed to install Chromium."
    echo "  You may need to run manually: playwright install chromium"
}

# 7. Verify credentials preserved
if [ -f "$CREDS_FILE" ]; then
    echo "Credentials OK: $CREDS_FILE"
fi

# 8. Status
echo ""
echo "=== Setup Complete ==="
echo "  Virtual env: $VENV_DIR"
echo "  Python:      $(python --version)"
echo "  notebooklm:  $(pip show notebooklm-py 2>/dev/null | grep Version || echo 'not installed')"
echo "  Credentials: $([ -f "$CREDS_FILE" ] && echo "present" || echo "missing - run auth setup")"
echo "  Activate:    source $VENV_DIR/bin/activate"
echo ""
echo "Usage:"
echo "  ./install.sh            Install environment"
echo "  ./install.sh --upgrade  Upgrade notebooklm-py from GitHub"
