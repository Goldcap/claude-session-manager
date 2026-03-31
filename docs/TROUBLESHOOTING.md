# Troubleshooting Guide

Common issues and their solutions for Claude Session Manager.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Hook Not Triggering](#hook-not-triggering)
- [Archiving Issues](#archiving-issues)
- [Summary Problems](#summary-problems)
- [Continue Command Issues](#continue-command-issues)
- [Linear Integration Issues](#linear-integration-issues)
- [Performance Issues](#performance-issues)
- [Debug Mode](#debug-mode)

---

## Installation Issues

### "Command not found" when running scripts

**Symptoms:**
```
bash: /home/user/.claude/hooks/post-response.sh: No such file or directory
```

**Cause:** Scripts not copied to correct location or not executable.

**Fix:**
```bash
# Verify scripts exist
ls -la ~/.claude/hooks/post-response.sh
ls -la ~/.claude/tools/archive-session.py

# Make executable if needed
chmod +x ~/.claude/hooks/post-response.sh
chmod +x ~/.claude/tools/archive-session.py
```

### "Permission denied" errors

**Symptoms:**
```
-bash: ./post-response.sh: Permission denied
```

**Cause:** Scripts not marked as executable.

**Fix:**
```bash
chmod +x ~/.claude/hooks/post-response.sh
chmod +x ~/.claude/tools/archive-session.py
```

### "Python not found" errors

**Symptoms:**
```
python3: command not found
```

**Cause:** Python 3 not installed or not in PATH.

**Fix:**
```bash
# Check Python version
python3 --version

# If missing, install:
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3

# Other Linux
# See https://www.python.org/downloads/
```

---

## Hook Not Triggering

### Archiving never happens automatically

**Check 1: Verify hook is configured**
```bash
cat ~/.claude/settings.local.json | grep -A10 "Stop"
```

**Expected:**
```json
"Stop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "$HOME/.claude/hooks/post-response.sh",
        "statusMessage": "Checking session size...",
        "async": true
      }
    ]
  }
]
```

**If missing:** Add the Stop hook configuration to `~/.claude/settings.local.json`.

**Check 2: Verify hook script exists**
```bash
ls -la ~/.claude/hooks/post-response.sh
```

**Expected:** `-rwxr-xr-x ... post-response.sh` (executable)

**If not executable:**
```bash
chmod +x ~/.claude/hooks/post-response.sh
```

**Check 3: Test hook manually**
```bash
~/.claude/hooks/post-response.sh
```

**Expected:** Either no output (if session < 5MB) or archive success message.

**If errors appear:** Read error message and check:
- Archiver script exists and is executable
- Session directory exists
- Archive directory can be created

### "statusMessage" doesn't appear in Claude Code

**Cause:** This is normal if async mode is enabled. Status messages are brief.

**Verification:**
- Check if archives are being created in `~/docs/sessions/`
- Look for timestamped directories

### Hook runs but nothing happens

**Debug:**
```bash
# Run hook with verbose output
bash -x ~/.claude/hooks/post-response.sh
```

**Common issues:**
- Session file not found (expected before first message)
- Session size below threshold (5MB default)
- Archive directory permissions

---

## Archiving Issues

### Archives not being created

**Check 1: Session size**
```bash
# Find current session
CURRENT=$(ls -t ~/.claude/projects/-home-$USER/*.jsonl 2>/dev/null | head -1)

# Check size in MB
du -m "$CURRENT"
```

**Expected:** If output is less than 5, archiving won't trigger yet.

**Solution:** Wait for session to grow, or manually archive:
```bash
~/.claude/tools/archive-session.py "$CURRENT"
```

**Check 2: Archive directory permissions**
```bash
# Create archive directory if missing
mkdir -p ~/docs/sessions

# Check permissions
ls -ld ~/docs/sessions
```

**Expected:** `drwxr-xr-x` (writable by user)

**Check 3: Archiver script syntax errors**
```bash
# Test archiver syntax
python3 -m py_compile ~/.claude/tools/archive-session.py
```

**If errors:** Fix syntax errors in script or reinstall.

### "Archive failed" messages

**Symptoms:**
```
⚠️  Archive failed for session: /path/to/session.jsonl
    Manual archive: /home/user/.claude/tools/archive-session.py <session-path>
```

**Cause:** Archiver script encountered an error.

**Debug:**
```bash
# Run archiver manually to see detailed error
~/.claude/tools/archive-session.py /path/to/session.jsonl
```

**Common causes:**
- Malformed JSON in session file (corrupted line)
- Disk full (no space for archive)
- Archive directory not writable

### Archives created but session continues

**This is expected behavior.** The session file is copied to the archive, but Claude Code continues using the original file. This is intentional - archiving doesn't interrupt your work.

**To verify archiving worked:**
```bash
# List archives
ls -la ~/docs/sessions/

# Check most recent archive
ls -la ~/docs/sessions/$(ls -t ~/docs/sessions/ | head -1)/
```

**Expected:**
- `chunk-001.jsonl` (copy of session)
- `summary.md` (intelligent summary)
- `metadata.json` (session stats)

---

## Summary Problems

### Summary missing sections

**Symptoms:** `summary.md` exists but missing "What Was Accomplished" or other sections.

**Cause:** Extraction functions didn't find matching patterns.

**Debug:**
```bash
# Read the summary
cat ~/docs/sessions/YYYY-MM-DD-HH-MM-topic/summary.md
```

**Expected sections:**
- What Was Accomplished
- Files Changed
- Linear Tickets
- Key Decisions
- Related Artifacts

**Common reasons for missing sections:**
- **Accomplishments:** No keywords like "successfully", "completed", "created" in messages
- **Files Changed:** No Edit/Write/NotebookEdit tool calls
- **Linear Tickets:** No TEC-xxx or TECH-xxx patterns in messages
- **Key Decisions:** No decision indicators like "decided to", "chose", "strategy:"
- **Artifacts:** No references to docs/brainstorms/, docs/plans/, docs/solutions/

**Solution (if genuine content missing):**

Regenerate summary:
```bash
~/.claude/tools/archive-session.py --regenerate-summary ~/docs/sessions/YYYY-MM-DD-HH-MM-topic/
```

### Summary content looks wrong

**Symptoms:** Summary includes irrelevant content or misses important content.

**Cause:** Keyword-based extraction isn't perfect.

**Customization:**

Edit `~/.claude/tools/archive-session.py` and adjust extraction patterns:

**For accomplishments:**
```python
# Line ~100
accomplishment_keywords = [
    "successfully", "completed", "created", "updated",
    "fixed", "deployed", "tested", "implemented",
    "✅", "finished", "done"
    # Add your keywords here
]
```

**For decisions:**
```python
# Line ~150
decision_keywords = [
    "decided to", "chose", "selected", "went with",
    "approach:", "strategy:", "decision:", "plan:"
    # Add your keywords here
]
```

**After customization:**
```bash
# Regenerate summary with new patterns
~/.claude/tools/archive-session.py --regenerate-summary ~/docs/sessions/YYYY-MM-DD-HH-MM-topic/
```

### No accomplishments extracted

**Check session content:**
```bash
# Search for accomplishment keywords in original session
grep -i "successfully\|completed\|created" ~/docs/sessions/YYYY-MM-DD-HH-MM-topic/chunk-001.jsonl
```

**If no matches:** The session may not have explicit accomplishment statements. This is normal for exploratory or incomplete sessions.

**Workaround:** Manually edit the summary.md file.

---

## Continue Command Issues

### `/continue` not recognized

**Symptoms:**
```
Unknown command: /continue
```

**Cause:** Skill not installed.

**Fix:**
```bash
# Check skill is installed
ls -la ~/.claude/skills/continue/

# Should show:
# skill.json
# instructions.md

# If missing, copy skill
cp -r /path/to/claude-session-manager/skills/continue ~/.claude/skills/
```

### `/continue` shows no context

**Symptoms:**
```
📋 Resuming Work

No recent session context available.
What should we continue working on?
```

**Cause:** No archived sessions and empty current session.

**Expected:** This is normal for first use or fresh sessions.

**To test with data:**
1. Create a session > 5MB (or manually archive a session)
2. Start new Claude Code session
3. Run `/continue`

### `/continue` missing archived summary

**Check archives exist:**
```bash
ls -la ~/docs/sessions/
```

**Expected:** One or more timestamped directories with `summary.md` files.

**If missing:**
- No sessions have been archived yet (size < 5MB)
- Archive directory configured to different location

**Check archive directory configuration:**
```bash
echo $CLAUDE_ARCHIVE_DIR
```

**If set:** `/continue` may be looking in wrong location.

**Fix:** Ensure environment variable matches where archives are stored.

### `/continue` shows "Linear API failed"

**Cause:** Linear integration not configured or API unavailable.

**This is not fatal** - `/continue` will show local context (recent messages + archived summary) without Linear tickets.

**To enable Linear:**

**Option A: Linear MCP (recommended)**
- Configure Linear MCP in Claude Code settings
- `/continue` will automatically use it

**Option B: Direct API**
```bash
# In Claude Code session, store API token in CLTM
# User message: Remember my Linear API token as "linear-api-token": lin_api_xxxxx
```

---

## Linear Integration Issues

### "Linear API token not found"

**Cause:** Token not stored in Claude LTM or Linear MCP not configured.

**Fix (MCP):**
- Add Linear MCP server to Claude Code settings
- Restart Claude Code

**Fix (Direct API):**
```bash
# In Claude Code session
# User message: Remember my Linear API token as "linear-api-token": lin_api_xxxxx
```

**Get Linear API token:** https://linear.app/settings/api

### "GraphQL query failed"

**Cause:** Invalid API token or Linear API unavailable.

**Debug:**
```bash
# Test Linear API manually
curl -X POST https://api.linear.app/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lin_api_xxxxx" \
  -d '{"query":"query { viewer { id name email } }"}'
```

**Expected:** JSON response with viewer data.

**If error:** Check token validity at https://linear.app/settings/api

### Linear tickets not showing in summary

**Cause:** No TEC-xxx or TECH-xxx patterns found in session messages.

**Debug:**
```bash
# Search session for ticket references
grep -E "TEC-[0-9]+|TECH-[0-9]+" ~/docs/sessions/YYYY-MM-DD-HH-MM-topic/chunk-001.jsonl
```

**If no matches:** Session didn't reference Linear tickets. This is normal.

**Customize ticket patterns:**

Edit `~/.claude/tools/archive-session.py`:
```python
# Line ~120
ticket_pattern = r'TEC-\d+|TECH-\d+|PROJ-\d+'  # Add your patterns
```

---

## Performance Issues

### Hook execution is slow

**Symptoms:** Noticeable delay after each Claude Code response.

**Cause:** Hook is running in sync mode instead of async.

**Fix:** Verify async mode in settings:
```bash
cat ~/.claude/settings.local.json | grep -A5 "async"
```

**Expected:** `"async": true`

**If false or missing:**
```json
{
  "type": "command",
  "command": "$HOME/.claude/hooks/post-response.sh",
  "async": true
}
```

### Archiving takes too long

**Symptoms:** Archiving takes > 10 seconds for large sessions.

**Expected:** 1-3 seconds for 5MB session is normal.

**If slower:**
- Check disk I/O (slow disk, network drive)
- Check CPU usage (other processes competing)
- Check session size (> 10MB sessions will be slower)

**Optimization:**

Increase threshold to archive less frequently:
```bash
# Add to ~/.bashrc or ~/.zshrc
export CLAUDE_THRESHOLD_MB=10  # Archive at 10MB instead of 5MB
```

### Summary generation fails on large sessions

**Symptoms:**
```
MemoryError: Unable to allocate memory
```

**Cause:** Session too large to fit in memory.

**Workaround:**

Increase system swap or split session manually:
```bash
# Split large JSONL into chunks
split -l 1000 large-session.jsonl chunk-

# Archive each chunk separately
for chunk in chunk-*; do
  ~/.claude/tools/archive-session.py "$chunk"
done
```

---

## Debug Mode

### Enable verbose logging

**For hook:**
```bash
# Edit post-response.sh, add at top:
set -x  # Enable debug output

# Output will appear in Claude Code logs
```

**For archiver:**
```python
# Edit archive-session.py, add at top of main():
import logging
logging.basicConfig(level=logging.DEBUG)

# Detailed logs will print to stderr
```

**For `/continue` skill:**
```bash
# Skill runs within Claude Code - check Claude Code logs
# Or manually test the workflow from skill instructions
```

### View Claude Code logs

**Location varies by platform:**

**macOS:**
```bash
~/Library/Logs/Claude/
```

**Linux:**
```bash
~/.config/claude/logs/
```

**Windows:**
```
%APPDATA%\Claude\logs\
```

### Manual testing workflow

**Test hook:**
```bash
# Create test session
mkdir -p /tmp/test-sessions
dd if=/dev/zero of=/tmp/test-sessions/test.jsonl bs=1M count=6

# Set environment
export CLAUDE_SESSION_DIR=/tmp/test-sessions
export CLAUDE_ARCHIVE_DIR=/tmp/test-archives
export CLAUDE_THRESHOLD_MB=5

# Run hook
~/.claude/hooks/post-response.sh

# Verify archive created
ls /tmp/test-archives/
```

**Test archiver:**
```bash
# Use real session or create mock
echo '{"type":"user","message":{"content":"Test"},"timestamp":"2026-03-31T10:00:00"}' > /tmp/test.jsonl

# Run archiver
~/.claude/tools/archive-session.py /tmp/test.jsonl

# Check output
ls ~/docs/sessions/
```

**Test `/continue`:**
```bash
# Create mock archive
mkdir -p ~/docs/sessions/2026-03-31-10-00-test
echo "# Mock Summary" > ~/docs/sessions/2026-03-31-10-00-test/summary.md

# In Claude Code session, run: /continue
```

---

## Getting Help

If troubleshooting doesn't resolve your issue:

1. **Check GitHub Issues:**
   https://github.com/yourusername/claude-session-manager/issues

2. **Search for similar problems:**
   Someone may have encountered the same issue.

3. **Open a new issue with:**
   - Description of the problem
   - Steps to reproduce
   - Relevant logs and error messages
   - Your configuration (environment variables, settings.local.json)
   - System info (OS, Python version, Claude Code version)

4. **Provide diagnostics:**
   ```bash
   # Collect diagnostic info
   echo "=== System Info ===" > diagnostic.txt
   uname -a >> diagnostic.txt
   python3 --version >> diagnostic.txt

   echo "=== File Checks ===" >> diagnostic.txt
   ls -la ~/.claude/hooks/post-response.sh >> diagnostic.txt
   ls -la ~/.claude/tools/archive-session.py >> diagnostic.txt
   ls -la ~/.claude/skills/continue/ >> diagnostic.txt

   echo "=== Environment ===" >> diagnostic.txt
   env | grep CLAUDE >> diagnostic.txt

   echo "=== Recent Archives ===" >> diagnostic.txt
   ls -lt ~/docs/sessions/ | head -5 >> diagnostic.txt
   ```

---

## FAQ

See [docs/FAQ.md](FAQ.md) for frequently asked questions.

## Additional Resources

- [README.md](../README.md) - Project overview and features
- [INSTALL.md](../INSTALL.md) - Installation guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
- [Examples](../examples/) - Configuration examples
