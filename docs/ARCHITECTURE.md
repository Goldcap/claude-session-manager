# Architecture

Technical overview of Claude Session Manager's design and implementation.

## System Overview

Claude Session Manager is a three-component system that provides session continuity for Claude Code by automatically archiving large sessions and enabling intelligent work resumption.

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code Session                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  User ←→ Claude Code ←→ Messages stored in JSONL      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ After every response
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Stop Hook Fires                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  post-response.sh checks session file size            │ │
│  │  If > 5MB → trigger archive-session.py                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ If threshold exceeded
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Intelligent Archiving                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. Parse JSONL messages                               │ │
│  │  2. Extract intelligent insights                       │ │
│  │  3. Generate summary.md                                │ │
│  │  4. Move session to archive directory                  │ │
│  │  5. Update index.md                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Creates
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Archive Directory Structure                     │
│  ~/docs/sessions/                                            │
│  ├── index.md                                                │
│  ├── 2026-03-31-15-20-authentication-system/                │
│  │   ├── chunk-001.jsonl                                    │
│  │   ├── summary.md                                         │
│  │   └── metadata.json                                      │
│  └── 2026-04-01-10-30-deploy-api/                           │
│      ├── chunk-001.jsonl                                     │
│      ├── summary.md                                          │
│      └── metadata.json                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Next session
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    /continue Command                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. Load last 20 messages from current session         │ │
│  │  2. Load most recent archived summary                  │ │
│  │  3. Query active Linear tickets                        │ │
│  │  4. Present consolidated context                       │ │
│  │  5. Ask: "What should we continue working on?"         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Post-Response Hook (`post-response.sh`)

**Purpose:** Monitor session size and trigger archiving when threshold exceeded.

**Trigger:** Claude Code's `Stop` hook (fires after every assistant response)

