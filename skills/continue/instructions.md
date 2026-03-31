# /continue - Resume Work from Previous Session

Resume work by loading context from previous sessions and active Linear tickets.

## Purpose

Start a new session with comprehensive context by loading:
- Last 20 messages from current session (recent working context)
- Summary from most recent archived session (what we finished)
- Active Linear tickets from Techno87 workspace (pending work)

This provides instant continuity across sessions without manually reviewing history.

## Workflow

### 1. Load Recent Session Context

Find and parse the current session file:

```bash
# Find current session file (most recently modified JSONL)
CURRENT_SESSION=$(ls -t /home/amadsen/.claude/projects/-home-amadsen/*.jsonl 2>/dev/null | head -1)

if [ -z "$CURRENT_SESSION" ]; then
  echo "No active session found"
  exit 0
fi
```

Use Python to parse the last 20 messages:

```python
import json
from pathlib import Path

def parse_recent_context(session_path: Path, limit: int = 20) -> dict:
    """Parse last N messages from session JSONL."""
    messages = []

    try:
        with session_path.open() as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                if line.strip():
                    try:
                        msg = json.loads(line)
                        messages.append(msg)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Warning: Could not read session: {e}")
        return {'tool_calls': [], 'user_messages': [], 'files_modified': []}

    # Extract patterns
    tool_calls = []
    user_messages = []
    files_modified = set()

    for msg in messages:
        if msg.get('type') == 'assistant':
            # Extract tool calls
            message_data = msg.get('message', {})
            content = message_data.get('content', [])

            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'tool_use':
                        tool_name = block.get('name', '')
                        tool_calls.append({
                            'tool': tool_name,
                            'timestamp': msg.get('timestamp', '')
                        })

                        # Track file modifications
                        if tool_name in ['Edit', 'Write', 'NotebookEdit']:
                            input_data = block.get('input', {})
                            file_path = input_data.get('file_path') or input_data.get('notebook_path')
                            if file_path:
                                files_modified.add(file_path)

        elif msg.get('type') == 'user':
            message_data = msg.get('message', {})
            content = message_data.get('content', '')
            user_messages.append({
                'text': str(content)[:200],
                'timestamp': msg.get('timestamp', '')
            })

    return {
        'tool_calls': tool_calls,
        'user_messages': user_messages,
        'files_modified': sorted(list(files_modified))
    }
```

### 2. Load Most Recent Archived Session

Find and read the most recent archive summary:

```bash
# Find most recent archive summary
LATEST_SUMMARY=$(ls -t /home/amadsen/docs/sessions/*/summary.md 2>/dev/null | head -1)

if [ -n "$LATEST_SUMMARY" ]; then
  # Extract archive directory name for context
  ARCHIVE_DIR=$(dirname "$LATEST_SUMMARY")
  ARCHIVE_NAME=$(basename "$ARCHIVE_DIR")
fi
```

Read the summary.md to get:
- What was accomplished
- Files changed
- Linear tickets referenced
- Key decisions made
- Related artifacts (brainstorms, plans)

### 3. Query Active Linear Tickets

**Option A: Use Linear MCP (if available)**

Check if linear-mcp is available and configured:

```bash
# Check MCP server status
if grep -q "linear" /home/amadsen/.claude/settings.local.json; then
  # Use Linear MCP tools to query active tickets
  # linear_mcp tools available in session
fi
```

**Option B: Direct API Query (fallback)**

If Linear MCP is not available, recall API token from CLTM and query directly:

```python
import requests

def get_active_linear_tickets():
    """Query Linear for active tickets using API token from CLTM."""
    # First, recall Linear API token
    # mcp__claude-ltm__recall("linear api key techno87")

    query = '''
    query {
      issues(filter: {
        state: { type: { nin: ["completed", "canceled"] } }
      }) {
        nodes {
          id
          identifier
          title
          description
          assignee { name }
          state { name }
          project { name }
        }
      }
    }
    '''

    # Token should be retrieved from CLTM
    # response = requests.post(...)
    # return response.json()
```

**Note:** Prefer using Linear MCP tools if available over direct API calls.

### 4. Present Context to User

Format and present the consolidated context:

```markdown
📋 **Resuming Work**

## Last Archived Session: {archive_name}

**Topic:** {session_topic}

**Accomplished:**
- {accomplishment_1}
- {accomplishment_2}
...

**Files Changed:**
- `{file_path_1}`
- `{file_path_2}`
...

**Linear Tickets:**
- {ticket_id_1}
- {ticket_id_2}
...

**Key Decisions:**
- {decision_1}
- {decision_2}
...

**Related Artifacts:**
- [Brainstorm](path/to/brainstorm.md)
- [Plan](path/to/plan.md)

---

## Recent Activity (Last 20 Messages)

**Recent Tools Used:**
- {tool_1} ({count} times)
- {tool_2} ({count} times)
...

**Files Modified Recently:**
- `{recent_file_1}`
- `{recent_file_2}`
...

**Recent Discussion:**
- {recent_user_message_1}
- {recent_user_message_2}
...

---

## Active Linear Tickets

- **{ticket_id}**: {title} - *{state}* (Project: {project})
  {description_summary}

---

**What should we continue working on?**
```

