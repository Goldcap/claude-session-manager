#!/usr/bin/env python3
"""
Archive large session files to prevent /resume freezing.

Usage:
    archive-session.py <session-jsonl-path>
    archive-session.py --regenerate-summary <archive-dir>

Examples:
    archive-session.py /home/amadsen/.claude/projects/-home-amadsen/abc123.jsonl
    archive-session.py --regenerate-summary /home/amadsen/docs/sessions/2026-03-31-14-30-topic/
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
import shutil
import re


def parse_session_metadata(session_path: Path) -> dict:
    """Extract first prompt, message count, timestamps from JSONL.

    Args:
        session_path: Path to session JSONL file

    Returns:
        Dictionary with first_prompt, message_count, created, modified

    Raises:
        ValueError: If JSONL file is empty or malformed
    """
    try:
        with session_path.open() as f:
            first_line = f.readline()
            if not first_line:
                raise ValueError("Session file is empty")

            first_msg = json.loads(first_line)

            # Extract content from message structure
            message_content = first_msg.get('message', {})
            if isinstance(message_content, dict):
                first_prompt = message_content.get('content', '')
            else:
                first_prompt = str(message_content)

            # Handle content as list (tool calls, etc)
            if isinstance(first_prompt, list):
                # Extract text from content blocks
                text_parts = []
                for block in first_prompt:
                    if isinstance(block, dict):
                        if block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                        elif 'text' in block:
                            text_parts.append(block['text'])
                first_prompt = ' '.join(text_parts)

            first_prompt = str(first_prompt).strip()

    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse first message: {e}")

    # Count total messages
    message_count = 0
    try:
        with session_path.open() as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    message_count += 1
    except Exception as e:
        print(f"Warning: Could not count all messages: {e}", file=sys.stderr)
        message_count = 1  # At least we parsed the first one

    # Get file timestamps
    stat = session_path.stat()
    created = datetime.fromtimestamp(stat.st_ctime).isoformat()
    modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

    return {
        'first_prompt': first_prompt[:100],  # Truncate for topic
        'message_count': message_count,
        'created': created,
        'modified': modified,
        'session_file': str(session_path.name)
    }


def generate_topic_slug(first_prompt: str) -> str:
    """Generate kebab-case topic from first prompt.

    Args:
        first_prompt: The first user message from the session

    Returns:
        Kebab-case slug suitable for directory name
    """
    if not first_prompt:
        return "untitled-session"

    # Remove common starting phrases
    prompt = first_prompt.lower()
    for prefix in ['hey ', 'hi ', 'hello ', 'ok ', 'okay ', 'please ', 'can you ']:
        if prompt.startswith(prefix):
            prompt = prompt[len(prefix):]

    # Extract meaningful words
    words = re.findall(r'\w+', prompt)

    # Take first 5 meaningful words (skip very short ones)
    meaningful_words = [w for w in words if len(w) > 2][:5]

    if not meaningful_words:
        # Fallback to any words
        meaningful_words = words[:5] if words else ['session']

    return '-'.join(meaningful_words)


def create_archive_directory(topic: str) -> Path:
    """Create timestamped archive directory.

    Args:
        topic: Topic slug for the session

    Returns:
        Path to created archive directory
    """
    import os
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    archive_name = f"{timestamp}-{topic}"

    # Use environment variable or default to ~/docs/sessions
    archive_base = os.environ.get('CLAUDE_ARCHIVE_DIR', str(Path.home() / "docs/sessions"))
    archive_path = Path(archive_base) / archive_name
    archive_path.mkdir(parents=True, exist_ok=True)
    return archive_path


def parse_session_messages(session_path: Path) -> list:
    """Parse all messages from a session JSONL file.

    Args:
        session_path: Path to session JSONL file

    Returns:
        List of parsed message dictionaries
    """
    messages = []
    try:
        with session_path.open() as f:
            for line in f:
                if line.strip():
                    try:
                        msg = json.loads(line)
                        messages.append(msg)
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
    except Exception as e:
        print(f"Warning: Failed to parse some messages: {e}", file=sys.stderr)

    return messages


def extract_accomplishments(messages: list) -> list:
    """Parse session messages to extract accomplishments.

    Args:
        messages: List of session messages

    Returns:
        List of accomplishment dictionaries with timestamp and text
    """
    accomplishments = []

    for msg in messages:
        if msg.get('type') == 'assistant':
            message_data = msg.get('message', {})
            content = message_data.get('content', '')

            # Handle content as string or list
            if isinstance(content, list):
                # Extract text from content blocks
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                content = ' '.join(text_parts)

            content_str = str(content).lower()

            # Look for completion indicators
            if any(phrase in content_str for phrase in [
                'successfully', 'completed', 'created', 'updated',
                'fixed', 'deployed', 'tested', '✅'
            ]):
                accomplishments.append({
                    'timestamp': msg.get('timestamp', ''),
                    'text': str(content)[:200]  # Summary excerpt
                })

    return accomplishments


def extract_files_changed(messages: list) -> set:
    """Extract files modified during session.

    Args:
        messages: List of session messages

    Returns:
        Set of file paths that were modified
    """
    files = set()

    for msg in messages:
        # Look for tool calls that modify files
        if msg.get('type') == 'assistant':
            message_data = msg.get('message', {})
            content = message_data.get('content', [])

            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'tool_use':
                        tool_name = block.get('name', '')
                        if tool_name in ['Edit', 'Write', 'NotebookEdit']:
                            input_data = block.get('input', {})
                            if 'file_path' in input_data:
                                files.add(input_data['file_path'])
                            # Also check for notebook_path
                            if 'notebook_path' in input_data:
                                files.add(input_data['notebook_path'])

    return files


def extract_linear_tickets(messages: list) -> list:
    """Extract Linear ticket references from session.

    Args:
        messages: List of session messages

    Returns:
        List of ticket dictionaries with id and timestamp
    """
    tickets = []
    ticket_pattern = r'TEC-\d+|TECH-\d+'  # Techno87 workspace pattern

    for msg in messages:
        message_data = msg.get('message', {})
        content = message_data.get('content', '')

        # Handle content as string or list
        if isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                    elif 'text' in block:
                        text_parts.append(block['text'])
            content = ' '.join(text_parts)

        content_str = str(content)
        matches = re.findall(ticket_pattern, content_str)

        for ticket_id in matches:
            if ticket_id not in [t['id'] for t in tickets]:
                tickets.append({
                    'id': ticket_id,
                    'timestamp': msg.get('timestamp', '')
                })

    return tickets


def extract_artifacts(messages: list) -> list:
    """Extract references to brainstorms, plans, and solutions created during session.

    Args:
        messages: List of session messages

    Returns:
        List of artifact dictionaries with type and path
    """
    artifacts = []
    artifact_patterns = {
        'brainstorm': r'docs/brainstorms/[\w\-]+\.md',
        'plan': r'docs/plans/[\w\-]+\.md',
        'solution': r'docs/solutions/[\w\-]+\.md'
    }

    # Track artifacts we've already found
    found_paths = set()

    for msg in messages:
        message_data = msg.get('message', {})
        content = message_data.get('content', '')

        # Handle skill invocations (ce:brainstorm, ce:plan, etc.)
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    # Check for skill invocations in text
                    if block.get('type') == 'text':
                        text = block.get('text', '')
                        # Check for file paths in artifact directories
                        for artifact_type, pattern in artifact_patterns.items():
                            matches = re.findall(pattern, text)
                            for path in matches:
                                if path not in found_paths:
                                    artifacts.append({
                                        'type': artifact_type,
                                        'path': path,
                                        'timestamp': msg.get('timestamp', '')
                                    })
                                    found_paths.add(path)

                    # Check for Write/Edit tool calls to artifact directories
                    elif block.get('type') == 'tool_use':
                        tool_name = block.get('name', '')
                        if tool_name in ['Write', 'Edit']:
                            input_data = block.get('input', {})
                            file_path = input_data.get('file_path', '')

                            # Check if this is an artifact file
                            for artifact_type, pattern in artifact_patterns.items():
                                if re.search(pattern, file_path):
                                    if file_path not in found_paths:
                                        artifacts.append({
                                            'type': artifact_type,
                                            'path': file_path,
                                            'timestamp': msg.get('timestamp', '')
                                        })
                                        found_paths.add(file_path)

        # Also check string content for artifact paths
        elif isinstance(content, str):
            for artifact_type, pattern in artifact_patterns.items():
                matches = re.findall(pattern, content)
                for path in matches:
                    if path not in found_paths:
                        artifacts.append({
                            'type': artifact_type,
                            'path': path,
                            'timestamp': msg.get('timestamp', '')
                        })
                        found_paths.add(path)

    return artifacts


def extract_key_decisions(messages: list) -> list:
    """Extract important decisions made during session.

    Args:
        messages: List of session messages

    Returns:
        List of decision dictionaries with timestamp and text
    """
    decisions = []
    decision_indicators = [
        'decided to', 'chose', 'selected', 'went with',
        'approach:', 'strategy:', 'decision:'
    ]

    for msg in messages:
        if msg.get('type') == 'user':
            message_data = msg.get('message', {})
            content = message_data.get('content', '')

            # Handle content as string
            content_str = str(content).lower()

            if any(indicator in content_str for indicator in decision_indicators):
                decisions.append({
                    'timestamp': msg.get('timestamp', ''),
                    'text': str(content)[:300]
                })

    return decisions


def generate_summary_md(metadata: dict, messages: list) -> str:
    """Generate comprehensive summary.md from session messages.

    Args:
        metadata: Session metadata dictionary
        messages: List of parsed session messages

    Returns:
        Markdown formatted summary text
    """
    accomplishments = extract_accomplishments(messages)
    files = extract_files_changed(messages)
    tickets = extract_linear_tickets(messages)
    decisions = extract_key_decisions(messages)
    artifacts = extract_artifacts(messages)

    summary = f"""# Session Summary

