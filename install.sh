#!/bin/bash
# Installation script for Claude Session Manager
# Automates copying files and configuring Claude Code hooks

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "  Claude Session Manager Installation"
echo "========================================"
echo ""

# Determine Claude home directory
CLAUDE_HOME="${CLAUDE_HOME:-$HOME}"
CLAUDE_DIR="$CLAUDE_HOME/.claude"

# Check if Claude Code is installed
if [ ! -d "$CLAUDE_DIR" ]; then
    echo -e "${RED}Error: Claude Code directory not found at $CLAUDE_DIR${NC}"
    echo "Please install Claude Code first: https://claude.com/claude-code"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found Claude Code directory: $CLAUDE_DIR"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p "$CLAUDE_DIR/hooks"
mkdir -p "$CLAUDE_DIR/tools"
mkdir -p "$CLAUDE_DIR/skills"

# Copy hook
echo "Installing post-response hook..."
cp hooks/post-response.sh "$CLAUDE_DIR/hooks/"
chmod +x "$CLAUDE_DIR/hooks/post-response.sh"
echo -e "${GREEN}✓${NC} Installed: $CLAUDE_DIR/hooks/post-response.sh"

# Copy archiver tool
echo "Installing archive-session tool..."
cp tools/archive-session.py "$CLAUDE_DIR/tools/"
chmod +x "$CLAUDE_DIR/tools/archive-session.py"
echo -e "${GREEN}✓${NC} Installed: $CLAUDE_DIR/tools/archive-session.py"

# Copy continue skill
echo "Installing /continue skill..."
cp -r skills/continue "$CLAUDE_DIR/skills/"
echo -e "${GREEN}✓${NC} Installed: $CLAUDE_DIR/skills/continue/"

# Check for settings.local.json
SETTINGS_FILE="$CLAUDE_DIR/settings.local.json"

echo ""
echo "========================================"
echo "  Hook Configuration"
echo "========================================"
echo ""

if [ -f "$SETTINGS_FILE" ]; then
    echo -e "${YELLOW}Found existing settings.local.json${NC}"
    echo ""
    echo "You need to add the Stop hook to your settings.local.json file."
    echo ""
    echo "Add this to your 'hooks' section:"
    echo ""
    cat examples/stop-hook.json
    echo ""
    echo -e "${YELLOW}Would you like me to create a backup and add the hook automatically? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Create backup
        BACKUP_FILE="$SETTINGS_FILE.backup.$(date +%Y%m%d-%H%M%S)"
        cp "$SETTINGS_FILE" "$BACKUP_FILE"
        echo -e "${GREEN}✓${NC} Created backup: $BACKUP_FILE"

        # This is a simple append - user may need to adjust manually
        echo ""
        echo -e "${YELLOW}Note: You may need to manually adjust the JSON structure.${NC}"
        echo "Opening your settings file now..."
        sleep 2

        # Try to open in editor
        if command -v code &> /dev/null; then
            code "$SETTINGS_FILE"
        elif command -v nano &> /dev/null; then
            nano "$SETTINGS_FILE"
        else
            echo "Please edit manually: $SETTINGS_FILE"
        fi
    else
        echo ""
        echo "Please manually add the Stop hook to: $SETTINGS_FILE"
        echo "Example configuration: examples/settings.local.json"
    fi
else
    echo "Creating new settings.local.json..."
    cat > "$SETTINGS_FILE" <<'EOF'
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
    echo -e "${GREEN}✓${NC} Created: $SETTINGS_FILE"
fi

# Create default archive directory
ARCHIVE_DIR="$CLAUDE_HOME/docs/sessions"
mkdir -p "$ARCHIVE_DIR"
echo -e "${GREEN}✓${NC} Created archive directory: $ARCHIVE_DIR"

echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "What was installed:"
echo "  • Hook: $CLAUDE_DIR/hooks/post-response.sh"
echo "  • Archiver: $CLAUDE_DIR/tools/archive-session.py"
echo "  • Skill: $CLAUDE_DIR/skills/continue/"
echo ""
echo "Default configuration:"
echo "  • Archive directory: $ARCHIVE_DIR"
echo "  • Size threshold: 5MB"
echo ""
echo "Next steps:"
echo "  1. Verify hook configuration in $SETTINGS_FILE"
echo "  2. Start using Claude Code normally"
echo "  3. Sessions will auto-archive at 5MB"
echo "  4. Use '/continue' to resume work in new sessions"
echo ""
echo "Customize settings with environment variables:"
echo "  export CLAUDE_ARCHIVE_DIR=\"\$HOME/my-archives\""
echo "  export CLAUDE_THRESHOLD_MB=10"
echo ""
echo "Documentation: README.md"
echo "Troubleshooting: INSTALL.md"
echo ""
echo -e "${GREEN}Happy coding!${NC}"
echo ""
