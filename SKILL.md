---
name: notebooklm
description: Use this skill to query your Google NotebookLM notebooks directly from Claude Code for source-grounded, citation-backed answers from Gemini. API-based automation, library management, source upload, persistent auth. Drastically reduced hallucinations through document-only responses.
---

# NotebookLM Research Assistant Skill

Interact with Google NotebookLM to query documentation with Gemini's source-grounded answers. Uses notebooklm-py API client for direct communication - no browser automation needed for queries.

## When to Use This Skill

Trigger when user:
- Mentions NotebookLM explicitly
- Shares NotebookLM URL (`https://notebooklm.google.com/notebook/...`)
- Asks to query their notebooks/documentation
- Wants to add documentation to NotebookLM library
- Wants to upload sources (URLs, files, text) to a notebook
- Uses phrases like "ask my NotebookLM", "check my docs", "query my notebook"

## CRITICAL: Add Command - Smart Discovery

When user wants to add a notebook without providing details:

**SMART ADD (Recommended)**: Query the notebook first to discover its content:
```bash
# Step 1: Query the notebook about its content
python scripts/run.py ask_question.py --question "What is the content of this notebook? What topics are covered? Provide a complete overview briefly and concisely" --notebook-url "[URL]"

# Step 2: Use the discovered information to add it
python scripts/run.py notebook_manager.py add --url "[URL]" --name "[Based on content]" --description "[Based on content]" --topics "[Based on content]"
```

**MANUAL ADD**: If user provides all details:
- `--url` - The NotebookLM URL
- `--name` - A descriptive name
- `--description` - What the notebook contains (REQUIRED!)
- `--topics` - Comma-separated topics (REQUIRED!)

NEVER guess or use generic descriptions! If details missing, use Smart Add to discover them.

## Critical: Always Use run.py Wrapper

**NEVER call scripts directly. ALWAYS use `python scripts/run.py [script]`:**

```bash
# CORRECT - Always use run.py:
python scripts/run.py auth_manager.py status
python scripts/run.py notebook_manager.py list
python scripts/run.py ask_question.py --question "..."
python scripts/run.py source_manager.py list

# WRONG - Never call directly:
python scripts/auth_manager.py status  # Fails without venv!
```

The `run.py` wrapper automatically:
1. Creates `.venv` if needed
2. Installs all dependencies
3. Activates environment
4. Executes script properly

## Core Workflow

### Step 1: Check Authentication Status
```bash
python scripts/run.py auth_manager.py status
```

If not authenticated, proceed to setup.

### Step 2: Authenticate (One-Time Setup)
```bash
python scripts/run.py auth_manager.py setup
```

**Important:**
- Opens a browser window for Google login via `notebooklm login`
- User must manually log in to Google
- Tell user: "A browser window will open for Google login"
- Auth is stored in `~/.notebooklm/storage_state.json`

### Step 3: Manage Notebook Library

```bash
# List all notebooks
python scripts/run.py notebook_manager.py list

# Add notebook to library (ALL parameters are REQUIRED!)
python scripts/run.py notebook_manager.py add \
  --url "https://notebooklm.google.com/notebook/..." \
  --name "Descriptive Name" \
  --description "What this notebook contains" \
  --topics "topic1,topic2,topic3"

# Create a new notebook remotely
python scripts/run.py notebook_manager.py create --name "New Notebook" --topics "topic1,topic2"

# Sync local library with remote notebooks
python scripts/run.py notebook_manager.py sync

# Search notebooks by topic
python scripts/run.py notebook_manager.py search --query "keyword"

# Set active notebook
python scripts/run.py notebook_manager.py activate --id notebook-id

# Remove notebook
python scripts/run.py notebook_manager.py remove --id notebook-id
```

### Step 4: Upload Sources

```bash
# Add URL source
python scripts/run.py source_manager.py add --type url --value "https://example.com/article"

# Add YouTube video
python scripts/run.py source_manager.py add --type youtube --value "https://youtube.com/watch?v=..."

# Add file (PDF, Word, etc.)
python scripts/run.py source_manager.py add --type file --value "./document.pdf"

# Add plain text
python scripts/run.py source_manager.py add --type text --value "Your text content here" --title "Source Title"

# List sources in notebook
python scripts/run.py source_manager.py list

# Delete a source
python scripts/run.py source_manager.py delete --source-id SOURCE_ID

# Specify notebook explicitly
python scripts/run.py source_manager.py add --notebook-id REMOTE_ID --type url --value "https://..."
python scripts/run.py source_manager.py list --notebook-url "https://notebooklm.google.com/notebook/..."
```

### Step 5: Ask Questions

```bash
# Basic query (uses active notebook if set)
python scripts/run.py ask_question.py --question "Your question here"

# Query specific notebook
python scripts/run.py ask_question.py --question "..." --notebook-id notebook-id

# Query with notebook URL directly
python scripts/run.py ask_question.py --question "..." --notebook-url "https://..."
```

