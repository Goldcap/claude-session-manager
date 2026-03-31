# Installation Guide

Step-by-step guide to install Claude Session Manager.

## Quick Install (5 minutes)

```bash
# 1. Navigate to Claude directory
cd ~/.claude

# 2. Clone repository
git clone https://github.com/yourusername/claude-session-manager.git

# 3. Run installation script
./claude-session-manager/install.sh
```

The install script will:
- Copy hooks to `~/.claude/hooks/`
- Copy tools to `~/.claude/tools/`
- Copy skills to `~/.claude/skills/`
- Make scripts executable
- Guide you through hook configuration

## Manual Installation

### Step 1: Clone Repository

```bash
cd ~/.claude
git clone https://github.com/yourusername/claude-session-manager.git
```

### Step 2: Copy Files

```bash
# Copy hook
cp claude-session-manager/hooks/post-response.sh ~/.claude/hooks/

# Copy archiver tool
cp claude-session-manager/tools/archive-session.py ~/.claude/tools/

# Copy continue skill
cp -r claude-session-manager/skills/continue ~/.claude/skills/
```

### Step 3: Set Permissions

```bash
chmod +x ~/.claude/hooks/post-response.sh
chmod +x ~/.claude/tools/archive-session.py
```

### Step 4: Configure Hook

Edit `~/.claude/settings.local.json` and add the Stop hook:

**If settings.local.json doesn't exist:**

```bash
cat > ~/.claude/settings.local.json <<'EOF'
{
  "hooks": {
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
  }
}
EOF
```

**If settings.local.json exists:**

Add the Stop hook to your existing hooks section:

```json
{
  "hooks": {
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
  }
}
```

### Step 5: Verify Installation

```bash
# Check hook exists and is executable
ls -la ~/.claude/hooks/post-response.sh

# Should show: -rwxr-xr-x ... post-response.sh

# Check archiver exists and is executable
ls -la ~/.claude/tools/archive-session.py

# Should show: -rwxr-xr-x ... archive-session.py

# Check skill installed
ls -la ~/.claude/skills/continue/

# Should show: skill.json and instructions.md

# Test archiver
~/.claude/tools/archive-session.py --help

# Should show usage information
```

## Configuration (Optional)

### Customize Archive Directory

Default: `~/docs/sessions`

To change:

```bash
# Add to ~/.bashrc or ~/.zshrc
export CLAUDE_ARCHIVE_DIR="$HOME/my-archives"
```

### Customize Threshold

Default: 5MB

To change:

```bash
# Add to ~/.bashrc or ~/.zshrc
export CLAUDE_THRESHOLD_MB=10  # Archive at 10MB instead
```

### Linear Integration

**Option A: Linear MCP (Recommended)**

If you have Linear MCP configured in Claude Code, the `/continue` command will automatically use it. No additional configuration needed.

**Option B: Direct API**

Store your Linear API token in Claude LTM:

1. Get your Linear API token from https://linear.app/settings/api
2. In a Claude Code session:
   ```
   Remember my Linear API token as "linear-api-token": lin_api_xxxxx
   ```

The `/continue` command will recall and use it.

## Verification

### Test Manual Archive

```bash
# Find current session
CURRENT=$(ls -t ~/.claude/projects/-home-$USER/*.jsonl 2>/dev/null | head -1)

# Archive it
~/.claude/tools/archive-session.py "$CURRENT"

# Check archive created
ls ~/docs/sessions/
```

Expected output:
```
✅ Archived session to /home/user/docs/sessions/2026-03-31-15-20-topic-slug
```

### Test `/continue` Command

In a new Claude Code session, type:

```
/continue
```

Expected output:
```
📋 Resuming Work

## Last Archived Session: ...
[Context loads here]

What should we continue working on?
```

### Test Automatic Archiving

The automatic archiving will trigger after your next response if the session exceeds 5MB. You'll see:

```
Checking session size...
✅ Archived session to ~/docs/sessions/YYYY-MM-DD-HH-MM-topic
```

## Troubleshooting

### "Command not found" error

**Cause:** Scripts not executable or not in correct location

**Fix:**
```bash
chmod +x ~/.claude/hooks/post-response.sh
chmod +x ~/.claude/tools/archive-session.py
```

### Hook not triggering

**Cause:** Stop hook not configured correctly

**Fix:** Verify `~/.claude/settings.local.json`:
```bash
cat ~/.claude/settings.local.json | grep -A10 "Stop"
```

Should show the Stop hook configuration.

### `/continue` command not recognized

**Cause:** Skill not installed

**Fix:**
```bash
ls ~/.claude/skills/continue/
```

Should show `skill.json` and `instructions.md`.

If missing:
```bash
cp -r claude-session-manager/skills/continue ~/.claude/skills/
```

### Python errors

**Cause:** Python 3 not available

**Check Python version:**
```bash
python3 --version
```

Should show Python 3.7 or higher.

**Fix:** Install Python 3:
- macOS: `brew install python3`
- Ubuntu/Debian: `sudo apt install python3`
- Other: See https://www.python.org/downloads/

## Uninstallation

To remove Claude Session Manager:

```bash
# Remove hook
rm ~/.claude/hooks/post-response.sh

# Remove archiver
rm ~/.claude/tools/archive-session.py

# Remove skill
rm -rf ~/.claude/skills/continue

# Remove hook configuration from settings.local.json
# Edit ~/.claude/settings.local.json and remove the "Stop" section

# Keep or remove archives (your choice)
# rm -rf ~/docs/sessions/  # WARNING: This deletes all archived sessions
```

## Next Steps

After installation:

1. ✅ Continue using Claude Code normally
2. ✅ Sessions will auto-archive at 5MB
3. ✅ Use `/continue` to resume work in new sessions
4. ✅ Read [README.md](README.md) for usage details
5. ✅ See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how it works

## Support

Having issues? Check:
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [FAQ](docs/FAQ.md)
- [GitHub Issues](https://github.com/yourusername/claude-session-manager/issues)
