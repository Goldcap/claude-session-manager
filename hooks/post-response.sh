#!/bin/bash
# Post-response hook to check session file size and archive if needed
# Triggered after every assistant response by Claude Code
#
# Configuration can be overridden with environment variables:
# - CLAUDE_SESSION_DIR: Directory containing session JSONL files
# - CLAUDE_ARCHIVE_DIR: Directory to store archived sessions
# - CLAUDE_THRESHOLD_MB: Size threshold in MB for archiving (default: 5)
# - CLAUDE_ARCHIVER: Path to archive-session.py script

set -e  # Exit on error

# Configuration - can be overridden with environment variables
CLAUDE_HOME="${CLAUDE_HOME:-$HOME}"
SESSION_DIR="${CLAUDE_SESSION_DIR:-$CLAUDE_HOME/.claude/projects/-home-$(whoami)}"
ARCHIVE_DIR="${CLAUDE_ARCHIVE_DIR:-$CLAUDE_HOME/docs/sessions}"
THRESHOLD_MB="${CLAUDE_THRESHOLD_MB:-5}"
ARCHIVER_SCRIPT="${CLAUDE_ARCHIVER:-$CLAUDE_HOME/.claude/tools/archive-session.py}"

# Ensure directories exist
mkdir -p "$SESSION_DIR" "$ARCHIVE_DIR"

# Find current session file (most recently modified JSONL)
CURRENT_SESSION=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)

# If no session file found, exit silently
if [ -z "$CURRENT_SESSION" ]; then
    exit 0
fi

# Check session file size in MB
SESSION_SIZE=$(du -m "$CURRENT_SESSION" 2>/dev/null | cut -f1)

# If size check failed, exit silently
if [ -z "$SESSION_SIZE" ]; then
    exit 0
fi

# Archive if session exceeds threshold
if [ "$SESSION_SIZE" -gt "$THRESHOLD_MB" ]; then
    # Only archive if archiver script exists
    if [ -x "$ARCHIVER_SCRIPT" ]; then
        # Run archiver (errors will be logged by the script itself)
        "$ARCHIVER_SCRIPT" "$CURRENT_SESSION" 2>&1 || {
            echo "⚠️  Archive failed for session: $CURRENT_SESSION" >&2
            echo "    Manual archive: $ARCHIVER_SCRIPT <session-path>" >&2
            # Don't fail the hook - session should continue
            exit 0
        }
    else
        echo "⚠️  Archiver script not found or not executable: $ARCHIVER_SCRIPT" >&2
        exit 0
    fi
fi

exit 0