**Topic:** {metadata['first_prompt']}
**Messages:** {metadata['message_count']}
**Duration:** {metadata['created']} to {metadata['modified']}

## What Was Accomplished

"""

    if accomplishments:
        for item in accomplishments:
            summary += f"- {item['text']}\n"
    else:
        summary += "_No specific accomplishments detected._\n"

    summary += "\n## Files Changed\n\n"

    if files:
        for file_path in sorted(files):
            summary += f"- `{file_path}`\n"
    else:
        summary += "_No files modified._\n"

    summary += "\n## Linear Tickets\n\n"

    if tickets:
        for ticket in tickets:
            summary += f"- {ticket['id']}\n"
    else:
        summary += "_No Linear tickets referenced._\n"

    summary += "\n## Key Decisions\n\n"

    if decisions:
        for decision in decisions:
            summary += f"- {decision['text']}\n\n"
    else:
        summary += "_No key decisions captured._\n"

    summary += "\n## Related Artifacts\n\n"

    if artifacts:
        # Group by type
        brainstorms = [a for a in artifacts if a['type'] == 'brainstorm']
        plans = [a for a in artifacts if a['type'] == 'plan']
        solutions = [a for a in artifacts if a['type'] == 'solution']

        if brainstorms:
            summary += "**Brainstorms:**\n"
            for artifact in brainstorms:
                summary += f"- [{artifact['path']}]({artifact['path']})\n"
            summary += "\n"

        if plans:
            summary += "**Plans:**\n"
            for artifact in plans:
                summary += f"- [{artifact['path']}]({artifact['path']})\n"
            summary += "\n"

        if solutions:
            summary += "**Solutions:**\n"
            for artifact in solutions:
                summary += f"- [{artifact['path']}]({artifact['path']})\n"
            summary += "\n"
    else:
        summary += "_No related artifacts created._\n"

    summary += "\n## References\n\n"
    summary += "- Full session: `chunk-001.jsonl`\n"
    summary += "- Metadata: `metadata.json`\n"

    return summary


def update_sessions_index(archive_name: str, metadata: dict):
    """Update docs/sessions/index.md with new entry.

    Args:
        archive_name: Name of the archive directory
        metadata: Session metadata dictionary
    """
    import os

    # Use environment variable or default to ~/docs/sessions
    archive_base = os.environ.get('CLAUDE_ARCHIVE_DIR', str(Path.home() / "docs/sessions"))
    index_path = Path(archive_base) / "index.md"

    # Create index if it doesn't exist
    if not index_path.exists():
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("# Archived Sessions\n\n")

    # Append new entry
    entry = f"""