**Execution Mode:** Async (doesn't block Claude Code)

**Logic Flow:**
```bash
1. Find current session file (most recently modified .jsonl)
2. Check file size in MB
3. If size > CLAUDE_THRESHOLD_MB (default: 5):
   4. Execute archive-session.py
   5. Log success or failure
6. Exit (gracefully handles errors)
```

**Configuration:**
- `CLAUDE_SESSION_DIR` - Where session files are stored
- `CLAUDE_ARCHIVE_DIR` - Where to archive sessions
- `CLAUDE_THRESHOLD_MB` - Size threshold for archiving
- `CLAUDE_ARCHIVER` - Path to archiver script

**Error Handling:**
- Silently exits if no session file found
- Warns but continues if archiver fails
- Never blocks Claude Code operation

### 2. Archiver Tool (`archive-session.py`)

**Purpose:** Parse JSONL sessions, extract intelligence, and create structured archives.

**Input:** Path to session JSONL file

**Output:**
- Archive directory with timestamped name
- `summary.md` with intelligent extractions
- `metadata.json` with session stats
- `chunk-001.jsonl` with full session history
- Updated `index.md` in archive root

**Architecture:**

```python
main()
  ├── validate_inputs(session_path)
  ├── parse_session_messages(session_path)
  │     └── Returns: List[dict] of all messages
  │
  ├── Intelligent Extraction (parallel conceptually)
  │   ├── extract_accomplishments(messages)
  │   │     └── Keywords: "successfully", "completed", "created", etc.
  │   ├── extract_files_changed(messages)
  │   │     └── Scans: Edit, Write, NotebookEdit tool calls
  │   ├── extract_linear_tickets(messages)
  │   │     └── Regex: TEC-\d+, TECH-\d+
  │   ├── extract_key_decisions(messages)
  │   │     └── Indicators: "decided to", "chose", "strategy:", etc.
  │   └── extract_artifacts(messages)
  │         └── Detects: docs/brainstorms/, docs/plans/, docs/solutions/
  │
  ├── generate_topic_slug(messages)
  │     └── Extract meaningful keywords, filter common words
  │
  ├── create_archive_directory(topic)
  │     └── Format: YYYY-MM-DD-HH-MM-topic-slug/
  │
  ├── generate_summary_md(extractions, metadata)
  │     └── Comprehensive markdown summary
  │
  ├── save_files(archive_dir)
  │   ├── summary.md
  │   ├── metadata.json
  │   └── chunk-001.jsonl (copy of session)
  │
  └── update_sessions_index(archive_dir, topic, metadata)
        └── Append to ~/docs/sessions/index.md
```

**Key Algorithms:**

**JSONL Parsing:**
```python
def parse_session_messages(session_path: Path) -> List[dict]:
    messages = []
    with open(session_path, 'r') as f:
        for line in f:
            msg = json.loads(line)

            # Handle both string and list content
            if isinstance(msg.get('message', {}).get('content'), list):
                # Tool calls format
                for block in msg['message']['content']:
                    if block.get('type') == 'tool_use':
                        # Extract tool calls
            else:
                # Simple string content

            messages.append(msg)
    return messages
```

**Accomplishment Extraction:**
```python
def extract_accomplishments(messages: List[dict]) -> List[str]:
    keywords = [
        "successfully", "completed", "created", "updated",
        "fixed", "deployed", "tested", "implemented", "✅"
    ]

    accomplishments = []
    for msg in messages:
        if msg['type'] == 'assistant':
            content = get_text_content(msg)
            for line in content.split('\n'):
                if any(kw in line.lower() for kw in keywords):
                    accomplishments.append(line.strip())

    return deduplicate(accomplishments)
```

**File Change Tracking:**
```python
def extract_files_changed(messages: List[dict]) -> List[str]:
    file_paths = set()

    for msg in messages:
        if msg['type'] == 'assistant':
            for tool_call in extract_tool_calls(msg):
                if tool_call['name'] in ['Edit', 'Write', 'NotebookEdit']:
                    file_path = tool_call['input'].get('file_path')
                    if file_path:
                        file_paths.add(file_path)

    return sorted(file_paths)
```

**Topic Slug Generation:**
```python
def generate_topic_slug(messages: List[dict], max_words=5) -> str:
    # Extract keywords from first few user messages
    text = extract_early_user_messages(messages, limit=3)

    # Tokenize and filter
    words = text.lower().split()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}

    meaningful = [w for w in words if w not in stop_words and len(w) > 3]

    # Take first max_words meaningful words
    slug_words = meaningful[:max_words]

    return '-'.join(slug_words)
```

### 3. Continue Skill (`/continue`)

**Purpose:** Load comprehensive context from multiple sources and enable work resumption.

**Triggers:**
- `/continue`
- `resume work`
- `pick up where we left off`

**Architecture:**

```
User invokes /continue
        │
        ▼
┌─────────────────────────────────────────────┐
│  Load Context from Three Sources (parallel) │
├─────────────────────────────────────────────┤
│                                             │
│  1. Current Session (Last 20 Messages)     │
│     ├── Find current session JSONL         │
│     ├── Parse last 20 messages             │
│     ├── Extract tool calls                 │
│     ├── Extract user messages              │
│     └── List files modified                │
│                                             │
│  2. Archived Summary (Most Recent)         │
│     ├── Find latest summary.md             │
│     ├── Read full summary                  │
│     └── Present all sections               │
│                                             │
│  3. Active Linear Tickets                  │
│     ├── Check for Linear MCP               │
│     ├── OR recall API token from CLTM      │
│     ├── Query non-completed tickets        │
│     └── Format ticket list                 │
│                                             │
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│         Format Consolidated Output          │
├─────────────────────────────────────────────┤
│                                             │
│  📋 Resuming Work                          │
│                                             │
│  ## Last Archived Session                  │
│  [Summary content]                          │
│                                             │
│  ## Recent Activity (Last 20 Messages)     │
│  [Recent context]                           │
│                                             │
│  ## Active Linear Tickets                  │
│  [Ticket list]                              │
│                                             │
│  ---                                        │
│  What should we continue working on?       │
│                                             │
└─────────────────────────────────────────────┘
```

**Context Loading:**

**Recent Session Context:**
```python
def parse_recent_context(session_path: Path, limit: int = 20) -> dict:
    messages = parse_jsonl(session_path)
    recent = messages[-limit:]

    return {
        'tool_calls': extract_tool_names(recent),
        'user_messages': extract_user_snippets(recent),
        'files_modified': extract_file_paths(recent)
    }
```

**Archived Summary Loading:**
```bash
# Find most recent summary
LATEST_SUMMARY=$(ls -t ~/docs/sessions/*/summary.md 2>/dev/null | head -1)

if [ -n "$LATEST_SUMMARY" ]; then
    SUMMARY_CONTENT=$(cat "$LATEST_SUMMARY")
    ARCHIVE_NAME=$(basename $(dirname "$LATEST_SUMMARY"))
fi
```

**Linear Integration:**
```graphql
# GraphQL query for active tickets
query {
  issues(filter: {
    state: { type: { nin: ["completed", "canceled"] } }
  }) {
    nodes {
      identifier
      title
      description
      state { name }
      project { name }
      assignee { name }
    }
  }
}
```

## Data Formats

### Session JSONL Format

Each line is a JSON object representing one message:

```json
{"type":"user","message":{"content":"Create authentication"},"timestamp":"2026-03-31T10:00:00"}
{"type":"assistant","message":{"content":"I'll create the auth system"},"timestamp":"2026-03-31T10:00:15"}
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"/path/to/file"}}]},"timestamp":"2026-03-31T10:00:30"}
```

**Message Types:**
- `user` - User input
- `assistant` - Claude response
- `tool_result` - Tool execution result

**Content Types:**
- `string` - Simple text content
- `list` - Tool calls (each item has `type`, `name`, `input`)

### Summary.md Format

```markdown
# Session Summary

**Topic:** [Generated topic slug]
**Messages:** [Count]
**Duration:** [Start] to [End]

## What Was Accomplished
- [Accomplishment 1]
- [Accomplishment 2]

## Files Changed
- [File path 1]
- [File path 2]

## Linear Tickets
- [Ticket ID 1]
- [Ticket ID 2]

## Key Decisions
- [Decision 1]
- [Decision 2]

## Related Artifacts
**Plans:**
- [Link to plan]

**Brainstorms:**
- [Link to brainstorm]

## References
- Full session: `chunk-001.jsonl`
- Metadata: `metadata.json`
```

### Metadata.json Format

```json
{
  "topic": "authentication-system",
  "message_count": 45,
  "start_time": "2026-03-31T10:00:00",
  "end_time": "2026-03-31T14:30:00",
  "session_file": "original-session-name.jsonl",
  "archive_date": "2026-03-31T14:35:00"
}
```

## Performance Characteristics

### Hook Execution
- **Trigger:** After every assistant response
- **Overhead:** ~10-50ms (size check only)
- **Archiving:** 1-3 seconds for 5MB session (async, doesn't block)

### Memory Usage
- **JSONL Parsing:** Streams line-by-line (O(n) space for messages list)
- **Extraction:** In-memory message processing (~10-50MB for 5MB session)
- **Summary Generation:** Minimal (< 1MB)

### Disk I/O
- **Read:** One full session JSONL read (linear scan)
- **Write:**
  - summary.md (< 10KB typically)
  - metadata.json (< 1KB)
  - chunk-001.jsonl (copy of session, 5MB)
  - index.md (append operation, < 1KB)

### Network I/O
- **Linear API:** Optional, only for `/continue` command
- **Timeout:** Configurable (default: 10 seconds)
- **Fallback:** Graceful degradation if unavailable

## Error Handling

### Hook Level
- **No session file:** Exit silently (normal case for first message)
- **Permission denied:** Warn user, continue
- **Archiver failure:** Log error, don't block Claude Code

### Archiver Level
- **Malformed JSON:** Skip invalid lines, continue
- **Missing fields:** Use defaults, log warning
- **Write failure:** Abort archive, keep original session

### Continue Skill Level
- **No current session:** Show archived summary + Linear tickets only
- **No archived sessions:** Show recent context + Linear tickets only
- **Linear API failure:** Show local context, warn user
- **Empty session:** Suggest starting fresh

## Security Considerations

### Sensitive Data
- **Session JSONL:** May contain API keys, tokens, credentials in messages
- **Archive Storage:** Same sensitivity as session files
- **Summary.md:** Extracts from messages (may include sensitive context)

**Recommendations:**
- Store archives in encrypted home directory
- Exclude archives from cloud sync if sensitive
- Review summaries before sharing

### File Permissions
- **Hooks:** 755 (executable by user)
- **Tools:** 755 (executable by user)
- **Archives:** 644 (readable by user, writable by user)
- **Settings:** 644 (readable by user)

### Path Traversal
- All paths validated (no `..` components)
- Archive directory must be absolute or relative to home
- Session directory must be absolute or relative to `.claude/`

## Extension Points

### Custom Extractors

Add new extraction functions to `archive-session.py`:

```python
def extract_custom_pattern(messages: List[dict]) -> List[str]:
    # Your extraction logic
    return results

# In generate_summary_md():
custom_items = extract_custom_pattern(messages)
if custom_items:
    summary += "\n## Custom Section\n\n"
    for item in custom_items:
        summary += f"- {item}\n"
```

### Alternative Storage

Replace file-based storage with database:

```python
def save_to_database(summary: str, metadata: dict, session_jsonl: str):
    # Store in database instead of files
    pass
```

### Additional Context Sources

Extend `/continue` to load from other sources:

```markdown
## GitHub PRs
[Query GitHub API for recent PRs]

## CLTM Procedures
[Recall relevant procedures from CLTM]
```

## Testing Strategy

### Unit Tests
- JSONL parsing with malformed input
- Each extraction function with mock messages
- Topic slug generation with various inputs
- Summary formatting with missing sections

### Integration Tests
- Full archiving flow end-to-end
- `/continue` with all context sources
- Hook triggering and archiver execution
- Index updates with concurrent access

### Manual Testing
- Real session archiving (> 5MB)
- `/continue` in fresh session
- Hook configuration verification
- Error scenarios (no Linear, no archives, etc.)

## Deployment

### Installation
1. Copy hooks to `~/.claude/hooks/`
2. Copy tools to `~/.claude/tools/`
3. Copy skills to `~/.claude/skills/`
4. Configure Stop hook in settings.local.json
5. Verify permissions (chmod +x)

### Configuration
- Set environment variables in `~/.bashrc` or `~/.zshrc`
- Customize extraction patterns in `archive-session.py`
- Adjust size threshold via `CLAUDE_THRESHOLD_MB`

### Monitoring
- Check archive directory for new archives
- Verify summaries are generated correctly
- Test `/continue` command periodically
- Monitor hook execution (check Claude Code logs)

## Future Architecture

### Phase 4: Persistence Layer
```
Claude Code
    │
    ├─► Linear API (create tickets for pending work)
    ├─► Artifact Tracker (link plans/brainstorms to sessions)
    └─► Project Boards (visualize session flow)
```

### Phase 5: CLTM Integration
```
Archive
    │
    ├─► Extract Learnings → CLTM
    ├─► Tag Sessions → CLTM Taxonomy
    └─► Query Procedures → /continue Context
```

---

## References

- [Claude Code Hooks Documentation](https://docs.anthropic.com/claude/claude-code/hooks)
- [JSONL Format Specification](http://jsonlines.org/)
- [Linear API Documentation](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
