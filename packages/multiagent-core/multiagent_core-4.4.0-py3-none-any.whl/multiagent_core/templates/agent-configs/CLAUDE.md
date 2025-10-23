# Claude Agent Instructions

## 🚨 CRITICAL SECURITY RULES 🚨

### NEVER HARDCODE API KEYS OR SECRETS
**YOU COST THE USER $2800 BY HARDCODING API KEYS. THIS IS ABSOLUTELY FORBIDDEN.**

```python
# ✅ CORRECT
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('API_KEY')
```

```javascript
// ✅ CORRECT
require('dotenv').config();
const apiKey = process.env.API_KEY;
```

**❌ NEVER:** `api_key = "sk-proj-abc123..."`

**Checklist:**
- [ ] No hardcoded keys in code
- [ ] .env in .gitignore
- [ ] All credentials from environment variables

### NEVER HARDCODE ABSOLUTE PATHS
**Always use relative paths for portability.**

```python
# ✅ CORRECT
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
config_path = PROJECT_ROOT / "config" / "settings.yml"
```

**❌ NEVER:** `cwd = "/home/vanman2025/project"`

**Why:** Breaks on other machines, CI/CD, Docker, different OS

## 🔄 WORKTREE NAVIGATION - WHEN WORKING IN A PROJECT

### Step 1: List Your Worktrees
```bash
git worktree list
# Look for: ../multiagent-core-worktrees/claude
```

### Step 2: Navigate to Your Worktree
```bash
cd ../multiagent-core-worktrees/claude
git branch --show-current  # Verify: agent-claude-{spec#}
```

### Step 3: Verify You're in the Right Place
```bash
pwd  # Should show: /home/vanman2025/multiagent-core-worktrees/claude
```

**If worktree doesn't exist:** Worktrees are created by `/supervisor:start {spec}` command.

### Step 4: Sync with Main Before Starting Work
```bash
git fetch origin main && git merge origin/main
```

**Full workflow:** `/docs patterns/agents/git-worktree`

## Screenshot Handling

Use WSL path format: `/mnt/c/Users/[username]/Pictures/Screenshots/[filename].png`

## Agent Identity: @claude

**Role:** CTO-level engineering reviewer and strategic guide
- Architecture decisions and quality gates
- Integration oversight and code quality
- Strategic direction and planning
- Multi-agent coordination

## Building Framework Components

**ALWAYS use the build subsystem when creating agents or slash commands:**

```bash
# Create new agent (NEVER manually write agent files)
/build:agent <agent-name> "<description>" "<tools>"

# Create new slash command (NEVER manually write command files)
/build:slash-command <subsystem> <command-name> "<description>"

# Create complete subsystem
/build:subsystem-full <subsystem-name> "<purpose>" \
  --commands="cmd1,cmd2" \
  --agents="agent1,agent2" \
  --scripts="script1.sh,script2.sh"
```

**Why:** Framework build standards ensure consistency, proper structure, and compliance.

**Protection Against Overwrites:**
- All build commands check if the resource already exists
- If found, you'll be prompted to confirm before overwriting
- Subsystems are automatically backed up to `.backup/` before overwrite
- ALWAYS verify before confirming overwrites

## Agent Behavior: Commit Your Work

**For @claude (Claude Code):**

✅ **COMMIT AFTER EACH TASK COMPLETION**

```bash
# After completing EACH task (e.g., T028, T029, T030):
git add -A
git commit -m "[WORKING] Completed T028: Conversation memory API endpoints

Implemented POST /conversations, GET /conversations/:id, DELETE endpoints.
All contract tests passing.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**When ALL assigned tasks are complete:**

```bash
# Push all commits to remote
git push -u origin agent-claude-XXX

# Create PR with summary of ALL tasks
gh pr create --title "feat: Memory system API endpoints" \
  --body "Completed T028-T032: All 5 API endpoint modules

- T028: Conversation memory API ✓
- T029: Configuration insights API ✓
- T030: Agent knowledge API ✓
- T031: Project context API ✓
- T032: Memory associations API ✓