## Implementation Notes

### Execution Order

1. **Recent context** (fast, always available) - Parse current session
2. **Archived summary** (fast, may not exist) - Read last summary.md
3. **Linear tickets** (network call, may fail) - Query active work

Run steps 1 and 2 in parallel for speed. Step 3 can timeout gracefully.

### Error Handling

- **No current session:** Show only archived summary and Linear tickets
- **No archived sessions:** Show only recent context and Linear tickets
- **Linear API failure:** Continue with local context only, warn user
- **Empty session:** Suggest starting fresh or provide Linear tickets only

### Performance Considerations

- Limit recent context to 20 messages (configurable)
- Cache Linear ticket queries (5-minute TTL)
- Skip network calls if offline

### Security Notes

- Linear API token stored in CLTM (never hardcoded)
- Session files may contain sensitive data (don't log contents)
- Archive summaries are sanitized (no secrets)

## Usage Examples

### Basic Usage

User types:
```
/continue
```

Or:
```
Pick up where we left off
```

Or:
```
Resume work
```

### Expected Output

The skill loads context and presents:
- Last session summary (if exists)
- Recent activity from current session
- Active Linear tickets
- Clear question: "What should we continue working on?"

User can then respond with:
- Continue specific ticket: "Let's work on TEC-200"
- Continue recent work: "Continue with the authentication system"
- Start fresh: "Let's start something new"

## Integration with Other Skills

- `/ce:work` - After reviewing context, start executing a plan
- `/ce:brainstorm` - If no clear direction, brainstorm next steps
- `/ce:plan` - Create plan for work identified in Linear tickets

## Future Enhancements (Not Implemented Yet)

- **Smart suggestions:** Analyze context to suggest next task
- **Ticket prioritization:** Rank Linear tickets by urgency/importance
- **Context filtering:** Only show relevant context based on current project
- **Multi-session summary:** Aggregate insights from last N sessions
- **Automatic task creation:** Create Linear tickets for pending work

## Troubleshooting

**Issue:** "No active session found"
- **Cause:** Session file doesn't exist or wrong path
- **Fix:** Check `/home/amadsen/.claude/projects/-home-amadsen/` for JSONL files

**Issue:** "Could not load archived summary"
- **Cause:** No archived sessions exist yet
- **Fix:** This is normal for first-time use, continue will show recent context only

**Issue:** "Linear API query failed"
- **Cause:** Network issue, invalid token, or Linear downtime
- **Fix:** Check CLTM for valid Linear API token, verify network connectivity

**Issue:** Context is too long or overwhelming
- **Cause:** Very active session with many messages
- **Fix:** Reduce limit in parse_recent_context() or summarize tool calls

## Related Documentation

- **Archive README:** `/home/amadsen/docs/sessions/README.md`
- **Phase 1 Summary:** `/home/amadsen/docs/sessions/PHASE1-IMPLEMENTATION-SUMMARY.md`
- **Phase 2 Summary:** `/home/amadsen/docs/sessions/PHASE2-IMPLEMENTATION-SUMMARY.md`
- **Plan:** `/home/amadsen/docs/plans/2026-03-31-feat-session-continuity-management-plan.md`
- **CLTM Taxonomy:** `/home/amadsen/.claude/CLTM-TAXONOMY.yaml`

## Implementation Checklist

When implementing this skill, execute these steps:

- [ ] Find current session JSONL file
- [ ] Parse last 20 messages with error handling
- [ ] Extract tool calls, user messages, files modified
- [ ] Find most recent archive directory
- [ ] Read summary.md from archive
- [ ] Parse summary sections (accomplishments, files, tickets, decisions, artifacts)
- [ ] Check if Linear MCP is available
- [ ] Query Linear for active tickets (use MCP if available, else API)
- [ ] Format consolidated context presentation
- [ ] Present to user with clear "What should we continue working on?" prompt

## Success Criteria

- ✅ Skill triggers from any of the trigger phrases
- ✅ Recent context loads without errors
- ✅ Archived session summary displayed (if exists)
- ✅ Active Linear tickets retrieved (if API available)
- ✅ Output is clear, structured, and actionable
- ✅ User can immediately understand what to continue working on
- ✅ Graceful degradation if any data source unavailable
