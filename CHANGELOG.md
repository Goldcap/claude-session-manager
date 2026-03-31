# Changelog

All notable changes to Claude Session Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-31

### Added

**Initial Release:**

- ✅ Automatic session archiving at 5MB threshold
- ✅ Intelligent summary generation with 6 extraction functions:
  - Accomplishments extraction (keywords: "successfully", "completed", etc.)
  - Files changed tracking (from Edit/Write/NotebookEdit tool calls)
  - Linear ticket detection (TEC-xxx, TECH-xxx patterns)
  - Key decisions extraction (decision indicators in messages)
  - Related artifacts detection (brainstorms, plans, solutions)
  - Comprehensive markdown summary generation
- ✅ `/continue` command for work resumption
- ✅ Linear ticket integration (MCP and direct API support)
- ✅ Environment variable configuration for all paths
- ✅ Complete documentation and examples
- ✅ Automated installation script

**Hook System:**
- `post-response.sh` - Triggered by Stop hook after every response
- Configurable size threshold (default: 5MB)
- Async execution (doesn't block Claude Code)
- Graceful error handling

**Archiving:**
- `archive-session.py` - JSONL parser and intelligent extractor
- Timestamped archive directories with topic slugs
- Full session JSONL preservation
- Metadata JSON with session stats
- Index maintenance (index.md)

**Skills:**
- `/continue` - Resume work command
- Loads last 20 messages from current session
- Loads most recent archived summary
- Queries active Linear tickets
- Presents consolidated, actionable context

**Documentation:**
- Comprehensive README.md
- Step-by-step INSTALL.md
- Example configurations
- Troubleshooting guide

### Configuration

**Environment Variables:**
- `CLAUDE_HOME` - Base directory for Claude Code
- `CLAUDE_SESSION_DIR` - Session JSONL location
- `CLAUDE_ARCHIVE_DIR` - Archive storage location
- `CLAUDE_THRESHOLD_MB` - Size threshold for archiving
- `CLAUDE_ARCHIVER` - Path to archiver script

**Defaults:**
- Archive directory: `~/docs/sessions`
- Size threshold: 5MB
- Async hook execution

## [Unreleased]

### Planned

**Phase 4: Persistence Layer Integration** (Not implemented)
- Auto-create Linear tickets for pending work
- Track artifacts created during session
- Link sessions to Linear project boards

**Phase 5: CLTM Taxonomy** (Documented but not implemented)
- Tag sessions with category/project/technology
- Auto-extract learnings to CLTM
- Query CLTM in `/continue` for relevant procedures

**Future Enhancements:**
- Smart context suggestions based on analysis
- Multi-session summary aggregation
- Configurable extraction patterns
- Ticket prioritization in `/continue`
- Alternative LTM backends (filesystem, database)

---

## Release Notes

### v1.0.0 - Initial Release

This is the first public release of Claude Session Manager, a complete session continuity system for Claude Code.

**Highlights:**
- Prevents context loss by automatically archiving large sessions
- Extracts meaningful insights from session history
- Enables seamless work resumption across sessions
- Integrates with Linear for project tracking
- Zero configuration required (sensible defaults)
- Fully customizable via environment variables

**System Requirements:**
- Claude Code CLI
- Python 3.7+
- Bash shell

**Installation:**
```bash
cd ~/.claude
git clone https://github.com/yourusername/claude-session-manager.git
./claude-session-manager/install.sh
```

**Feedback:**
Please report issues at: https://github.com/yourusername/claude-session-manager/issues

---

[1.0.0]: https://github.com/yourusername/claude-session-manager/releases/tag/v1.0.0
