# Claude Session Manager

Automatic session archiving and intelligent resumption for Claude Code.

## Problem

Claude Code sessions can grow large (>100MB), causing:
- `/resume` command to freeze or timeout
- Loss of context when starting new sessions
- Difficulty tracking what was accomplished across sessions

## Solution

This system provides:

1. **Automatic Archiving** - Sessions >5MB automatically archived with intelligent summaries
2. **Smart Summaries** - Extracts accomplishments, files changed, tickets, decisions, and artifacts
3. **`/continue` Command** - Resume work with full context from previous sessions

## Features

### 🗂️ Automatic Archiving

- Runs after every assistant response (via Stop hook)
- Archives sessions >5MB automatically
- Creates timestamped directories with meaningful topic slugs
- Preserves full session JSONL for complete audit trail

### 🧠 Intelligent Summaries

Automatically extracts from session:
- ✅ **Accomplishments** - What was completed ("successfully created", "deployed", "fixed")
- 📁 **Files Changed** - All files modified via Edit/Write/NotebookEdit
- 🎫 **Linear Tickets** - Referenced ticket IDs (TEC-xxx, TECH-xxx patterns)
- 🎯 **Key Decisions** - Decision points from user messages
- 📋 **Artifacts** - Links to brainstorms, plans, solutions created

### ⚡ `/continue` Command

Resume work by loading:
- Last 20 messages from current session (recent context)
- Most recent archived summary (what was finished)
- Active Linear tickets (what's pending)

Presents consolidated context with clear "What should we continue working on?" prompt.

## Installation

### Prerequisites

- Claude Code CLI installed
- Python 3.7+ (for archive-session.py)
- Bash shell (for hooks)

### Quick Install

```bash
# 1. Clone repository
cd ~/.claude
git clone https://github.com/yourusername/claude-session-manager.git

# 2. Copy scripts to Claude directories
cp claude-session-manager/hooks/post-response.sh ~/.claude/hooks/
cp claude-session-manager/tools/archive-session.py ~/.claude/tools/
cp -r claude-session-manager/skills/continue ~/.claude/skills/

# 3. Make scripts executable
chmod +x ~/.claude/hooks/post-response.sh
chmod +x ~/.claude/tools/archive-session.py

# 4. Configure Stop hook in settings
# Add to ~/.claude/settings.local.json:
```

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

### Verify Installation

```bash
# Check scripts are executable
ls -la ~/.claude/hooks/post-response.sh
ls -la ~/.claude/tools/archive-session.py

# Check skill is installed
ls -la ~/.claude/skills/continue/

# Test archiver manually (optional)
~/.claude/tools/archive-session.py --help
```

## Usage

### Automatic Archiving

Once configured, archiving happens automatically:

1. Work in Claude Code session as normal
2. After every response, hook checks session size
3. If >5MB, session automatically archived
4. New timestamped directory created in `~/docs/sessions/`
5. Intelligent summary generated
6. Session continues in fresh JSONL file

**Archive structure:**
```
~/docs/sessions/
├── index.md
├── 2026-03-31-15-20-authentication-system/
│   ├── chunk-001.jsonl              # Full session JSONL
│   ├── summary.md                   # Intelligent summary
│   └── metadata.json                # Session metadata
└── 2026-04-01-10-30-deploy-api/
    ├── chunk-001.jsonl
    ├── summary.md
    └── metadata.json
```

### Resume Work with `/continue`

In a new session, type:

```
/continue
```

Or:
```
resume work
```

Or:
```
pick up where we left off
```

**Output:**
```markdown
📋 Resuming Work

## Last Archived Session: 2026-03-31-authentication-system

**Accomplished:**
- Successfully created JWT handler
- Implemented login endpoint for TEC-200
- Deployed to staging

**Files Changed:**
- `/home/user/auth/jwt_handler.py`
- `/home/user/auth/routes.py`

**Linear Tickets:**
- TEC-200

**Key Decisions:**
- Decided to use JWT tokens instead of session-based auth

**Related Artifacts:**
- [Plan](docs/plans/2026-03-31-auth-plan.md)

## Recent Activity (Last 20 Messages)

**Recent Tools Used:**
- Edit (3 times)
- Bash (2 times)

**Files Modified Recently:**
- `/home/user/auth/routes.py`

## Active Linear Tickets

- **TEC-200**: JWT Authentication - *In Progress*
- **TEC-201**: User Registration - *Todo*

---

What should we continue working on?
```

### Manual Archiving

Archive a session manually:

```bash
~/.claude/tools/archive-session.py /path/to/session.jsonl
```

Regenerate summary for existing archive:

```bash
~/.claude/tools/archive-session.py --regenerate-summary ~/docs/sessions/2026-03-31-15-20-topic/
```

## Configuration

### Environment Variables

Customize behavior with environment variables:

```bash
# Archive directory (default: ~/docs/sessions)
export CLAUDE_ARCHIVE_DIR="$HOME/my-custom-archive-dir"

# Session directory (default: ~/.claude/projects/-home-$USER)
export CLAUDE_SESSION_DIR="$HOME/.claude/projects/custom-session-dir"

# Size threshold in MB (default: 5)
export CLAUDE_THRESHOLD_MB=10

# Archiver script path (default: ~/.claude/tools/archive-session.py)
export CLAUDE_ARCHIVER="$HOME/.claude/tools/archive-session.py"
```

Add to `~/.bashrc` or `~/.zshrc` to persist.

### Hook Configuration

**Async mode (recommended):**
```json
{
  "type": "command",
  "command": "$HOME/.claude/hooks/post-response.sh",
  "async": true
}
```

**Sync mode (blocks until complete):**
```json
{
  "type": "command",
  "command": "$HOME/.claude/hooks/post-response.sh",
  "async": false
}
```

### Linear Integration

**Option A: Linear MCP (recommended)**

If you have Linear MCP configured, `/continue` will automatically query active tickets.

**Option B: Direct API**

Store Linear API token in Claude LTM:

```
# In Claude Code session
Remember Linear API token as "linear-api-token"
```

The `/continue` command will recall and use it.

## Architecture

### System Flow

```
Session Work → Stop Hook → Size Check → >5MB? → Archive → Summary Generation
                                           │
                                           └─→ Continue (if <5MB)

Next Session → /continue → Load Context → Present → User Chooses Next Task
```

### Components

**Hooks:**
- `post-response.sh` - Triggered by Stop hook after every response

**Tools:**
- `archive-session.py` - JSONL parser, intelligent extractor, archiver

**Skills:**
- `continue/` - Resume work command with context loading

### Data Flow

1. **Session accumulates** messages in JSONL format
2. **Hook checks** size after every response
3. **Archiver moves** JSONL to archive directory
4. **Extractor parses** messages for intelligence
5. **Summary generated** with accomplishments, files, tickets, decisions
6. **Index updated** with new archive entry
7. **Continue loads** context from archive + current session + Linear

## Examples

### Example Summary

```markdown
# Session Summary

**Topic:** Create authentication system for API
**Messages:** 45
**Duration:** 2026-03-31T10:00:00 to 2026-03-31T14:30:00

## What Was Accomplished

- Successfully created JWT authentication handler
- Implemented login and registration endpoints
- Deployed to staging environment for TEC-200

## Files Changed

- `/home/user/auth/jwt_handler.py`
- `/home/user/auth/routes.py`
- `/home/user/tests/test_auth.py`

## Linear Tickets

- TEC-200

## Key Decisions

- Decided to use JWT tokens with 15-minute expiration
- Strategy: Use short-lived access tokens and long-lived refresh tokens

## Related Artifacts

**Plans:**
- [docs/plans/2026-03-31-auth-plan.md](docs/plans/2026-03-31-auth-plan.md)

## References

- Full session: `chunk-001.jsonl`
- Metadata: `metadata.json`
```

### Example Settings

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/session-startup.sh"
          }
        ]
      }
    ],
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