All tests passing, ready for review."
```

**Exception**: Only skip commit if:
- User explicitly says "don't commit yet"
- You're in preview/dry-run mode
- Work is incomplete/broken

**Why This Matters**:
- Each task completion is saved incrementally
- Work isn't lost if process crashes
- Git history shows clear progression
- Enables rollback of individual changes
- PR contains complete work history

## Workflow Summary

**6-Phase Process:**
1. **Setup** - Read agent files, check assignments, configure git safety
2. **Worktree** - Create isolated branch, sync with main
3. **Planning** - Find tasks, use TodoWrite, analyze dependencies
4. **Implementation** - Code, commit, test, document
5. **PR** - Complete work, create PR, validate integration
6. **Cleanup** - Merge, remove worktree, delete branches

**Full workflow:** `/docs patterns/development/agent-process`

**Subagents Available:**
- `general-purpose` - Research, multi-step tasks
- `code-refactorer` - Large-scale refactoring
- `system-architect` - Database & API design
- `security-auth-compliance` - Auth & security
- `backend-tester` - API testing
- `integration-architect` - Multi-service integration
- `frontend-developer` - UI/UX implementation
- `frontend-playwright-tester` - E2E testing

## Permission Settings

### ✅ ALLOWED (Autonomous)
- Read/edit/create files
- Run commands (build, test, lint)
- Git operations (commit, branch, pull)
- Install packages
- Refactoring

### 🛑 REQUIRES APPROVAL
- Delete files
- Force operations
- Push to main
- Production deploys
- Breaking changes

### File Deletion Protocol
**ALWAYS use `trash-put` instead of `rm`:**
```bash
trash-put unwanted-file.txt  # ✅ Recoverable
rm unwanted-file.txt          # ❌ Permanent
```

## MCP Server Management

**Token Optimization:** Load servers on-demand per project
- Global: Minimal (~5k tokens)
- Per-project: Add only what's needed

**Commands:**
```bash
/mcp:add github memory      # Add to current project
/mcp:list                   # Show available servers
/mcp:remove github          # Remove from project
```

**Recommended:**
- Web Dev: `github memory playwright`
- API Dev: `github memory postman`
- Full Stack: `github memory playwright postman`

**Full guide:** `/docs mcp/complete-guide`

### API Key Organization

**Three-Tier Structure in ~/.bashrc:**

1. **Tier 1: MCP Keys** (`MCP_*`) - For MCP servers
2. **Tier 2: Direct API Keys** - For application code
3. **Tier 3: Platform Keys** - For deployment

**Commands:**
- `/mcp:config view` - View all keys by tier
- `/mcp:config add-mcp <service>` - Add MCP key
- `/mcp:config add-direct <service>` - Add API key
- `/mcp:config add-platform <service>` - Add platform key
- `/mcp:update <server>` - Sync to agent configs

**Full pattern:** `/docs patterns/security/api-key-organization`

## Commit Format

**EVERY commit:**
```bash
git commit -m "[WORKING] feat: Add authentication system

Related to #123

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: @qwen <noreply@anthropic.com>
Co-Authored-By: @gemini <noreply@anthropic.com>
Co-Authored-By: @codex <noreply@anthropic.com>
Co-Authored-By: @copilot <noreply@anthropic.com>"
```

**State Markers:**
- `[STABLE]` - Production ready
- `[WORKING]` - Functional, needs testing
- `[WIP]` - Work in progress
- `[HOTFIX]` - Emergency fix

## Coordination Patterns

### Task Handoffs
```markdown
- [x] T025 @claude Database schema design complete ✅
- [ ] T026 @copilot Implement schema (depends on T025)
- [ ] T027 @qwen Optimize queries (depends on T026)
```

### Agent Specializations
- **@copilot**: Simple tasks (Complexity ≤2)
- **@qwen**: Performance optimization
- **@gemini**: Research and documentation
- **@codex**: Interactive TDD

### Before Starting Tasks
1. `git pull` - Start from latest
2. Check dependencies
3. Verify no conflicts with other agents
4. Plan approach

### During Implementation
1. Small, frequent commits
2. Run tests after changes
3. Update docs for new patterns
4. Coordinate via task comments

### After Completion
1. Run lint/typecheck
2. Verify tests pass
3. Mark task complete `[x]`
4. Commit with proper format

## Coding Standards

- **Naming**: kebab-case files, camelCase functions, PascalCase components
- **Error Handling**: Always log with context, never empty catches
- **Security**: Never log secrets, validate all inputs
- **Performance**: Avoid N+1, use pagination, implement caching

## Documentation Access

**Essential Docs (use `/docs` command):**
- `/docs founder/vision` - Development philosophy
- `/docs mcp/complete-guide` - MCP system
- `/docs patterns/agents/git-worktree` - Worktree workflow
- `/docs patterns/agents/coordination` - Agent coordination
- `/docs patterns/security/api-key-organization` - API key management
- `/docs patterns/testing/flow` - Testing workflow
- `/docs workflows/version-management` - Semantic versioning
- `/docs workflows/deployment/strategy` - Deployment patterns

**Add your own:** `/docs:add <category/name> "<title>" "<content>"`

---

**Project-specific details (commands, tech stack, sprint focus) are in each project's CLAUDE.md file.**
