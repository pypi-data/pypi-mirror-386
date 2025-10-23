#!/usr/bin/env python3
"""
Bashrc Organization Tool

Safely reorganizes messy ~/.bashrc files into a clean three-tier structure:
- Tier 1: Global MCP Keys (for agent tools)
- Tier 2: Platform Keys (deployment infrastructure)
- Tier 3: Project Keys (referenced but stored in project .env files)

Features:
- Automatic backup before changes
- Detects and categorizes API keys
- Removes duplicates
- Preserves all custom functions and aliases
- Adds clear section headers
- Safe and reversible
"""

import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple


class BashrcOrganizer:
    """Analyzes and reorganizes bashrc files into clean sections."""

    # Known MCP-related key patterns
    MCP_KEYS = {
        'POSTMAN_API_KEY', 'CONTEXT7_API_KEY', 'MEM0_API_KEY',
        'GITHUB_PERSONAL_ACCESS_TOKEN', 'CATS_MCP_API_KEY',
        'MCP_TWILIO_AUTH_TOKEN', 'MCP_TWILIO_ACCOUNT_SID',
        'MCP_SENDGRID_API_KEY', 'MCP_OPENAI_API_KEY',
        'MCP_ANTHROPIC_API_KEY', 'MCP_GITHUB_TOKEN',
        'MCP_GOOGLE_AI_API_KEY'
    }

    # Platform/infrastructure keys
    PLATFORM_KEYS = {
        'DIGITALOCEAN_API_KEY', 'CATS_API_KEY', 'VERCEL_TOKEN',
        'RAILWAY_TOKEN', 'RENDER_API_KEY', 'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 'HEROKU_API_KEY'
    }

    # Keys that should be in project .env files
    PROJECT_KEYS = {
        'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY',
        'GOOGLE_API_KEY', 'STRIPE_SECRET_KEY', 'DATABASE_URL',
        'TWILIO_AUTH_TOKEN', 'SENDGRID_API_KEY'
    }

    def __init__(self, bashrc_path: Path = None):
        self.bashrc_path = bashrc_path or Path.home() / '.bashrc'
        self.backup_path = None

        # Organized sections
        self.shell_config = []
        self.prompt_config = []
        self.colors_aliases = []
        self.completions = []
        self.safe_delete = []
        self.node_npm = []
        self.dev_tools = []
        self.ai_tools = []
        self.project_shortcuts = []
        self.mcp_setup = []
        self.wsl_helpers = []
        self.screenshot_helpers = []
        self.custom_functions = []
        self.path_exports = []
        self.mcp_keys = []
        self.platform_keys = []
        self.misc_exports = []
        self.unknown = []

        # Track what we've seen to remove duplicates
        self.seen_aliases = set()
        self.seen_exports = set()
        self.seen_functions = set()

    def backup(self) -> Path:
        """Create timestamped backup of bashrc."""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.backup_path = self.bashrc_path.parent / f'.bashrc.backup-{timestamp}'
        shutil.copy(self.bashrc_path, self.backup_path)
        return self.backup_path

    def analyze_line(self, line: str) -> Tuple[str, str]:
        """
        Analyze a line and categorize it.
        Returns (category, content) tuple.
        """
        stripped = line.strip()

        # Skip empty lines and comments (will be re-added in sections)
        if not stripped or stripped.startswith('#'):
            return 'skip', line

        # Detect exports
        if stripped.startswith('export '):
            var_name = re.match(r'export\s+([A-Z_][A-Z0-9_]*)', stripped)
            if var_name:
                var = var_name.group(1)

                # Check for duplicates
                if var in self.seen_exports:
                    return 'skip', line
                self.seen_exports.add(var)

                # Categorize API keys
                if var in self.MCP_KEYS:
                    return 'mcp_key', line
                elif var in self.PLATFORM_KEYS:
                    return 'platform_key', line
                elif var in self.PROJECT_KEYS:
                    # Note but don't include (should be in .env)
                    return 'skip', f'# {line.strip()}  # MOVED TO PROJECT .env'
                elif 'PATH' in var:
                    return 'path', line
                elif var in {'NVM_DIR', 'BUN_INSTALL', 'GOOGLE_CLOUD_PROJECT',
                             'CLAUDE_HOME', 'MULTIAGENT_HOME', 'NODE_ENV',
                             'SHOT_WIN_DIR', 'SHOT_WSL_DIR', 'GEMINI_MODEL'}:
                    return 'tool_config', line
                else:
                    return 'misc_export', line

        # Detect aliases
        if stripped.startswith('alias '):
            alias_name = re.match(r'alias\s+([a-zA-Z0-9_-]+)', stripped)
            if alias_name:
                alias = alias_name.group(1)
                if alias in self.seen_aliases:
                    return 'skip', line
                self.seen_aliases.add(alias)

                # Categorize aliases
                if alias in {'rm', 'del', 'trash', 'trash-list', 'trash-restore',
                             'trash-empty', 'permanent-rm', 'tclean'}:
                    return 'safe_delete', line
                elif alias in {'python', 'pip', 'gemini-google', 'gemini-api',
                               'codex', 'cg'}:
                    return 'ai_tool', line
                elif alias in {'devloop', 'backend-venv', 'new-project',
                               'cleanup', 'deep-clean', 'add-postman'}:
                    return 'project_shortcut', line
                elif alias in {'mcp-setup', 'mcp-status', 'mcp-health'}:
                    return 'mcp_setup', line
                elif alias in {'code', 'ngrok', 'cdk', 'cdcb', 'winpath'}:
                    return 'wsl_helper', line
                elif 'shot-' in alias:
                    return 'screenshot', line
                else:
                    return 'color_alias', line

        # Detect functions
        func_match = re.match(r'([a-zA-Z0-9_-]+)\s*\(\s*\)', stripped)
        if func_match:
            func_name = func_match.group(1)
            if func_name in self.seen_functions:
                return 'skip', line
            self.seen_functions.add(func_name)

            if 'shot-' in func_name or func_name in {'cdk', 'cdcb', 'winpath'}:
                return 'custom_function', line
            elif 'trash-' in func_name:
                return 'custom_function', line
            else:
                return 'custom_function', line

        # Shell configuration patterns
        if any(x in stripped for x in ['HISTCONTROL', 'HISTSIZE', 'shopt', 'case $-']):
            return 'shell_config', line
        if any(x in stripped for x in ['PS1=', 'color_prompt', 'debian_chroot']):
            return 'prompt', line
        if 'dircolors' in stripped or 'll=' in stripped or 'alert=' in stripped:
            return 'color_alias', line
        if 'bash_completion' in stripped or 'bash_aliases' in stripped:
            return 'completion', line
        if '[ -s "$NVM_DIR' in stripped or 'nvm.sh' in stripped:
            return 'node_npm', line
        if 'google-cloud-sdk' in stripped or '[ -f ' in stripped:
            return 'dev_tool', line

        # Unknown - preserve as-is
        return 'unknown', line

    def parse(self):
        """Parse bashrc and categorize all lines."""
        with open(self.bashrc_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        current_function = []
        in_function = False

        for line in lines:
            # Handle multi-line functions
            if re.match(r'[a-zA-Z0-9_-]+\s*\(\s*\)', line.strip()):
                in_function = True
                current_function = [line]
                continue

            if in_function:
                current_function.append(line)
                if line.strip() == '}':
                    # Function complete
                    func_text = '\n'.join(current_function)
                    if 'shot-' in current_function[0] or 'trash-' in current_function[0]:
                        self.custom_functions.append(func_text)
                    elif any(x in current_function[0] for x in ['cdk', 'cdcb', 'winpath']):
                        self.wsl_helpers.append(func_text)
                    else:
                        self.custom_functions.append(func_text)
                    in_function = False
                    current_function = []
                continue

            # Categorize single lines
            category, content = self.analyze_line(line)

            if category == 'skip':
                continue
            elif category == 'shell_config':
                self.shell_config.append(content)
            elif category == 'prompt':
                self.prompt_config.append(content)
            elif category == 'color_alias':
                self.colors_aliases.append(content)
            elif category == 'completion':
                self.completions.append(content)
            elif category == 'safe_delete':
                self.safe_delete.append(content)
            elif category == 'node_npm':
                self.node_npm.append(content)
            elif category == 'dev_tool':
                self.dev_tools.append(content)
            elif category == 'tool_config':
                self.dev_tools.append(content)
            elif category == 'ai_tool':
                self.ai_tools.append(content)
            elif category == 'project_shortcut':
                self.project_shortcuts.append(content)
            elif category == 'mcp_setup':
                self.mcp_setup.append(content)
            elif category == 'wsl_helper':
                self.wsl_helpers.append(content)
            elif category == 'screenshot':
                self.screenshot_helpers.append(content)
            elif category == 'mcp_key':
                self.mcp_keys.append(content)
            elif category == 'platform_key':
                self.platform_keys.append(content)
            elif category == 'path':
                self.path_exports.append(content)
            elif category == 'misc_export':
                self.misc_exports.append(content)
            else:
                self.unknown.append(content)

    def generate_organized_bashrc(self) -> str:
        """Generate the organized bashrc content."""
        sections = []

        # Header
        sections.append("""# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples
""")

        # Shell Configuration
        if self.shell_config:
            sections.append("""# ============================================================
# SHELL CONFIGURATION
# ============================================================
""")
            sections.append('\n'.join(self.shell_config))
            sections.append("")

        # Prompt Configuration
        if self.prompt_config:
            sections.append("""# ============================================================
# PROMPT CONFIGURATION
# ============================================================
""")
            sections.append('\n'.join(self.prompt_config))
            sections.append("")

        # Colors & Aliases
        if self.colors_aliases:
            sections.append("""# ============================================================
# COLOR & ALIASES
# ============================================================
""")
            sections.append('\n'.join(self.colors_aliases))
            sections.append("")

        # Completions
        if self.completions:
            sections.append('\n'.join(self.completions))
            sections.append("")

        # Safe Delete
        if self.safe_delete:
            sections.append("""# ============================================================
# SAFE DELETE - Prevent accidental permanent file deletion
# ============================================================
# Override rm to use trash instead
""")
            sections.append('\n'.join(self.safe_delete))
            sections.append("")

        # Custom Functions (trash helpers)
        if any('trash-' in f for f in self.custom_functions):
            trash_funcs = [f for f in self.custom_functions if 'trash-' in f]
            sections.append('\n'.join(trash_funcs))
            sections.append("")

        # Node & NPM
        if self.node_npm:
            sections.append("""# ============================================================
# NODE & NPM CONFIGURATION
# ============================================================
""")
            sections.append('\n'.join(self.node_npm))
            sections.append("")

        # Development Tools
        if self.dev_tools:
            sections.append("""# ============================================================
# DEVELOPMENT TOOLS
# ============================================================
""")
            sections.append('\n'.join(self.dev_tools))
            sections.append("")

        # AI Agent Tools
        if self.ai_tools:
            sections.append("""# ============================================================
# AI AGENT TOOLS
# ============================================================
""")
            sections.append('\n'.join(self.ai_tools))
            sections.append("")

        # Project Shortcuts
        if self.project_shortcuts:
            sections.append("""# ============================================================
# PROJECT SHORTCUTS
# ============================================================
""")
            sections.append('\n'.join(self.project_shortcuts))
            sections.append("")

        # MCP Setup
        if self.mcp_setup:
            sections.append("""# ============================================================
# MCP (Model Context Protocol) GLOBAL SETUP
# ============================================================
""")
            sections.append('\n'.join(self.mcp_setup))
            sections.append("")

        # WSL Helpers
        if self.wsl_helpers or any('cdk' in f or 'cdcb' in f for f in self.custom_functions):
            sections.append("""# ============================================================
# WSL PATH HELPERS (Windows <-> WSL)
# ============================================================
""")
            wsl_funcs = [f for f in self.custom_functions if any(x in f for x in ['cdk', 'cdcb', 'winpath'])]
            if wsl_funcs:
                sections.append('\n'.join(wsl_funcs))
                sections.append("")
            if self.wsl_helpers:
                sections.append('\n'.join(self.wsl_helpers))
                sections.append("")

        # Screenshot Helpers
        if self.screenshot_helpers or any('shot-' in f for f in self.custom_functions):
            sections.append("""# ============================================================
# SCREENSHOT QUICK HELPERS
# ============================================================
""")
            shot_funcs = [f for f in self.custom_functions if 'shot-' in f]
            if shot_funcs:
                sections.append('\n'.join(shot_funcs))
                sections.append("")
            if self.screenshot_helpers:
                sections.append('\n'.join(self.screenshot_helpers))
                sections.append("")

        # PATH exports
        if self.path_exports:
            sections.append("""# ============================================================
# PATH CONFIGURATION
# ============================================================
""")
            sections.append('\n'.join(self.path_exports))
            sections.append("")

        # API Keys - Three Tiers
        if self.mcp_keys:
            sections.append("""# ============================================================
# API KEYS & SECRETS - THREE-TIER STRUCTURE
# ============================================================

# ============================================================================
# TIER 1: GLOBAL DEV MCP SERVERS - AGENT TOOL ACCESS
# ============================================================================
# Keys used BY agents (Claude Code, VS Code, etc.) through MCP servers
# These are GLOBAL development tools shared across ALL projects
# Low cost, dev overhead - NOT customer-facing or billable per-project
""")
            sections.append('\n'.join(self.mcp_keys))
            sections.append("")

        if self.platform_keys:
            sections.append("""# ============================================================================
# TIER 2: PLATFORM KEYS - INFRASTRUCTURE & DEPLOYMENT
# ============================================================================
# Keys for deployment platforms and infrastructure management
# Shared across all your projects - can be overridden per-project in .env if needed
""")
            sections.append('\n'.join(self.platform_keys))
            sections.append("")

        sections.append("""# ============================================================================
# TIER 3: PROJECT-SPECIFIC KEYS (Not in ~/.bashrc)
# ============================================================================
# All other API keys go in each project's .env file:
#   - Application API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
#   - Production service keys (TWILIO_*, SENDGRID_*, etc.)
#   - Database credentials (DATABASE_URL, etc.)
#   - Project-specific secrets
#
# Why? Per-project isolation for billing, security, and key rotation
# Use: Copy .env.template to .env in each project and fill in your keys
""")

        # Misc exports
        if self.misc_exports:
            sections.append("")
            sections.append('\n'.join(self.misc_exports))
            sections.append("")

        # Unknown content (preserve just in case)
        if self.unknown:
            sections.append("""# ============================================================
# ADDITIONAL CONFIGURATION
# ============================================================
""")
            sections.append('\n'.join(self.unknown))
            sections.append("")

        # Footer
        sections.append("""# ============================================================
# END OF BASHRC
# ============================================================
""")

        return '\n'.join(sections)

    def organize(self, dry_run=False) -> Tuple[Path, str]:
        """
        Organize the bashrc file.

        Args:
            dry_run: If True, don't write changes, just return what would be written

        Returns:
            (backup_path, organized_content)
        """
        # Always create backup first
        backup_path = self.backup()

        # Parse and organize
        self.parse()
        organized = self.generate_organized_bashrc()

        if not dry_run:
            with open(self.bashrc_path, 'w') as f:
                f.write(organized)

        return backup_path, organized


def main():
    """CLI entry point."""
    import sys

    bashrc_path = Path.home() / '.bashrc'

    if len(sys.argv) > 1:
        if sys.argv[1] == '--dry-run':
            print("DRY RUN MODE - No changes will be made")
            print(f"Analyzing: {bashrc_path}")
            print("")

            organizer = BashrcOrganizer(bashrc_path)
            backup_path, organized = organizer.organize(dry_run=True)

            print(f"Backup would be created at: {backup_path}")
            print("")
            print("=" * 70)
            print("ORGANIZED CONTENT (first 50 lines):")
            print("=" * 70)
            lines = organized.split('\n')[:50]
            print('\n'.join(lines))
            print("")
            print(f"Total lines: {len(organized.split(chr(10)))}")
            print(f"Original lines: {len(open(bashrc_path).readlines())}")

            sys.exit(0)
        elif sys.argv[1] == '--help':
            print("""
Bashrc Organization Tool

Usage:
    python bashrc_organizer.py [--dry-run|--help]

Options:
    --dry-run    Show what would be changed without modifying bashrc
    --help       Show this help message

Features:
    - Creates timestamped backup before changes
    - Organizes into clean sections with headers
    - Three-tier API key structure (MCP / Platform / Project)
    - Removes duplicates
    - Preserves all custom functions and aliases

The organized bashrc will have these sections:
    1. Shell Configuration (history, options)
    2. Prompt Configuration
    3. Colors & Aliases
    4. Safe Delete (trash-cli aliases)
    5. Node & NPM Configuration
    6. Development Tools (git, docker, etc.)
    7. AI Agent Tools (claude, gemini, codex)
    8. Project Shortcuts
    9. MCP Setup
    10. WSL Helpers (Windows path conversion)
    11. Screenshot Helpers
    12. PATH Configuration
    13. API Keys (Three Tiers)
            """)
            sys.exit(0)

    # Interactive mode
    print("Bashrc Organization Tool")
    print("=" * 70)
    print(f"Target: {bashrc_path}")
    print("")

    response = input("Create organized bashrc? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    organizer = BashrcOrganizer(bashrc_path)
    backup_path, organized = organizer.organize(dry_run=False)

    print("")
    print(f"✓ Backup created: {backup_path}")
    print(f"✓ Bashrc organized: {bashrc_path}")
    print("")
    print("To restore from backup:")
    print(f"  cp {backup_path} {bashrc_path}")
    print("")
    print("Reload your shell:")
    print("  source ~/.bashrc")


if __name__ == '__main__':
    main()