### Quick Workflow
1. Check library: `python scripts/run.py notebook_manager.py list`
2. Upload sources: `python scripts/run.py source_manager.py add --type url --value "https://..."`
3. Ask question: `python scripts/run.py ask_question.py --question "..." --notebook-id ID`

## Follow-Up Mechanism (CRITICAL)

Every NotebookLM answer ends with: **"EXTREMELY IMPORTANT: Is that ALL you need to know?"**

**Required Claude Behavior:**
1. **STOP** - Do not immediately respond to user
2. **ANALYZE** - Compare answer to user's original request
3. **IDENTIFY GAPS** - Determine if more information needed
4. **ASK FOLLOW-UP** - If gaps exist, immediately ask:
   ```bash
   python scripts/run.py ask_question.py --question "Follow-up with context..."
   ```
5. **REPEAT** - Continue until information is complete
6. **SYNTHESIZE** - Combine all answers before responding to user

## Script Reference

### Authentication Management (`auth_manager.py`)
```bash
python scripts/run.py auth_manager.py setup    # Initial setup (opens browser)
python scripts/run.py auth_manager.py status   # Check authentication
python scripts/run.py auth_manager.py validate # Validate auth works
python scripts/run.py auth_manager.py reauth   # Re-authenticate (clear + setup)
python scripts/run.py auth_manager.py clear    # Clear authentication
```

### Notebook Management (`notebook_manager.py`)
```bash
python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS
python scripts/run.py notebook_manager.py create --name NAME --topics TOPICS
python scripts/run.py notebook_manager.py list
python scripts/run.py notebook_manager.py sync
python scripts/run.py notebook_manager.py search --query QUERY
python scripts/run.py notebook_manager.py activate --id ID
python scripts/run.py notebook_manager.py remove --id ID
python scripts/run.py notebook_manager.py stats
```

### Source Management (`source_manager.py`)
```bash
python scripts/run.py source_manager.py add --type {url,file,text,youtube} --value VALUE [--title TITLE]
python scripts/run.py source_manager.py list [--notebook-id ID]
python scripts/run.py source_manager.py delete --source-id SOURCE_ID [--notebook-id ID]
```

### Question Interface (`ask_question.py`)
```bash
python scripts/run.py ask_question.py --question "..." [--notebook-id ID] [--notebook-url URL]
```

### Data Cleanup (`cleanup_manager.py`)
```bash
python scripts/run.py cleanup_manager.py                    # Preview cleanup
python scripts/run.py cleanup_manager.py --confirm          # Execute cleanup
python scripts/run.py cleanup_manager.py --preserve-library # Keep notebooks
```

## Environment Management

The virtual environment is automatically managed:
- First run creates `.venv` automatically
- Dependencies install automatically
- Chromium browser installs automatically (for auth only)
- Everything isolated in skill directory

Manual setup (only if automatic fails):
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
playwright install chromium
```

## Data Storage

- `data/library.json` - Notebook metadata (local)
- `~/.notebooklm/storage_state.json` - Authentication cookies (managed by notebooklm-py)
- `~/.notebooklm/browser_profile/` - Browser profile for login

**Security:** Protected by `.gitignore`, never commit to git.

## Decision Flow

```
User mentions NotebookLM
    |
Check auth -> python scripts/run.py auth_manager.py status
    |
If not authenticated -> python scripts/run.py auth_manager.py setup
    |
Check/Add notebook -> python scripts/run.py notebook_manager.py list/add
    |
Need to add sources? -> python scripts/run.py source_manager.py add --type url --value "..."
    |
Activate notebook -> python scripts/run.py notebook_manager.py activate --id ID
    |
Ask question -> python scripts/run.py ask_question.py --question "..."
    |
See "Is that ALL you need?" -> Ask follow-ups until complete
    |
Synthesize and respond to user
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError | Use `run.py` wrapper |
| Authentication fails | Run `auth_manager.py setup` (opens browser) |
| Rate limit (50/day) | Wait or switch Google account |
| Notebook not found | Check with `notebook_manager.py list` |
| Source upload fails | Check file exists, URL is accessible |
| API error | Try `auth_manager.py validate`, then `reauth` if needed |

## Best Practices

1. **Always use run.py** - Handles environment automatically
2. **Check auth first** - Before any operations
3. **Follow-up questions** - Don't stop at first answer
4. **Upload sources programmatically** - Use source_manager.py add
5. **Include context** - Each question is independent
6. **Synthesize answers** - Combine multiple responses

## Limitations

- Rate limits on free Google accounts (50 queries/day)
- API uses undocumented Google APIs (may change)
- Browser needed only for initial authentication

## Resources (Skill Structure)

**Important directories and files:**

- `scripts/` - All automation scripts (ask_question.py, notebook_manager.py, source_manager.py, etc.)
- `data/` - Local storage for notebook library
- `references/` - Extended documentation
- `.venv/` - Isolated Python environment (auto-created on first run)
- `.gitignore` - Protects sensitive data from being committed