## [{archive_name}]({archive_name}/)

- **Topic:** {metadata['first_prompt'][:100]}
- **Messages:** {metadata['message_count']}
- **Created:** {metadata['created']}
- **Modified:** {metadata['modified']}

"""

    with index_path.open('a') as f:
        f.write(entry)


def archive_session(session_path: Path):
    """Main archiving logic.

    Args:
        session_path: Path to session JSONL file to archive

    Raises:
        ValueError: If session file is invalid
        IOError: If file operations fail
    """
    if not session_path.exists():
        raise ValueError(f"Session file not found: {session_path}")

    if not session_path.is_file():
        raise ValueError(f"Not a file: {session_path}")

    # Parse metadata
    try:
        metadata = parse_session_metadata(session_path)
    except Exception as e:
        raise ValueError(f"Failed to parse session metadata: {e}")

    topic = generate_topic_slug(metadata['first_prompt'])

    # Create archive directory
    try:
        archive_dir = create_archive_directory(topic)
    except Exception as e:
        raise IOError(f"Failed to create archive directory: {e}")

    # Move session file → chunk-001.jsonl
    chunk_path = archive_dir / "chunk-001.jsonl"
    try:
        shutil.move(str(session_path), str(chunk_path))
    except Exception as e:
        raise IOError(f"Failed to move session file: {e}")

    # Parse messages for intelligent summary generation
    messages = []
    try:
        messages = parse_session_messages(chunk_path)
    except Exception as e:
        print(f"Warning: Failed to parse messages for summary: {e}", file=sys.stderr)

    # Generate summary.md with intelligent extraction
    summary_path = archive_dir / "summary.md"
    try:
        summary_content = generate_summary_md(metadata, messages)
        summary_path.write_text(summary_content)
    except Exception as e:
        # If summary fails, log but don't fail the archive
        print(f"Warning: Failed to generate summary: {e}", file=sys.stderr)

    # Save metadata.json
    metadata_path = archive_dir / "metadata.json"
    try:
        with metadata_path.open('w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save metadata: {e}", file=sys.stderr)

    # Update docs/sessions/index.md
    try:
        update_sessions_index(archive_dir.name, metadata)
    except Exception as e:
        print(f"Warning: Failed to update index: {e}", file=sys.stderr)

    print(f"✅ Archived session to {archive_dir}")


def regenerate_summary(archive_dir: Path):
    """Regenerate summary.md for an existing archive (recovery function).

    Args:
        archive_dir: Path to archive directory

    Raises:
        ValueError: If archive directory is invalid
    """
    if not archive_dir.exists() or not archive_dir.is_dir():
        raise ValueError(f"Archive directory not found: {archive_dir}")

    # Read metadata
    metadata_path = archive_dir / "metadata.json"
    if not metadata_path.exists():
        raise ValueError(f"metadata.json not found in {archive_dir}")

    with metadata_path.open() as f:
        metadata = json.load(f)

    # Find the chunk file (chunk-001.jsonl or higher)
    chunk_files = sorted(archive_dir.glob("chunk-*.jsonl"))
    if not chunk_files:
        raise ValueError(f"No chunk files found in {archive_dir}")

    # Parse messages from the first chunk
    messages = []
    try:
        messages = parse_session_messages(chunk_files[0])
    except Exception as e:
        print(f"Warning: Failed to parse messages: {e}", file=sys.stderr)

    # Regenerate summary with intelligent extraction
    summary_path = archive_dir / "summary.md"
    summary_content = generate_summary_md(metadata, messages)
    summary_path.write_text(summary_content)

    print(f"✅ Regenerated summary for {archive_dir.name}")


def main():
    """Main entry point for the archiver script."""
    parser = argparse.ArgumentParser(
        description='Archive large Claude Code session files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        'session_path',
        type=Path,
        nargs='?',
        help='Path to session JSONL file to archive'
    )

    parser.add_argument(
        '--regenerate-summary',
        type=Path,
        metavar='ARCHIVE_DIR',
        help='Regenerate summary.md for an existing archive directory'
    )

    args = parser.parse_args()

    try:
        if args.regenerate_summary:
            regenerate_summary(args.regenerate_summary)
        elif args.session_path:
            archive_session(args.session_path)
        else:
            parser.print_help()
            sys.exit(1)

    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"❌ I/O Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