## Troubleshooting

### Archive Not Happening

**Check hook is configured:**
```bash
cat ~/.claude/settings.local.json | grep -A5 "Stop"
```

**Check hook is executable:**
```bash
ls -la ~/.claude/hooks/post-response.sh
```

**Check archiver is executable:**
```bash
ls -la ~/.claude/tools/archive-session.py
```

**Test archiver manually:**
```bash
~/.claude/tools/archive-session.py ~/.claude/projects/-home-$USER/*.jsonl
```

### Summary Missing Sections

**Regenerate summary:**
```bash
~/.claude/tools/archive-session.py --regenerate-summary ~/docs/sessions/YYYY-MM-DD-HH-MM-topic/
```

**Check extraction patterns:**
- Accomplishments: Keywords like "successfully", "completed", "deployed"
- Files: Edit/Write/NotebookEdit tool calls
- Tickets: TEC-\d+, TECH-\d+ patterns
- Decisions: "decided to", "chose", "selected", "strategy:"

### `/continue` Not Working

**Check skill is installed:**
```bash
ls -la ~/.claude/skills/continue/
```

**Verify trigger phrases:**
- `/continue`
- `resume work`
- `pick up where we left off`

**Check recent session exists:**
```bash
ls -t ~/.claude/projects/-home-$USER/*.jsonl | head -1
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development

**Test archiver:**
```bash
# Create test session
echo '{"type":"user","message":{"content":"Test"},"timestamp":"2026-03-31T10:00:00"}' > /tmp/test.jsonl

# Run archiver
./tools/archive-session.py /tmp/test.jsonl

# Verify archive created
ls ~/docs/sessions/
```

**Test hook:**
```bash
# Set environment
export CLAUDE_SESSION_DIR=/tmp/test-sessions
export CLAUDE_ARCHIVE_DIR=/tmp/test-archives
export CLAUDE_THRESHOLD_MB=1

# Create test session
mkdir -p /tmp/test-sessions
dd if=/dev/zero of=/tmp/test-sessions/test.jsonl bs=1M count=2

# Run hook
./hooks/post-response.sh

# Verify archive
ls /tmp/test-archives/
```

## License

MIT License - see LICENSE file for details.

## Credits

Created by [@amadsen](https://github.com/amadsen) for the Claude Code community.

Built with:
- Python 3 for intelligent JSONL parsing
- Bash for lightweight hooks
- Claude Code's hook system

## Support

- GitHub Issues: https://github.com/yourusername/claude-session-manager/issues
- Documentation: https://github.com/yourusername/claude-session-manager/docs

## Changelog

### v1.0.0 (2026-03-31)

**Initial Release:**
- ✅ Automatic session archiving at 5MB threshold
- ✅ Intelligent summary generation with 6 extraction functions
- ✅ `/continue` command for work resumption
- ✅ Linear ticket integration
- ✅ Complete documentation and examples
