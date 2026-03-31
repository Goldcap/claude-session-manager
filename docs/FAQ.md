# Frequently Asked Questions

Common questions about Claude Session Manager.

## General

### What is Claude Session Manager?

Claude Session Manager is a session continuity system for Claude Code that:
- Automatically archives large sessions (>5MB) to prevent context loss
- Generates intelligent summaries with insights from session history
- Enables seamless work resumption via the `/continue` command

### Why do I need this?

Claude Code sessions can grow very large (100MB+), causing the `/resume` command to freeze or timeout. This system prevents that by automatically archiving sessions at a manageable size and extracting actionable context for resumption.

### Is this official Claude Code software?

No, this is a community project created by [@amadsen](https://github.com/amadsen). It uses Claude Code's official hook system but is not developed or supported by Anthropic.

### What are the system requirements?

- Claude Code CLI installed
- Python 3.7 or higher
- Bash shell (macOS, Linux, WSL on Windows)
- ~10MB disk space for the tool
- Additional space for archives (depends on session sizes)

---

## Installation & Setup

### How do I install it?

**Quick install:**
```bash
cd ~/.claude
git clone https://github.com/yourusername/claude-session-manager.git
./claude-session-manager/install.sh
```

See [INSTALL.md](../INSTALL.md) for detailed instructions.

### Can I customize where archives are stored?

Yes! Set the `CLAUDE_ARCHIVE_DIR` environment variable:

```bash
# Add to ~/.bashrc or ~/.zshrc
export CLAUDE_ARCHIVE_DIR="$HOME/my-custom-archive-dir"
```

Default: `~/docs/sessions`

### Can I change the 5MB threshold?

Yes! Set the `CLAUDE_THRESHOLD_MB` environment variable:

```bash
# Archive at 10MB instead of 5MB
export CLAUDE_THRESHOLD_MB=10
```

### Do I need to restart Claude Code after installation?

No, Claude Code automatically detects new hooks and skills. Just start using it.

---

## Usage

### How do I know when archiving happens?

You'll see a brief status message: "Checking session size..." after each response. If archiving occurs, you'll see:
```
✅ Archived session to ~/docs/sessions/YYYY-MM-DD-HH-MM-topic
```

### Can I manually archive a session?

Yes:
```bash
~/.claude/tools/archive-session.py /path/to/session.jsonl
```

### What gets archived?

Each archive directory contains:
- `chunk-001.jsonl` - Full session JSONL (complete history)
- `summary.md` - Intelligent summary with insights
- `metadata.json` - Session statistics

### Can I delete old archives?

Yes, archives are independent files. You can safely delete archive directories you don't need anymore. Consider keeping recent ones for `/continue` to use.

### How do I use the `/continue` command?

In a new Claude Code session, just type:
```
/continue
```

Or say:
- "resume work"
- "pick up where we left off"

The command will load context from your last archived session and recent activity.

---

## Features

### What does the intelligent summary extract?

The summary includes:
- **Accomplishments:** What was completed (keywords: "successfully", "completed", etc.)
- **Files Changed:** All files modified via Edit/Write/NotebookEdit tools
- **Linear Tickets:** Referenced ticket IDs (TEC-xxx, TECH-xxx patterns)
- **Key Decisions:** Decision points from messages (keywords: "decided to", "chose", etc.)
- **Related Artifacts:** Links to brainstorms, plans, solutions created

### Can I customize what gets extracted?

Yes! Edit `~/.claude/tools/archive-session.py` and modify the extraction functions:
- `extract_accomplishments()` - Add/remove accomplishment keywords
- `extract_key_decisions()` - Add/remove decision indicators
- `extract_linear_tickets()` - Modify ticket regex patterns

After changes, regenerate summaries:
```bash
~/.claude/tools/archive-session.py --regenerate-summary ~/docs/sessions/YYYY-MM-DD-HH-MM-topic/
```

### Does `/continue` require Linear integration?

No! Linear integration is optional. `/continue` will work with just:
- Recent session context (last 20 messages)
- Archived session summary

Linear tickets add extra context but aren't required.

### How do I set up Linear integration?

**Option A: Linear MCP (recommended)**
- Configure Linear MCP server in Claude Code settings
- `/continue` will automatically use it

**Option B: Direct API**
- Get API token from https://linear.app/settings/api
- In Claude Code session: `Remember my Linear API token as "linear-api-token": lin_api_xxxxx`

---

## Troubleshooting

### Why isn't my session being archived?

Common reasons:
- Session is under 5MB (check with `du -m <session-file>`)
- Hook not configured in `~/.claude/settings.local.json`
- Archiver script not executable (`chmod +x ~/.claude/tools/archive-session.py`)

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed debugging.

### The summary is missing sections I expected

This is normal if your session didn't contain matching patterns. For example:
- No "Accomplishments" → Session didn't use keywords like "successfully", "completed"
- No "Files Changed" → No Edit/Write/NotebookEdit tool calls
- No "Linear Tickets" → No TEC-xxx or TECH-xxx references

You can manually edit the summary or customize extraction patterns.

### `/continue` command not working

Check:
```bash
# Verify skill is installed
ls -la ~/.claude/skills/continue/
```

Should show `skill.json` and `instructions.md`.

If missing:
```bash
cp -r /path/to/claude-session-manager/skills/continue ~/.claude/skills/
```

### Can I use this with multiple Claude Code installations?

Yes! The environment variables make this flexible. Set different values per installation:

```bash
# Installation 1
export CLAUDE_ARCHIVE_DIR="$HOME/work-archives"
export CLAUDE_SESSION_DIR="$HOME/.claude/projects/work"

# Installation 2
export CLAUDE_ARCHIVE_DIR="$HOME/personal-archives"
export CLAUDE_SESSION_DIR="$HOME/.claude/projects/personal"
```

---

## Technical

### How does automatic archiving work?

After every assistant response, the Stop hook runs `post-response.sh`, which:
1. Finds the current session JSONL file
2. Checks its size in MB
3. If > threshold (default 5MB), runs `archive-session.py`
4. Archive is created in timestamped directory
5. Session continues normally in Claude Code

### Does archiving interrupt my session?

No! Archiving runs asynchronously (doesn't block Claude Code) and the original session file continues to be used. The archive is just a copy for continuity purposes.

### Where are session files stored?

Default: `~/.claude/projects/-home-{username}/`

You can customize with `CLAUDE_SESSION_DIR` environment variable.

### What happens if archiving fails?

The hook will warn you but won't block Claude Code. Your session continues normally. You can manually archive later if needed.

### Can I customize the archive directory naming?

The naming format is fixed: `YYYY-MM-DD-HH-MM-topic-slug`

The topic slug is auto-generated from early user messages (first 5 meaningful words). You can't customize the format, but you can rename directories after archiving.

### Does this work on Windows?

Yes, if you're using WSL (Windows Subsystem for Linux) or Git Bash. Native Windows PowerShell is not currently supported.

### What about privacy/security?

Archives contain the same data as your session files - which may include:
- API keys or tokens in messages
- Sensitive code or data discussed
- Personal information

**Recommendations:**
- Store archives in your encrypted home directory
- Exclude archives from cloud sync if sensitive
- Review summaries before sharing
- Use `.gitignore` to prevent committing archives to repositories

---

## Performance

### How much disk space do archives use?

Approximately the same size as the session JSONL file (~5MB per archive at default threshold). Summaries are small (~10KB).

Example:
- 10 archived sessions = ~50MB disk space
- 100 archived sessions = ~500MB disk space

### Does this slow down Claude Code?

No! The hook runs asynchronously and only does a quick size check after each response (~10-50ms overhead). Actual archiving (1-3 seconds) runs in the background.

### How many messages can be in an archived session?

There's no hard limit. A typical 5MB session contains 100-200 messages depending on message length and tool calls. The archiver can handle thousands of messages if needed.

### Can I archive multiple sessions in parallel?

Yes! Each archive creates an independent timestamped directory. You can run multiple Claude Code sessions simultaneously.

---

## Integration

### Does this work with the Linear MCP?

Yes! If you have Linear MCP configured, `/continue` will automatically use it to query active tickets.

### Can I use this with other project trackers?

Currently only Linear is supported. The `/continue` skill could be extended to support:
- GitHub Issues
- Jira
- Asana
- Other trackers via their APIs

Feel free to contribute extensions!

### Can I export archives to other formats?

The JSONL and summary.md files are standard formats. You can:
- Parse JSONL with any JSON library
- Convert summary.md to HTML, PDF, etc.
- Import into note-taking apps (Obsidian, Notion, etc.)

### Does this integrate with CLTM?

Not yet. Phase 5 of the roadmap includes CLTM integration for:
- Tagging sessions by category/project/technology
- Auto-extracting learnings to CLTM
- Querying CLTM in `/continue` for relevant procedures

---

## Roadmap

### What's planned for future versions?

**Phase 4: Persistence Layer Integration** (not yet implemented)
- Auto-create Linear tickets for pending work
- Track artifacts created during session
- Link sessions to Linear project boards

**Phase 5: CLTM Taxonomy** (documented but not implemented)
- Tag sessions with category/project/technology
- Auto-extract learnings to CLTM
- Query CLTM in `/continue` for relevant procedures

See [CHANGELOG.md](../CHANGELOG.md) for version history.

### Can I contribute?

Yes! Contributions welcome. Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

See [README.md](../README.md#contributing) for details.

### How do I request a feature?

Open an issue on GitHub:
https://github.com/yourusername/claude-session-manager/issues

Include:
- Description of the feature
- Use case / why it's valuable
- Example of how it would work

---

## Comparison

### How is this different from just using `/resume`?

`/resume` loads the entire session history, which:
- Can freeze or timeout with large sessions (>100MB)
- Provides no intelligent context extraction
- Doesn't preserve context across multiple sessions

Claude Session Manager:
- Archives automatically at manageable size
- Extracts actionable insights (what was done, what's next)
- Works across multiple sessions via `/continue`

### How is this different from manual note-taking?

Manual note-taking requires you to:
- Remember to take notes
- Decide what's important
- Organize notes yourself
- Manually link to code/tickets

Claude Session Manager:
- Automatically captures everything
- Intelligently extracts insights
- Structures information consistently
- Links to artifacts automatically

### Can I use both this and manual notes?

Absolutely! This provides automatic baseline continuity. You can still take additional notes for complex topics or decisions.

---

## Support

### Where can I get help?

1. **Documentation:**
   - [README.md](../README.md) - Overview
   - [INSTALL.md](../INSTALL.md) - Installation
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details

2. **GitHub Issues:**
   https://github.com/yourusername/claude-session-manager/issues

3. **Community:**
   - Check existing issues for similar problems
   - Search documentation for keywords
   - Ask in GitHub Discussions (if enabled)

### How do I report a bug?

Open an issue with:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs/error messages
- System info (OS, Python version, Claude Code version)

### How do I suggest improvements?

Open an issue or pull request! We welcome:
- New extraction patterns
- Additional context sources for `/continue`
- Performance optimizations
- Documentation improvements
- UI/UX enhancements

---

## License

### What license is this under?

MIT License - see [LICENSE](../LICENSE) for details.

This means you can:
- Use it commercially
- Modify it freely
- Distribute it
- Use it privately

Just include the original license when distributing.

### Can I use this in commercial projects?

Yes! The MIT License allows commercial use.

### Can I fork and modify it?

Yes! Please do. If you make improvements, consider contributing them back via pull request.

---

Still have questions? [Open an issue](https://github.com/yourusername/claude-session-manager/issues) and we'll add it to the FAQ!
