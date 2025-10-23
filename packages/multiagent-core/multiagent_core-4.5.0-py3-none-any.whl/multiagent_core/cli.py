"""Multi-Agent Core CLI

Command-line interface for the multi-agent development framework.
"""

from __future__ import annotations

import click
import json
import os
import subprocess
import tempfile
import requests
import glob
import threading
from typing import Any, Dict, Optional, Tuple, List
from packaging import version
try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata
from importlib import resources as importlib_resources
import shutil
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from shutil import which
from .config import config
# from .feedback import runtime as feedback_runtime  # Legacy - removed
# Docker imports removed - using simple file operations instead
from . import __version__
from .init_progress import InitProgress, create_init_phases
from .utils.version_detection import _save_current_version

console = Console()


def _load_version_metadata() -> Dict[str, Any]:
    """Return version metadata bundled with the package if available."""

    candidate_paths = [
        Path(__file__).resolve().parent / "VERSION",
        Path(__file__).resolve().parent.parent / "VERSION",
        Path.cwd() / "VERSION",
        Path.home() / ".multiagent" / "VERSION",
    ]

    for candidate in candidate_paths:
        if candidate.exists():
            try:
                with candidate.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    return data
            except (OSError, json.JSONDecodeError):
                continue

    try:
        with importlib_resources.files("multiagent_core").joinpath("VERSION").open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        pass

    return {}


def _current_framework_version() -> str:
    """Return the installed multiagent-core version string."""

    metadata_blob = _load_version_metadata()
    version_value = metadata_blob.get("version") if metadata_blob else None
    return str(version_value) if version_value else (__version__ or "unknown")


def _resolve_component_version(package_name: str, fallback: Optional[str] = None) -> str:
    """Best-effort lookup for a companion package version."""

    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return fallback or "unknown"
    except Exception:  # pragma: no cover - unexpected importlib issues
        return fallback or "unknown"


def _locate_specify_executable() -> Optional[str]:
    """Return the best-effort path to the `specify` CLI if available."""

    candidates = []
    env_path = which('specify')
    if env_path:
        candidates.append(env_path)

    fallback_paths = [
        Path.home() / '.local' / 'bin' / 'specify',
        Path.home() / '.npm-global' / 'bin' / 'specify',
        Path('/usr/local/bin/specify'),
        Path('/usr/bin/specify'),
    ]

    for candidate in fallback_paths:
        candidate_str = str(candidate)
        if candidate.exists() and candidate_str not in candidates:
            candidates.append(candidate_str)

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate

    return None


def _spec_kit_available() -> Tuple[bool, Optional[str]]:
    """Detect whether spec-kit is accessible on the current PATH."""

    specify_path = _locate_specify_executable()
    if not specify_path:
        return False, None

    try:
        result = subprocess.run(
            [specify_path, '--help'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, specify_path
    except (FileNotFoundError, subprocess.SubprocessError):
        return False, specify_path

    return False, specify_path

@click.group()
@click.version_option(__version__)
def main():
    """Multi-Agent Development Framework CLI"""
    # Auto-detect WSL environment and warn if using wrong Python
    _check_python_environment()
    # Check for updates on every command (non-blocking)
    _check_for_updates_async()
    pass

@main.command()
@click.argument('path', type=click.Path(), required=False)
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--create-repo', is_flag=True, help='Create a GitHub repository')
@click.option('--interactive/--no-interactive', default=True, help='Use interactive prompts to configure initialization')
@click.option('--backend-heavy', is_flag=True, help='Optimize for backend development (minimal frontend scaffolding)')
def init(path, dry_run, create_repo, interactive, backend_heavy):
    """Initialize multi-agent framework in a new or existing directory."""

    # Initialize progress tracker (unless dry_run)
    progress = None
    if not dry_run:
        progress = InitProgress(console)
        # Add all initialization phases
        for phase_name, steps in create_init_phases():
            progress.add_phase(phase_name, steps)

        # Start Phase 1: Prerequisites
        progress.start_phase("Phase 1: Prerequisites")

    # Check if spec-kit is installed (REQUIRED)
    spec_kit_available, spec_kit_path = _spec_kit_available()
    if progress:
        progress.complete_step("Phase 1: Prerequisites", "Check spec-kit installation")

    if not spec_kit_available:
        console.print("[bold yellow]WARNING: Spec-Kit Not Found[/bold yellow]")
        console.print("\nMultiAgent works with spec-kit for specification-driven development.")
        console.print("Please install spec-kit first:\n")
        console.print("  [cyan]# Install uv if needed[/cyan]")
        console.print("  [cyan]curl -LsSf https://astral.sh/uv/install.sh | sh[/cyan]")
        console.print("  [cyan]# Install spec-kit[/cyan]")
        console.print("  [cyan]uv tool install specify-cli --from git+https://github.com/github/spec-kit.git[/cyan]")
        console.print("  [cyan]# Verify installation[/cyan]")
        console.print("  [cyan]specify check[/cyan]\n")

        if interactive:
            if not click.confirm("Continue without spec-kit? (not recommended)", default=False):
                console.print("[red]Initialization cancelled. Please install spec-kit first.[/red]")
                return
        else:
            console.print("[yellow]Continuing without spec-kit (not recommended)[/yellow]")
    else:
        if spec_kit_path:
            console.print(f"[dim]spec-kit detected at {spec_kit_path}[/dim]")

    if path:
        target_path = Path(path).resolve()
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            console.print(f"[red]Error creating directory {target_path}: {e}[/red]")
            return
    else:
        target_path = Path.cwd()

    # Change current working directory to the target path
    os.chdir(target_path)
    cwd = target_path

    if progress:
        progress.complete_step("Phase 1: Prerequisites", "Verify package installation")
        progress.complete_step("Phase 1: Prerequisites", "Validate target directory")

    if dry_run:
        console.print("[bold blue]Dry run mode - no changes will be made[/bold blue]")

    if backend_heavy:
        console.print("[bold blue]Backend-heavy mode - optimizing for backend development[/bold blue]")

    console.print(f"Initializing multi-agent framework in: {cwd}")

    # Check if already initialized
    already_initialized = (cwd / ".multiagent" / "config.json").exists()

    if already_initialized:
        console.print("[dim]OK Project already initialized - re-registering[/dim]")
        # Re-register project (updates registry)
        _register_project(cwd, console)
        console.print("[green][OK] Project re-initialized successfully[/green]")
        return

    # Interactive setup prompts
    # Initialize defaults first
    git_exists = (cwd / ".git").exists()
    use_existing_git = git_exists  # Default to using existing git if it exists
    create_github = create_repo
    install_git_hooks = True
    install_issue_templates = False  # Default to not installing in non-interactive mode

    if not dry_run and interactive:
        # Check if existing git repository
        github_remote_exists = False

        if git_exists:
            # Check if GitHub remote already exists
            try:
                result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                      cwd=str(cwd), capture_output=True, text=True)
                if result.returncode == 0 and 'github.com' in result.stdout:
                    github_remote_exists = True
                    console.print(f"[yellow]GitHub remote detected: {result.stdout.strip()}[/yellow]")
                    if not click.confirm("Overwrite existing GitHub repository configuration?", default=False):
                        console.print("[dim]Keeping existing GitHub configuration[/dim]")
                        create_github = False
                    else:
                        create_github = click.confirm("Continue with GitHub repository setup?", default=True)
                else:
                    use_existing_git = click.confirm("Existing git repository detected. Use existing repository?", default=True)
                    create_github = create_repo or click.confirm("Create GitHub repository?", default=False)
            except:
                use_existing_git = click.confirm("Existing git repository detected. Use existing repository?", default=True)
                create_github = create_repo or click.confirm("Create GitHub repository?", default=False)
        else:
            use_existing_git = False
            create_github = create_repo or click.confirm("Create GitHub repository?", default=False)

        # Git hooks installation
        install_git_hooks = click.confirm("Install git hooks for multi-agent workflow?", default=True)

        # GitHub issue templates installation
        install_issue_templates = False
        if create_github or github_remote_exists:
            install_issue_templates = click.confirm("Install GitHub issue templates (bug, feature, task, hotfix)?", default=True)

        # Claude Code GitHub App setup prompt
        if create_github or github_remote_exists:
            console.print("\n[bold blue]Claude Code Integration Setup[/bold blue]")
            console.print("For automated PR reviews and agent feedback, Claude Code needs GitHub access.")
            console.print("\n[cyan]To set up Claude Code with your GitHub repository:[/cyan]")
            console.print("  1. In Claude, run: [yellow]/install github[/yellow]")
            console.print("  2. Follow the GitHub App installation flow")
            console.print("  3. Grant access to your repositories")
            console.print("  4. Claude will then be able to review PRs automatically")
            
            setup_claude = click.confirm("\nHave you installed the Claude Code GitHub app?", default=False)
            if not setup_claude:
                console.print("\n[yellow]Tip: After init completes, run '/install github' in Claude to enable automated reviews![/yellow]")

    # Copy framework structure from package
    if not dry_run:
        # Start Phase 2: Global Framework Setup
        if progress:
            progress.start_phase("Phase 2: Global Framework Setup")

        success = _generate_project_structure(cwd, backend_heavy=backend_heavy, interactive=interactive)
        if not success:
            console.print("[red]Framework initialization failed[/red]")
            return

        if progress:
            progress.complete_step("Phase 2: Global Framework Setup", "Create ~/.multiagent/ (or detect existing)")
            progress.complete_step("Phase 2: Global Framework Setup", "Install framework templates")
            progress.complete_step("Phase 2: Global Framework Setup", "Create global registry ~/.multiagent.json")
            progress.complete_step("Phase 2: Global Framework Setup", "Backup existing customizations (if applicable)")

        console.print("[green]Core framework initialized[/green]")

        _run_documentation_bootstrap(cwd)

        # Start Phase 4: MCP Configuration
        if progress:
            progress.start_phase("Phase 4: MCP Configuration")
            # MCP configs created in _generate_project_structure
            progress.complete_step("Phase 4: MCP Configuration", "Create .mcp.json (Claude Code)")
            progress.complete_step("Phase 4: MCP Configuration", "Create .vscode/mcp.json (VS Code Copilot)")

        # Start Phase 5: Project Structure
        if progress:
            progress.start_phase("Phase 5: Project Structure")
            progress.complete_step("Phase 5: Project Structure", "Generate project directories (docs/, scripts/)")
            progress.complete_step("Phase 5: Project Structure", "Install git hooks (pre-commit, pre-push, post-commit)")
            progress.complete_step("Phase 5: Project Structure", "Create components registry")

    # Handle git repository setup FIRST
    if not dry_run and not use_existing_git:
        # Start Phase 3: Git Repository Setup
        if progress:
            progress.start_phase("Phase 3: Git Repository Setup")

        console.print("Initializing git repository...")
        try:
            subprocess.run(['git', 'init'], cwd=str(cwd), check=True)
            if progress:
                progress.complete_step("Phase 3: Git Repository Setup", "Initialize or use existing git repository")

            # Handle git ownership issues in WSL/Windows
            try:
                subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', str(cwd)],
                             capture_output=True, text=True)
            except:
                pass  # Non-critical if this fails

            if progress:
                progress.complete_step("Phase 3: Git Repository Setup", "Configure git ownership (WSL/Windows safety)")
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]Warning: Git initialization failed: {e}[/yellow]")
    elif not dry_run and use_existing_git:
        # Using existing git repository
        if progress:
            progress.start_phase("Phase 3: Git Repository Setup")
            progress.complete_step("Phase 3: Git Repository Setup", "Initialize or use existing git repository")
            progress.complete_step("Phase 3: Git Repository Setup", "Configure git ownership (WSL/Windows safety)")

    # Handle git hooks installation (after git is initialized)
    # NOTE: Git hooks now installed via _install_git_hooks_from_templates in _generate_project_structure
    # if not dry_run and install_git_hooks:
    #     _install_git_hooks(cwd)

    # Create an initial commit before creating the repo
    if not dry_run and not use_existing_git:
        try:
            # Use -A to add all files including in subdirectories
            subprocess.run(['git', 'add', '-A'], cwd=str(cwd), check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit: MultiAgent Framework setup'], cwd=str(cwd), check=True)
            console.print("[green]OK Initial commit created[/green]")
            if progress:
                progress.complete_step("Phase 3: Git Repository Setup", "Create initial commit")
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]Warning: Initial commit failed: {e}[/yellow]")
    elif not dry_run and use_existing_git:
        # No initial commit needed for existing git
        if progress:
            progress.complete_step("Phase 3: Git Repository Setup", "Create initial commit")

    # Handle GitHub repository creation
    if not dry_run:
        # Start Phase 6: GitHub Integration
        if progress:
            progress.start_phase("Phase 6: GitHub Integration")

        if create_github:
            _create_github_repo(cwd)
            if progress:
                progress.complete_step("Phase 6: GitHub Integration", "Create GitHub repository (if enabled)")
                progress.complete_step("Phase 6: GitHub Integration", "Configure origin remote (if enabled)")
        else:
            if progress:
                progress.complete_step("Phase 6: GitHub Integration", "Create GitHub repository (if enabled)")
                progress.complete_step("Phase 6: GitHub Integration", "Configure origin remote (if enabled)")

    # Handle GitHub configuration installation
    if not dry_run:
        if install_issue_templates:
            _install_github_config(cwd)
            # Note: Workflows are NOT installed during init
            # They are generated by /core:project-setup based on project type
            console.print("[dim]Note: GitHub workflows will be generated by /core:project-setup based on your project type[/dim]")
            if progress:
                progress.complete_step("Phase 6: GitHub Integration", "Install issue templates (if enabled)")
        else:
            if progress:
                progress.complete_step("Phase 6: GitHub Integration", "Install issue templates (if enabled)")

    # Component recommendations removed - users install components manually when needed
    # if not dry_run:
    #     _recommend_additional_components(cwd)

    # Component linking removed - no longer creating run-component.py
    # if not dry_run:
    #     try:
    #         from .component_linker import setup_component_links
    #         console.print("\n[bold blue]Setting up local component links...[/bold blue]")
    #         linked, skipped = setup_component_links(cwd, console)
    #         if linked:
    #             console.print("[green]Local components linked for development[/green]")
    #     except Exception as e:
    #         console.print(f"[yellow]Component linking skipped: {e}[/yellow]")

    # Auto-register project for updates
    if not dry_run:
        # Start Phase 7: Registration & Finalization
        if progress:
            progress.start_phase("Phase 7: Registration & Finalization")

        try:
            from multiagent_core.auto_updater import register_deployment
            register_deployment(cwd)
            console.print("[dim]Project registered for automatic updates[/dim]")
            if progress:
                progress.complete_step("Phase 7: Registration & Finalization", "Register project in ~/.multiagent.json")
                progress.complete_step("Phase 7: Registration & Finalization", "Update last_updated timestamp")
        except Exception:
            pass  # Silent fail if registration doesn't work

        # Save initialization log
        if progress:
            try:
                log_file = progress.save_log(cwd)
                progress.complete_step("Phase 7: Registration & Finalization", "Save initialization log")
                console.print(f"[dim]Initialization log saved to: {log_file}[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not save initialization log: {e}[/yellow]")

        # Display completion summary
        if progress:
            progress.complete_step("Phase 7: Registration & Finalization", "Display completion summary")

            # Show final summary (especially important for WSL/Windows where continuous updates are skipped)
            progress.show_final_summary()

        # Save current version for upgrade detection
        try:
            _save_current_version(__version__)
        except Exception as e:
            console.print(f"[dim]Warning: Could not save version info: {e}[/dim]")

    # Offer bashrc organization (interactive only)
    if not dry_run and interactive:
        bashrc_path = Path.home() / '.bashrc'
        if bashrc_path.exists():
            console.print("")
            console.print("=" * 70)
            console.print("[bold cyan]Bashrc Organization[/bold cyan]")
            console.print("=" * 70)
            console.print("")
            console.print("Your ~/.bashrc can be organized into a clean three-tier structure:")
            console.print("  • Clear section headers for all configurations")
            console.print("  • Three-tier API key organization (MCP / Platform / Project)")
            console.print("  • Removes duplicates while preserving functionality")
            console.print("  • Automatic backup created before changes")
            console.print("")

            response = Prompt.ask(
                "Organize ~/.bashrc now?",
                choices=["y", "n", "preview"],
                default="n"
            )

            if response == "preview":
                # Show preview
                console.print("")
                console.print("[bold]Preview Mode - Showing what would be organized:[/bold]")
                console.print("")
                try:
                    from .bashrc_organizer import BashrcOrganizer
                    organizer = BashrcOrganizer(bashrc_path)
                    backup_path, organized = organizer.organize(dry_run=True)

                    console.print(f"[dim]Backup would be created at: {backup_path}[/dim]")
                    console.print("")
                    console.print("[bold]Preview (first 30 lines):[/bold]")
                    console.print("-" * 70)
                    lines = organized.split('\n')[:30]
                    for line in lines:
                        console.print(line)
                    console.print("-" * 70)
                    console.print(f"Total lines: {len(organized.split(chr(10)))} (original: {len(open(bashrc_path).readlines())})")
                    console.print("")

                    # Ask again after preview
                    response = Prompt.ask("Apply organization?", choices=["y", "n"], default="n")
                except Exception as e:
                    console.print(f"[red]Error generating preview: {e}[/red]")
                    response = "n"

            if response == "y":
                try:
                    from .bashrc_organizer import BashrcOrganizer
                    organizer = BashrcOrganizer(bashrc_path)
                    backup_path, organized = organizer.organize(dry_run=False)

                    console.print("")
                    console.print(f"[green]✓ Backup created: {backup_path}[/green]")
                    console.print(f"[green]✓ Bashrc organized: {bashrc_path}[/green]")
                    console.print("")
                    console.print("[dim]Reload your shell with: source ~/.bashrc[/dim]")
                except Exception as e:
                    console.print(f"[red]Error organizing bashrc: {e}[/red]")
            else:
                console.print("[dim]Skipped bashrc organization. Run 'multiagent bashrc-organize' anytime.[/dim]")

            console.print("")

    console.print("[green]Multi-agent framework initialization complete![/green]")

def _install_component(component, multiagent_dir, dry_run):
    """Install a specific component with intelligent directory merging"""
    console.print(f"Installing component: {component}")

    if not dry_run:
        # Create component-specific directories
        github_dir = Path.cwd() / ".github" / "workflows" / component
        github_dir.mkdir(parents=True, exist_ok=True)

        claude_dir = Path.cwd() / ".claude" / component
        claude_dir.mkdir(parents=True, exist_ok=True)

        project_root = multiagent_dir.parent
        registry = _load_components_registry(project_root)
        if not isinstance(registry, dict):  # pragma: no cover - defensive against corrupted files
            registry = {}

        components_map = registry.setdefault("components", {})
        existing_entry = components_map.get(component)
        previous_version = existing_entry.get("version") if isinstance(existing_entry, dict) else None

        components_map[component] = {
            "version": _resolve_component_version(component, previous_version),
            "installed": True,
        }

        install_order = registry.setdefault("installation_order", [])
        if component not in install_order:
            install_order.append(component)

        _apply_framework_metadata(registry)
        _write_components_registry(project_root, registry)

    console.print(f"[green]Component {component} installed with intelligent directory merging[/green]")

@main.command()
def status():
    """Show installation status and component information"""
    cwd = Path.cwd()
    multiagent_dir = cwd / ".multiagent"

    if not multiagent_dir.exists():
        console.print("[red]Multi-agent framework not initialized in this directory[/red]")
        console.print("Run 'multiagent init' to get started")
        return

    # Read components registry
    components_file = multiagent_dir / "components.json"
    registry = _load_components_registry(cwd)

    if components_file.exists():
        updated_registry = _apply_framework_metadata(dict(registry))
        if updated_registry != registry:
            _write_components_registry(cwd, updated_registry)
        registry = updated_registry

        installed_version = _current_framework_version()
        recorded_version = registry.get("framework_version", "unknown")
        metadata_blob = registry.get("framework_version_metadata")
        if not isinstance(metadata_blob, dict) or not metadata_blob:
            metadata_blob = _load_version_metadata()

        console.print(f"Framework version (installed): [cyan]{installed_version}[/cyan]")
        if recorded_version not in {"unknown", installed_version}:
            console.print(
                f"[yellow]Project registry recorded {recorded_version}. Run `multiagent upgrade` to align if needed.[/yellow]"
            )
        elif recorded_version != "unknown":
            console.print(f"Project registry version: [cyan]{recorded_version}[/cyan]")

        if isinstance(metadata_blob, dict):
            commit = metadata_blob.get("commit")
            build_date = metadata_blob.get("build_date")
            details = []
            if commit:
                details.append(f"commit [dim]{commit}[/dim]")
            if build_date:
                details.append(f"built [dim]{build_date}[/dim]")
            if details:
                console.print("; ".join(details))

        table = Table(title="Multi-Agent Framework Status")
        table.add_column("Component", style="cyan")
        table.add_column("Version", style="magenta")
        table.add_column("Status", style="green")

        components = registry.get("components", registry)
        rows_added = False

        for component, info in components.items():
            if component in ["installation_order", "framework_version", "framework_version_metadata"]:
                continue

            if isinstance(info, dict):
                status = "[green]Installed[/green]" if info.get("installed", False) else "[red]Not installed[/red]"
                version_label = info.get("version", "unknown")
                table.add_row(component, version_label, status)
                rows_added = True
            elif isinstance(info, str):
                table.add_row(component, info, "[yellow]Legacy format[/yellow]")
                rows_added = True
            else:
                table.add_row(component, str(info), "[yellow]Unknown format[/yellow]")
                rows_added = True

        if rows_added:
            console.print(table)
        else:
            console.print("[yellow]No components recorded in registry[/yellow]")

        install_order = registry.get("installation_order", [])
        if install_order:
            console.print(f"\nInstallation order: {' -> '.join(install_order)}")
    else:
        console.print("[yellow]WARNING: No components registry found[/yellow]")
        console.print(f"Framework version (installed): [cyan]{_current_framework_version()}[/cyan]")

@main.command()
def config_show():
    """Show current configuration"""
    console.print("[bold blue]MultiAgent Core Configuration[/bold blue]\n")

    # Core settings
    console.print("[bold]Core Settings:[/bold]")
    console.print(f"Debug: {config.debug}")
    console.print(f"Log Level: {config.log_level}")
    console.print(f"Development Mode: {config.development_mode}")
    console.print(f"Interactive: {config.interactive}")

    # GitHub settings
    console.print("\n[bold]GitHub Settings:[/bold]")
    console.print(f"GitHub Token: {'[green]Set[/green]' if config.github_token else '[red]Not set[/red]'}")
    console.print(f"GitHub Username: {config.github_username or '[red]Not set[/red]'}")

    # Docker settings
    console.print("\n[bold]Docker Settings:[/bold]")
    console.print(f"Docker Host: {config.docker_host}")
    console.print(f"Force Docker: {config.force_docker}")
    console.print(f"Docker Timeout: {config.docker_timeout}s")

    # WSL/Windows settings
    console.print("\n[bold]WSL/Windows Settings:[/bold]")
    console.print(f"Auto Convert Paths: {config.wsl_auto_convert_paths}")

    # Component defaults
    console.print("\n[bold]Component Installation Defaults:[/bold]")
    console.print(f"DevOps: {config.get_bool('default_install_devops', True)}")
    console.print(f"Testing: {config.get_bool('default_install_testing', True)}")
    console.print(f"AgentSwarm: {config.get_bool('default_install_agentswarm', False)}")

    console.print(f"\n[dim]Configuration loaded from .env file and environment variables[/dim]")
    console.print(f"[dim]Copy .env.example to .env to customize settings[/dim]")

@main.command()
def version_info():
    """Show detailed version information"""
    console.print(f"[bold blue]MultiAgent Core Version Information[/bold blue]\n")

    version_data = _load_version_metadata()

    if version_data:
        console.print(f"Version: [cyan]{version_data.get('version', 'unknown')}[/cyan]")
        console.print(f"Commit: [dim]{version_data.get('commit', 'unknown')}[/dim]")
        console.print(f"Build Date: [dim]{version_data.get('build_date', 'unknown')}[/dim]")
        console.print(f"Build Type: [dim]{version_data.get('build_type', 'unknown')}[/dim]")
    else:
        console.print(f"Version: [cyan]{__version__}[/cyan]")
        console.print("[dim]No detailed version information available[/dim]")
    
    console.print(f"\nInstallation: [cyan]pipx upgrade multiagent-core[/cyan] to update")

@main.command()
def doctor():
    """Comprehensive environment and package health check"""
    console.print("[bold blue]Multi-Agent Environment Health Check[/bold blue]\n")

    # Check Python version
    import sys
    console.print(f"Python: {sys.version.split()[0]}")

    # Check installed packages and versions
    packages = ['multiagent-core', 'multiagent-agentswarm', 'multiagent-devops', 'multiagent-testing']

    table = Table(title="Package Status")
    table.add_column("Package", style="cyan")
    table.add_column("Installed", style="green")
    table.add_column("Latest", style="yellow")
    table.add_column("Status", style="bold")

    for package in packages:
        try:
            current = metadata.version(package)
            latest = _get_latest_version(package)

            if latest and current != latest:
                status = "[red]Update Available[/red]"
            else:
                status = "[green]Up to Date[/green]"

            table.add_row(package, current, latest or "Unknown", status)
        except metadata.PackageNotFoundError:
            table.add_row(package, "[red]Not Installed[/red]", "Unknown", "[red]Missing[/red]")

    console.print(table)

    # Check spec-kit installation (REQUIRED)
    console.print("\n[bold]Spec-Kit Status (REQUIRED):[/bold]")
    spec_available, spec_path = _spec_kit_available()
    if spec_available:
        location = f" (at {spec_path})" if spec_path else ""
        console.print(f"spec-kit: [green]Available[/green]{location}")
    else:
        if spec_path:
            console.print(f"[yellow]spec-kit executable located at {spec_path} but failed to run[/yellow]")
        else:
            console.print("[red]spec-kit: Not detected on PATH[/red]")
        console.print("[yellow]Install with: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git[/yellow]")

    # Check available AI CLIs
    console.print("\n[bold]AI Assistant CLI Status:[/bold]")
    ai_status = _detect_available_clis()
    for cli, status in ai_status.items():
        if status['available']:
            console.print(f"{cli}: [green]{status['version']}[/green]")
        else:
            console.print(f"{cli}: [red]Not available[/red]")

    # Check GitHub CLI
    console.print("\n[bold]GitHub CLI Status:[/bold]")
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split()[2] if len(result.stdout.split()) > 2 else "unknown"
            console.print(f"GitHub CLI: [green]{version}[/green]")
        else:
            console.print("[red]GitHub CLI: Not found[/red]")
    except FileNotFoundError:
        console.print("[red]GitHub CLI: Not installed[/red]")

    # Check framework status
    console.print("\n[bold]Framework Status:[/bold]")
    cwd = Path.cwd()
    multiagent_dir = cwd / ".multiagent"

    if multiagent_dir.exists():
        console.print("[green]Framework: Initialized[/green]")
        registry = _load_components_registry(cwd)

        if registry:
            enriched_registry = _apply_framework_metadata(dict(registry))
            if enriched_registry != registry:
                try:
                    _write_components_registry(cwd, enriched_registry)
                except OSError:
                    pass
            registry = enriched_registry

            install_order = registry.get("installation_order", [])
            components_map = registry.get("components", {})

            if install_order:
                console.print(f"Components (installation order): {', '.join(install_order)}")
            elif isinstance(components_map, dict) and components_map:
                console.print(f"Components: {', '.join(sorted(components_map.keys()))}")
            else:
                console.print("[yellow]Components: Registry present but empty[/yellow]")

            recorded_version = registry.get("framework_version", "unknown")
            if recorded_version != "unknown":
                console.print(f"Framework version recorded in registry: [cyan]{recorded_version}[/cyan]")

            metadata_blob = registry.get("framework_version_metadata")
            if isinstance(metadata_blob, dict) and metadata_blob:
                commit = metadata_blob.get("commit")
                build_date = metadata_blob.get("build_date")
                details = []
                if commit:
                    details.append(f"commit [dim]{commit}[/dim]")
                if build_date:
                    details.append(f"built [dim]{build_date}[/dim]")
                if details:
                    console.print("; ".join(details))
        else:
            console.print("[yellow]Components: No registry found[/yellow]")
    else:
        console.print("[red]Framework: Not initialized[/red]")
        console.print("Run 'multiagent init' to get started")

    # Check git hooks status
    console.print("\n[bold]Git Hook Status:[/bold]")
    git_hooks_dir = cwd / '.git' / 'hooks'

    if not git_hooks_dir.exists():
        console.print("[yellow]Not a git repository - hooks not applicable[/yellow]")
    else:
        expected_hooks = {
            'pre-push': ('Secret scanning before push', ['secret', 'security', 'MultiAgent']),
            'post-commit': ('Agent workflow guidance', ['agent', 'workflow', 'Post-commit'])
        }

        hooks_healthy = True

        for hook_name, (description, keywords) in expected_hooks.items():
            hook_path = git_hooks_dir / hook_name

            if hook_path.exists() and os.access(hook_path, os.X_OK):
                # Verify content
                try:
                    with open(hook_path, 'r') as f:
                        content = f.read()
                        has_keywords = any(keyword in content for keyword in keywords)

                        if has_keywords:
                            console.print(f"{hook_name}: [green]Active[/green] ({description})")
                        else:
                            console.print(f"{hook_name}: [yellow]Installed but may be incorrect[/yellow]")
                            hooks_healthy = False
                except Exception:
                    console.print(f"{hook_name}: [yellow]Could not verify[/yellow]")
                    hooks_healthy = False
            else:
                console.print(f"{hook_name}: [red]Missing or not executable[/red]")
                hooks_healthy = False

        if not hooks_healthy:
            console.print("[dim]Run 'multiagent init' to reinstall hooks[/dim]")

@click.group()
def feedback():
    """Commands for handling feedback."""
    pass


@feedback.command()
@click.option('--pr-number', required=True, type=int, help='The pull request number.')
@click.option('--repo-name', required=True, help='The repository name in format owner/repo.')
@click.option('--json', 'json_output', is_flag=True, help='Output feedback in JSON format.')
def monitor(pr_number, repo_name, json_output):
    """Monitor a pull request for new feedback."""
    try:
        from github import Github
        import json as json_lib

        g = Github(os.environ["GITHUB_TOKEN"])
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        comments = pr.get_issue_comments()
        
        feedback_list = []
        for comment in comments:
            if "claude" in comment.user.login.lower():
                feedback_list.append({
                    "user": comment.user.login,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat()
                })

        if json_output:
            console.print(json_lib.dumps(feedback_list, indent=2))
        else:
            console.print(f"[bold green]Monitoring PR #{pr_number} for feedback...[/bold green]")
            for feedback in feedback_list:
                console.print(Panel(feedback["body"], title=f"Feedback from @{feedback['user']}", border_style="yellow"))

    except ImportError:
        console.print("[bold red]Error: PyGithub is not installed. Please run 'pip install PyGithub'.[/bold red]")
        exit(1)
    except KeyError as e:
        console.print(f"[bold red]Environment variable error: {e}[/bold red]")
        exit(1)
    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")
        exit(1)


main.add_command(feedback)

def _detect_available_clis():
    """Detect available AI assistant CLIs using non-interactive checks."""

    def _build_search_path() -> str:
        """Return a PATH string that includes common install prefixes."""
        current = os.environ.get("PATH", "")
        paths = [p for p in current.split(os.pathsep) if p]
        seen = set(paths)

        extra_templates = [
            os.path.expanduser("~/.npm-global/bin"),
            os.path.expanduser("~/.local/bin"),
            "/usr/local/bin",
        ]

        nvm_root = Path(os.path.expanduser("~/.nvm/versions/node"))
        if nvm_root.exists():
            for version_dir in nvm_root.iterdir():
                bin_dir = version_dir / "bin"
                if bin_dir.is_dir():
                    extra_templates.append(str(bin_dir))

        for template in extra_templates:
            for candidate in glob.glob(template):
                if candidate and candidate not in seen and Path(candidate).is_dir():
                    seen.add(candidate)
                    paths.append(candidate)

        return os.pathsep.join(paths)

    def _extract_version(raw: str) -> str | None:
        tokens = raw.strip().split()
        for token in tokens:
            if any(char.isdigit() for char in token) and any(ch == '.' for ch in token):
                return token.strip("()")
        return raw.strip() or None

    def _detect(commands: list[str]) -> tuple[bool, str | None]:
        search_path = _build_search_path()
        for cmd in commands:
            exe = which(cmd, path=search_path)
            if not exe:
                continue
            try:
                result = subprocess.run(
                    [exe, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    env={**os.environ, "PATH": search_path},
                )
            except subprocess.TimeoutExpired:
                # Command exists but timed out - still treat as available
                return True, "Available"
            except FileNotFoundError:
                continue

            if result.returncode == 0:
                version = _extract_version(result.stdout or result.stderr)
                return True, version or "Available"

            # Non-zero return code but executable exists – treat as available
            return True, "Available"

        return False, None

    status = {}
    cli_checks = {
        "Gemini CLI": ["gemini"],
        "Qwen CLI": ["qwen"],
        "Codex CLI": ["codex"],
        "GitHub Copilot": ["gh"],
        "Claude Code": ["claude"],
    }

    for cli_name, commands in cli_checks.items():
        available, version = _detect(commands)
        status[cli_name] = {"available": available, "version": version}

    if status["GitHub Copilot"].get("available"):
        gh_path = which("gh", path=_build_search_path())
        if gh_path:
            try:
                result = subprocess.run(
                    [gh_path, "extension", "list"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                output = result.stdout.lower()
                if "github/gh-copilot" in output or "copilot" in output:
                    status["GitHub Copilot"] = {"available": True, "version": "Available (with Copilot)"}
                else:
                    status["GitHub Copilot"] = {"available": True, "version": "Available (no Copilot extension)"}
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                status["GitHub Copilot"] = {"available": True, "version": "Available"}

    openai_available, openai_version = _detect(["openai", "openai-cli"])
    status["OpenAI CLI"] = {"available": openai_available, "version": openai_version}

    return status

def _recommend_additional_components(project_path):
    """Simple component recommendations based on CLI availability"""
    console.print("\n[bold]Checking for additional component recommendations...[/bold]")

    # Check available CLIs
    available_clis = _detect_available_clis()
    available_count = sum(1 for cli in available_clis.values() if cli['available'])

    # Show available CLIs
    for cli, status in available_clis.items():
        if status['available']:
            console.print(f"[green]FOUND[/green] {cli}: {status['version']}")
        else:
            console.print(f"[red]MISSING[/red] {cli}: Not available")

    # Check installed components
    console.print(f"\n[bold]MultiAgent Components Status:[/bold]")
    components = ['multiagent-devops', 'multiagent-testing', 'multiagent-agentswarm']
    
    for component in components:
        try:
            version = metadata.version(component)
            console.print(f"  - [cyan]{component}[/cyan]: [green]Installed (v{version})[/green]")
        except metadata.PackageNotFoundError:
            if component == 'multiagent-devops':
                console.print(f"  - [cyan]{component}[/cyan]: [yellow]Not installed[/yellow]")
                console.print(f"    Advanced CI/CD and deployment automation")
                console.print(f"    Install: [dim]pipx install multiagent-devops[/dim]")
                console.print(f"    Initialize: [dim]{_get_python_command()} -m multiagent_devops.cli init[/dim]")
            elif component == 'multiagent-testing':
                console.print(f"  - [cyan]{component}[/cyan]: [yellow]Not installed[/yellow]")
                console.print(f"    Comprehensive test automation")
                console.print(f"    Install: [dim]pipx install multiagent-testing[/dim]")
                console.print(f"    Initialize: [dim]{_get_python_command()} -m multiagent_testing.cli init[/dim]")
            elif component == 'multiagent-agentswarm':
                console.print(f"  - [cyan]{component}[/cyan]: [yellow]Not installed[/yellow]")
                console.print(f"    Multi-agent coordination and orchestration")
                console.print(f"    Install: [dim]pipx install multiagent-agentswarm[/dim]")

    if available_count > 0:
        console.print(f"    [dim]({available_count} AI assistant CLI(s) detected for enhanced coordination)[/dim]")

    console.print("\n[green]Core framework ready! Install components as needed.[/green]")

# Component installation removed - users install components manually when needed

def _get_latest_version(package_name):
    """Get latest version of package from PyPI"""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data['info']['version']
    except Exception:
        pass
    return None

def _get_python_command():
    """Get the appropriate python command - simplified since pipx handles environment isolation"""
    return 'python'

def _check_python_environment():
    """Check Python environment - simplified since pipx handles isolation"""
    # pipx handles environment isolation automatically, so no complex checks needed
    pass

def _check_for_updates_async():
    """Spawn a non-blocking update check if allowed by configuration."""

    if config.skip_version_check or os.environ.get("CI"):
        return

    def _worker() -> None:
        try:
            checker = UpdateChecker()
            updates = checker.check()
            if not updates:
                return

            # Respect non-interactive runs
            if not config.interactive:
                return

            message_lines = [
                f"[yellow]{update.package}[/yellow]: {update.current} → {update.latest}"
                for update in updates
            ]
            message_lines.append("[dim]Run `multiagent upgrade` to apply updates.[/dim]")
            console.print(Panel("\n".join(message_lines), title="Updates available", style="yellow", expand=False))
        except Exception:
            # Never interrupt CLI flow because of update checks
            pass

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

def _convert_path_for_windows_tools(path):
    """Convert paths for Windows tools like gh CLI - handles all WSL scenarios"""
    path_str = str(path)

    # Handle different WSL path formats
    if '\\\\wsl.localhost\\' in path_str:
        # Format: \\wsl.localhost\Ubuntu\tmp\test -> C:\Users\user\AppData\Local\Temp\test
        # Extract the Linux path part
        linux_path = path_str.replace('\\\\wsl.localhost\\Ubuntu', '').replace('\\', '/')

        # Try to convert using wslpath
        try:
            result = subprocess.run(['wslpath', '-w', linux_path], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        # Fallback: if in /tmp, map to Windows temp
        if linux_path.startswith('/tmp/'):
            import tempfile
            windows_temp = tempfile.gettempdir()
            relative_path = linux_path[5:]  # Remove /tmp/
            windows_path = os.path.join(windows_temp, relative_path).replace('/', '\\')

            # Create the directory in Windows if it doesn't exist
            try:
                os.makedirs(windows_path, exist_ok=True)
            except:
                pass

            return windows_path

    elif hasattr(os, 'uname') and 'Microsoft' in os.uname().release:
        # Running directly in WSL - convert to Windows path
        try:
            result = subprocess.run(['wslpath', '-w', path_str], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

    # If all else fails, return original path
    return path_str

def _should_create_github_repo():
    """Interactive prompt to ask if user wants to create GitHub repository"""
    if not config.interactive:
        return False

    while True:
        response = input("Create GitHub repository? [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no', '']:
            return False
        else:
            console.print("Please enter 'y' for yes or 'n' for no")

def _copy_non_destructive(src, dest, console):
    """
    Recursively copy files and directories.
    Does not overwrite existing files EXCEPT for template files.
    Template files (.multiagent/templates/*.md) are always updated.
    """
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dest, item)
            _copy_non_destructive(s, d, console)
    else:
        # Check if this is a template file that should always be updated
        dest_path = Path(dest)
        relative_to_multiagent = None

        # Find if this file is under .multiagent/templates
        for parent in dest_path.parents:
            if parent.name == '.multiagent':
                relative_to_multiagent = dest_path.relative_to(parent)
                break

        # Always overwrite template files
        should_overwrite = False
        if relative_to_multiagent:
            path_str = str(relative_to_multiagent)
            # Overwrite markdown files in templates/ directory or .multiagent/README.md
            if (path_str.startswith('templates/') and path_str.endswith('.md')) or \
               path_str == 'README.md':  # Also update .multiagent/README.md
                should_overwrite = True
        
        if should_overwrite:
            shutil.copy2(src, dest)
            console.print(f"[green]  [OK] Updated: {Path(dest).relative_to(Path(dest).parent.parent)}[/green]")
        elif not os.path.exists(dest):
            shutil.copy2(src, dest)
        else:
            # File exists and shouldn't be overwritten - skip silently
            pass


def _install_git_hooks_from_templates(cwd, templates_root, console):
    """Install git hooks from .multiagent/security/hooks/ and .multiagent/agents/hooks/ to .git/hooks/"""

    # Check if we're in a git repository
    git_hooks_dir = cwd / '.git' / 'hooks'
    if not git_hooks_dir.exists():
        console.print("[yellow]WARNING:  Not a git repository - skipping git hooks installation[/yellow]")
        console.print("[dim]   Run 'git init' first to enable git hooks[/dim]")
        return

    console.print(" Installing git hooks...")

    # Use global framework
    global_multiagent = Path.home() / ".multiagent"

    # Define hooks to install from subsystems
    # Format: (subsystem_path, hook_name, description)
    hooks_to_install = [
        (('security', 'hooks'), 'pre-push', 'Secret scanning before push'),
        (('agents', 'hooks'), 'post-commit', 'Agent workflow guidance'),
    ]

    hooks_installed = 0
    hooks_failed = []

    for hook_path_parts, hook_name, description in hooks_to_install:
        try:
            # Build path to hook in global framework
            hook_src_path = global_multiagent.joinpath(*hook_path_parts, hook_name)

            if not hook_src_path.exists():
                hooks_failed.append((hook_name, f"not found at {hook_src_path}"))
                continue

            hook_dest = git_hooks_dir / hook_name

            # Copy the hook
            shutil.copy2(hook_src_path, hook_dest)

            # Make it executable
            hook_dest.chmod(0o755)

            console.print(f"  [OK] Installed {hook_name} hook ({description})")
            hooks_installed += 1

        except FileNotFoundError:
            hooks_failed.append((hook_name, "file not found"))
        except Exception as e:
            hooks_failed.append((hook_name, str(e)))

    if hooks_installed > 0:
        console.print(f" Installed {hooks_installed} git hooks successfully")
        console.print("[dim]   Git hooks will automatically run on commit/push[/dim]")

    if hooks_failed:
        console.print(f"[yellow]WARNING:  Warning: {len(hooks_failed)} hooks could not be installed:[/yellow]")
        for hook_name, reason in hooks_failed:
            console.print(f"[dim]   - {hook_name}: {reason}[/dim]")

    if hooks_installed == 0:
        console.print("[yellow]No git hooks were installed[/yellow]")
        console.print("[dim]   Hooks may need to be installed manually from .multiagent/security/hooks/ and .multiagent/agents/hooks/[/dim]")


def _verify_hook_installation(cwd, console):
    """Verify hooks are installed correctly and provide basic content validation."""

    git_hooks_dir = cwd / '.git' / 'hooks'
    if not git_hooks_dir.exists():
        return

    console.print("\nVerifying hook installation...")

    hooks_to_verify = {
        'pre-push': ['secret', 'security', 'MultiAgent'],
        'post-commit': ['agent', 'workflow', 'Post-commit']
    }

    all_verified = True

    for hook_name, expected_keywords in hooks_to_verify.items():
        hook_path = git_hooks_dir / hook_name

        if hook_path.exists() and os.access(hook_path, os.X_OK):
            # Quick content verification
            try:
                with open(hook_path, 'r') as f:
                    content = f.read()
                    has_keywords = any(keyword in content for keyword in expected_keywords)

                    if has_keywords:
                        console.print(f"  [OK] {hook_name}: Installed and verified")
                    else:
                        console.print(f"  WARNING:  {hook_name}: Installed but content may be incorrect")
                        all_verified = False
            except Exception as e:
                console.print(f"  WARNING:  {hook_name}: Could not verify content ({e})")
                all_verified = False
        else:
            console.print(f"  [FAIL] {hook_name}: Missing or not executable")
            all_verified = False

    if all_verified:
        console.print("\n All hooks verified successfully")
        console.print("[dim]   Hooks will run automatically on commit/push[/dim]")
    else:
        console.print("\n[yellow]WARNING:  Some hooks may need attention[/yellow]")
        console.print("[dim]   Run 'multiagent doctor' for detailed diagnostics[/dim]")


def _run_documentation_bootstrap(cwd: Path) -> None:
    """Ensure documentation scaffolding exists after init."""
    doc_script = cwd / '.multiagent' / 'documentation' / 'scripts' / 'create-structure.sh'
    if not doc_script.exists():
        return

    console.print('[bold blue]Bootstrapping documentation scaffolding...[/bold blue]')
    try:
        subprocess.run([str(doc_script)], cwd=str(cwd), check=True)
    except subprocess.CalledProcessError as exc:
        console.print(
            f"[yellow]Warning: Documentation bootstrap failed ({exc.returncode}). "
            "Run the script manually if needed.[/yellow]"
        )
    else:
        console.print('[green]Documentation scaffolding ready[/green]')


def _create_minimal_profile(console, interactive=True):
    """Create minimal user profile for agent personalization."""
    from datetime import datetime

    profile_dir = Path.home() / ".multiagent" / "profile"
    profile_json = profile_dir / "user.json"

    # Skip if profile already exists
    if profile_json.exists():
        console.print("[dim]User profile exists[/dim]")
        return

    # In non-interactive mode, use defaults
    if not interactive:
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_data = {
            "role": "Developer",
            "solo_operation": False,
            "created_at": datetime.now().isoformat(),
            "preferences": {
                "suggest_team_tools": True,
                "suggest_automation": False
            }
        }
        with open(profile_json, 'w') as f:
            json.dump(profile_data, f, indent=2)
        console.print("[dim]Created default profile[/dim]")
        return

    console.print("\n[bold cyan]User Profile Setup[/bold cyan]")
    console.print("[dim]This helps agents make appropriate recommendations[/dim]\n")

    # Simple questionnaire
    role = click.prompt(
        "Your role?",
        type=click.Choice(['Founder', 'Developer', 'Team Lead', 'Other'], case_sensitive=False),
        default='Developer'
    )

    solo = click.confirm("Solo developer? (no team)", default=False)

    # Create profile
    profile_dir.mkdir(parents=True, exist_ok=True)

    profile_data = {
        "role": role,
        "solo_operation": solo,
        "created_at": datetime.now().isoformat(),
        "preferences": {
            "suggest_team_tools": not solo,
            "suggest_automation": solo
        }
    }

    with open(profile_json, 'w') as f:
        json.dump(profile_data, f, indent=2)

    console.print(f"[green]OK Profile created[/green]")


def _deploy_agent_instructions(templates_root, console):
    """Deploy agent instruction files to their respective home directories.

    Detects which AI agent directories exist (~/.claude/, ~/.qwen/, etc.) and
    deploys template instruction files only if they don't already exist.
    """
    import importlib_resources

    # Map of agent directories to their instruction file names
    agent_configs = {
        '.claude': 'CLAUDE.md',
        '.qwen': 'QWEN.md',
        '.gemini': 'GEMINI.md',
        '.codex': 'CODEX.md',
        '.copilot': 'COPILOT.md'
    }

    deployed_count = 0
    skipped_count = 0

    for agent_dir, config_file in agent_configs.items():
        agent_path = Path.home() / agent_dir

        # Check if agent directory exists
        if not agent_path.exists():
            continue

        target_file = agent_path / config_file

        # Skip if instruction file already exists
        if target_file.exists():
            skipped_count += 1
            continue

        # Deploy template
        try:
            template_path = templates_root.joinpath('agent-configs', config_file)
            with importlib_resources.as_file(template_path) as template_src:
                if template_src.exists():
                    shutil.copy(template_src, target_file)
                    console.print(f"[green]Deployed {config_file} to {agent_dir}/[/green]")
                    deployed_count += 1
        except Exception as e:
            console.print(f"[yellow]Warning: Could not deploy {config_file}: {e}[/yellow]")

    if deployed_count > 0:
        console.print(f"[green]OK Deployed {deployed_count} agent instruction file(s)[/green]")
    if skipped_count > 0:
        console.print(f"[dim]Skipped {skipped_count} existing agent instruction file(s)[/dim]")


def _register_project(cwd, console):
    """Register project in ~/.multiagent.json (following Claude's pattern)."""
    registry_file = Path.home() / ".multiagent.json"

    # Load existing registry (or migrate from old location)
    old_registry_file = Path.home() / ".multiagent" / "deployed-projects-registry.json"

    if registry_file.exists():
        # Load from new location
        try:
            with open(registry_file, 'r') as f:
                registry = json.load(f)
        except (json.JSONDecodeError, OSError):
            registry = {"version": "1.0.0", "framework_version": __version__, "projects": [], "settings": {"auto_update": True}}
    elif old_registry_file.exists():
        # Migrate from old location
        try:
            with open(old_registry_file, 'r') as f:
                data = json.load(f)
            # Handle old format (just a list) or dict format
            if isinstance(data, list):
                registry = {"version": "1.0.0", "framework_version": __version__, "projects": data, "settings": {"auto_update": True}}
            elif isinstance(data, dict):
                registry = data
                if "framework_version" not in registry:
                    registry["framework_version"] = __version__
                if "settings" not in registry:
                    registry["settings"] = {"auto_update": True}
            else:
                registry = {"version": "1.0.0", "framework_version": __version__, "projects": [], "settings": {"auto_update": True}}
            console.print(f"[dim]Migrated registry from {old_registry_file} to {registry_file}[/dim]")
        except (json.JSONDecodeError, OSError):
            registry = {"version": "1.0.0", "framework_version": __version__, "projects": [], "settings": {"auto_update": True}}
    else:
        # Create new registry
        registry = {"version": "1.0.0", "framework_version": __version__, "projects": [], "settings": {"auto_update": True}}

    # Check if project already registered
    project_path = str(cwd.resolve())
    project_name = cwd.name

    for project in registry.get("projects", []):
        if project.get("path") == project_path:
            console.print(f"[dim]OK Project already registered: {project_name}[/dim]")
            return

    # Register new project
    from datetime import datetime
    registry["projects"].append({
        "name": project_name,
        "path": project_path,
        "initialized_at": datetime.utcnow().isoformat() + "Z",
        "mcp_servers": [],
        "last_updated": datetime.utcnow().isoformat() + "Z"
    })

    # Update framework version
    registry["framework_version"] = __version__

    # Save registry to home root (like .claude.json)
    try:
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
        console.print(f"[green][OK] Registered project: {project_name}[/green]")
        console.print(f"[dim]   Registry: {registry_file}[/dim]")
    except OSError as e:
        console.print(f"[yellow]Warning: Could not update registry: {e}[/yellow]")


def _generate_project_structure(cwd, backend_heavy=False, interactive=True):
    """Copy framework directories from package to target directory.

    This function implements location-independent initialization:

    1. Uses importlib to find installed package (works from ANY directory)
    2. Copies templates from multiagent_core/templates/ to target
    3. Runs interactive menu for project configuration
    4. Registers project for automatic template updates

    Location Independence:
        Uses importlib_resources.files() instead of relative paths,
        so 'multiagent init' works from any directory:
        - /tmp/test-project
        - /home/user/my-app
        - Anywhere else

    Package-Based Architecture:
        Post-init operations (like /project-setup) run sync_project.py
        FROM THE INSTALLED PACKAGE, not from copied files. This ensures:
        - Latest sync logic always used
        - No need to copy sync scripts to projects
        - Users never run sync manually

    Auto-Update Registration:
        Project path stored in ~/.multiagent-core-deployments.json
        Next 'python -m build' automatically syncs templates to ALL
        registered projects.

    Args:
        cwd (Path): Target directory (can be anywhere)
        backend_heavy (bool): Optimize for backend development
        interactive (bool): Whether to prompt for user input

    Returns:
        None: Modifies filesystem directly, outputs status to console

    See Also:
        - auto_updater.register_deployment() - Registers for updates
        - build-system/README.md - Build system docs
        - _template_sync.py - Build-time template sync
    """
    console.print("[bold cyan]Setting up MultiAgent framework...[/bold cyan]")

    templates_root = importlib_resources.files("multiagent_core") / "templates"

    # Create user profile if doesn't exist
    _create_minimal_profile(console, interactive=interactive)

    # Deploy agent instruction files to agent directories
    console.print(" Deploying agent instruction files...")
    _deploy_agent_instructions(templates_root, console)

    # Register this project
    _register_project(cwd, console)

    # ARCHITECTURE: Everything lives in ~/.multiagent/ (global)
    # Slash commands read from global, deliver OUTPUT to projects
    # No template directories (docs/, scripts/) copied to projects

    # Copy .gitignore to project root
    console.print(" Setting up .gitignore...")
    try:
        resource = templates_root.joinpath('.gitignore')
        with importlib_resources.as_file(resource) as gitignore_src_path:
            gitignore_src_path = Path(gitignore_src_path)
            dest_gitignore_path = cwd / '.gitignore'
            if not dest_gitignore_path.exists():
                shutil.copy(gitignore_src_path, dest_gitignore_path)
                console.print("[OK] Copied comprehensive .gitignore to project root")
            else:
                console.print("[dim]Skipped existing .gitignore (keeping user's version)[/dim]")
    except FileNotFoundError:
        console.print("[yellow]Warning: .gitignore template not found in package resources[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not copy .gitignore: {e}[/yellow]")

    # Copy .env.template for project-specific API keys
    console.print("Setting up .env.template...")
    try:
        resource = templates_root.joinpath('.env.template')
        with importlib_resources.as_file(resource) as env_template_src:
            env_template_src = Path(env_template_src)
            dest_env_template = cwd / '.env.template'
            if not dest_env_template.exists():
                shutil.copy(env_template_src, dest_env_template)
                console.print("[green]Created .env.template (copy to .env and fill in your keys)[/green]")
            else:
                console.print("[dim]Skipped existing .env.template[/dim]")
    except FileNotFoundError:
        console.print("[yellow]Warning: .env.template not found in package resources[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not copy .env.template: {e}[/yellow]")

    # Copy .gitmessage for commit message template
    console.print("Setting up .gitmessage...")
    try:
        resource = templates_root.joinpath('.gitmessage')
        with importlib_resources.as_file(resource) as gitmessage_src:
            gitmessage_src = Path(gitmessage_src)
            dest_gitmessage = cwd / '.gitmessage'
            if not dest_gitmessage.exists():
                shutil.copy(gitmessage_src, dest_gitmessage)
                console.print("[green]Created .gitmessage (conventional commit template)[/green]")
            else:
                console.print("[dim]Skipped existing .gitmessage[/dim]")
    except FileNotFoundError:
        console.print("[yellow]Warning: .gitmessage template not found in package resources[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not copy .gitmessage: {e}[/yellow]")

    # Handle .mcp.json for Claude Code
    console.print(" Setting up .mcp.json (Claude Code MCP servers)...")
    try:
        dest_claude_mcp_path = cwd / '.mcp.json'
        if not dest_claude_mcp_path.exists():
            with open(dest_claude_mcp_path, 'w', encoding='utf-8') as f:
                json.dump({"mcpServers": {}}, f, indent=2)
            console.print("[OK] Created empty .mcp.json (for Claude Code MCP servers)")
        else:
            console.print("[dim]Skipped existing .mcp.json[/dim]")
    except Exception as e:
        console.print(f"[red]Error creating .mcp.json: {e}[/red]")

    # Handle .vscode/mcp.json for VS Code Copilot
    console.print(" Setting up .vscode/mcp.json (VS Code Copilot MCP servers)...")
    try:
        resource = templates_root.joinpath('.vscode', 'mcp.json')
        with importlib_resources.as_file(resource) as mcp_src_path:
            mcp_src_path = Path(mcp_src_path)
            dest_vscode_dir = cwd / '.vscode'
            dest_mcp_path = dest_vscode_dir / 'mcp.json'
            dest_vscode_dir.mkdir(exist_ok=True)

            if not dest_mcp_path.exists():
                shutil.copy(mcp_src_path, dest_mcp_path)
                console.print("[OK] Copied .vscode/mcp.json (empty, for VS Code Copilot)")
            else:
                console.print("[dim]Skipped existing .vscode/mcp.json[/dim]")
    except FileNotFoundError:
        console.print("[yellow]Warning: .vscode/mcp.json template not found, creating empty one...[/yellow]")
        try:
            dest_vscode_dir = cwd / '.vscode'
            dest_mcp_path = dest_vscode_dir / 'mcp.json'
            dest_vscode_dir.mkdir(exist_ok=True)
            if not dest_mcp_path.exists():
                with open(dest_mcp_path, 'w', encoding='utf-8') as f:
                    json.dump({"servers": {}}, f, indent=2)
                console.print("[OK] Created empty .vscode/mcp.json")
        except Exception as e:
            console.print(f"[red]Error creating .vscode/mcp.json: {e}[/red]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not copy .vscode/mcp.json: {e}[/yellow]")

    # Copy .api-keys-inventory.example.md to project root
    console.print(" Setting up .api-keys-inventory.example.md...")
    try:
        resource = templates_root.joinpath('.api-keys-inventory.example.md')
        with importlib_resources.as_file(resource) as inventory_src_path:
            inventory_src_path = Path(inventory_src_path)
            dest_inventory_path = cwd / '.api-keys-inventory.example.md'
            if not dest_inventory_path.exists():
                shutil.copy(inventory_src_path, dest_inventory_path)
                console.print("[OK] Copied .api-keys-inventory.example.md (global tracking template)")
            else:
                console.print("[dim]Skipped existing .api-keys-inventory.example.md[/dim]")
    except FileNotFoundError:
        console.print("[yellow]Warning: .api-keys-inventory.example.md template not found in package resources[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not copy .api-keys-inventory.example.md: {e}[/yellow]")

    # Install git hooks from templates (NEW!)
    _install_git_hooks_from_templates(cwd, templates_root, console)

    # Verify hooks are installed correctly
    _verify_hook_installation(cwd, console)

    console.print(" MultiAgent framework setup complete!")

    # Display key management guidance
    console.print("\n" + "="*70)
    console.print("[bold cyan]API Key Organization Guide[/bold cyan]")
    console.print("="*70)
    console.print("""
[bold]Three-Tier Key Structure:[/bold]

[cyan]1. Global MCP Keys[/cyan] (in ~/.bashrc)
   - MCP_OPENAI_API_KEY       - For Claude Code OpenAI MCP
   - MCP_ANTHROPIC_API_KEY    - For Claude Code Anthropic MCP
   - MCP_GITHUB_TOKEN         - For Claude Code GitHub MCP
   - MCP_GOOGLE_AI_API_KEY    - For Claude Code Gemini MCP
   [dim]These are shared across ALL projects using MCP servers[/dim]

[cyan]2. Project Keys[/cyan] (in .env - THIS PROJECT ONLY)
   - OPENAI_API_KEY           - For your app's runtime features
   - DATABASE_URL             - Database connection
   - STRIPE_SECRET_KEY        - Payment processing
   [dim]Copy .env.template to .env and add project-specific keys[/dim]

[cyan]3. Platform Keys[/cyan] (set via platform CLI)
   - vercel env add           - Vercel deployment
   - railway vars set         - Railway deployment
   - render env set           - Render deployment
   [dim]These are managed by your deployment platform[/dim]

[yellow]Next Steps:[/yellow]
  1. Copy .env.template to .env
  2. Add project-specific keys to .env (gitignored)
  3. For MCP servers: Add MCP_* keys to ~/.bashrc once
  4. Run /mcp:setup to configure MCP servers for this project
""")
    console.print("="*70 + "\n")

    return True


# Legacy feedback system - removed (no longer used)
# @main.group(name="agent-feedback")
# def agent_feedback() -> None:
#     """Interact with queued feedback routed to local agents."""
#
#
# @agent_feedback.command("pull")
# @click.option("--agent-id", required=True, help="Agent handle that should receive the feedback.")
# @click.option(
#     "--max-items",
#     default=1,
#     show_default=True,
#     type=int,
#     help="Maximum number of feedback messages to consume in one pull.",
# )
# @click.option(
#     "--json-output",
#     "as_json",
#     is_flag=True,
#     help="Return the feedback bundle as JSON for downstream automation.",
# )
# def agent_feedback_pull(agent_id: str, max_items: int, as_json: bool) -> None:
#     """Fetch pending feedback for a given agent from the routing queue."""
#
#     store = feedback_runtime.get_store()
#     try:
#         records = store.pop_feedback(agent_id, max_items=max_items)
#     except ValueError as exc:  # pragma: no cover - defensive guard
#         raise click.BadParameter(str(exc), param_hint="--max-items") from exc
#
#     if not records:
#         click.echo(f"No pending feedback for agent {agent_id}")
#         return
#
#     if as_json:
#         serialised = [
#             {
#                 "record_id": record.id,
#                 "received_at": record.received_at.isoformat(),
#                 **record.payload.to_dict(),
#             }
#             for record in records
#         ]
#         click.echo(json.dumps(serialised, indent=2))
#         return
#
#     for record in records:
#         console.print(f"[bold cyan]Feedback {record.id}[/bold cyan] → {record.payload.agent_id}")
#         console.print(f"[dim]Pull Request:[/dim] {record.payload.pull_request_id}")
#         console.print(f"[dim]Comment:[/dim] {record.payload.comment_id}")
#         console.print(record.payload.feedback_content)
#         console.print("")
#
#     remaining = store.pending_count(agent_id)
#     console.print(
#         f"[green]Delivered {len(records)} item(s). Remaining in queue: {remaining}[/green]"
#     )


def _create_github_repo(cwd):
    """Create a GitHub repository using the gh CLI."""
    repo_name = cwd.name
    console.print(f"Creating GitHub repository: {repo_name}")

    try:
        # Ensure we are in the correct directory
        os.chdir(cwd)

        # Command to create a private repo from the current directory
        command = [
            'gh', 'repo', 'create', repo_name,
            '--private',
            '--source', '.',
            '--push'
        ]

        # The GITHUB_TOKEN is read automatically by 'gh' from env variables
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(cwd)
        )
        console.print(f"[green]Successfully created and pushed to GitHub repository: {repo_name}[/green]")
        console.print(result.stdout)

        # Verify the push was complete
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=str(cwd)
        )
        if status_result.stdout.strip():
            console.print("[yellow]Warning: Some files may not have been pushed to GitHub[/yellow]")
            console.print("[yellow]Uncommitted changes detected. Run 'git status' to see details.[/yellow]")
        else:
            console.print("[green]OK All files successfully pushed to GitHub[/green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to create GitHub repository: {e}[/red]")
        console.print(f"[red]stdout: {e.stdout}[/red]")
        console.print(f"[red]stderr: {e.stderr}[/red]")
    except FileNotFoundError:
        console.print("[red]Failed to create GitHub repository: 'gh' command not found.[/red]")
        console.print("[red]Please ensure the GitHub CLI is installed and in your PATH.[/red]")


def _install_github_config(cwd):
    """Install GitHub configuration from ~/.multiagent/core/templates/github-config/"""
    console.print("\n[bold blue]Installing GitHub configuration...[/bold blue]")

    try:
        global_multiagent = Path.home() / ".multiagent"
        github_config_src = global_multiagent / "core" / "templates" / "github-config"

        # 1. Install issue templates
        issue_template_src = github_config_src / "ISSUE_TEMPLATE"
        issue_template_dst = cwd / ".github" / "ISSUE_TEMPLATE"
        issue_template_dst.mkdir(parents=True, exist_ok=True)

        if issue_template_src.is_dir():
            for template_file in issue_template_src.iterdir():
                if template_file.is_file():
                    dst_file = issue_template_dst / template_file.name
                    shutil.copy2(template_file, dst_file)
                    console.print(f"  OK {template_file.name}")
            console.print("[green]OK GitHub issue templates installed[/green]")
        else:
            console.print(f"[yellow]Warning: Issue templates not found at {issue_template_src}[/yellow]")

        # 2. Install copilot-instructions.md
        copilot_src = github_config_src / "copilot-instructions.md"
        copilot_dst = cwd / ".github" / "copilot-instructions.md"

        if copilot_src.exists():
            if copilot_dst.exists():
                # Append to existing
                with open(copilot_dst, 'a', encoding='utf-8') as f:
                    f.write('\n\n# MultiAgent Framework Instructions\n\n')
                    with open(copilot_src, 'r', encoding='utf-8') as src_f:
                        f.write(src_f.read())
                console.print("  OK copilot-instructions.md (appended)")
            else:
                shutil.copy2(copilot_src, copilot_dst)
                console.print("  OK copilot-instructions.md (created)")
        else:
            console.print(f"[yellow]Warning: copilot-instructions.md not found at {copilot_src}[/yellow]")

    except Exception as e:
        console.print(f"[yellow]Warning: Failed to install GitHub config: {e}[/yellow]")


def _should_install_git_hooks():
    """Interactive prompt to ask if user wants to install git hooks"""
    if not config.interactive:
        return True  # Default to installing git hooks in non-interactive mode

    while True:
        response = input("Install git hooks for multi-agent workflow? [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no', '']:
            return False
        else:
            console.print("Please enter 'y' for yes or 'n' for no")

def _install_git_hooks(project_path):
    """Install git hooks for multi-agent development workflow using tracked directory approach"""
    console.print("Installing git hooks...")

    try:
        # Check if this is a git repository
        if not (project_path / '.git').exists():
            console.print("[yellow]No .git directory found - not a git repository?[/yellow]")
            return False

        # Create scripts/hooks directory for tracked hooks
        scripts_hooks_dir = project_path / 'scripts' / 'hooks'
        scripts_hooks_dir.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[blue]Creating shared Git hooks in: {scripts_hooks_dir}[/blue]")

        # Generate pre-push hook for professional commit strategy
        pre_push_hook = scripts_hooks_dir / 'pre-push'
        pre_push_content = '''#!/bin/bash
# MultiAgent framework pre-push hook
# Provides guidance for professional commit accumulation

# Only guide on main branch
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [[ "$current_branch" != "main" ]]; then
    exit 0
fi

# Count commits to push
commits_to_push=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")

# Only guide if 1 or fewer commits
if [[ "$commits_to_push" -le 1 ]]; then
    echo "Professional Commit Strategy Guidance"
    echo "Commits to push: $commits_to_push"
    echo "For richer release notes, consider accumulating 3-6 commits"
    echo "Rich Release Pattern:"
    echo "   git commit -m 'fix(component): specific issue'"
    echo "   git commit -m 'feat(feature): new capability'"
    echo "   git commit -m 'docs: update guide'"
    echo "   git push  # <- Rich release (3+ bullets)"
    echo ""
    echo "Continue anyway? Proceeding in 3 seconds..."
    echo "   Press Ctrl+C to cancel, or wait to continue"

    # 3 second countdown
    for i in {3..1}; do
        echo -n "$i "
        sleep 1
    done
    echo ""
fi

exit 0
'''

        with open(pre_push_hook, 'w', encoding='utf-8', newline='\n') as f:
            f.write(pre_push_content)
        pre_push_hook.chmod(0o755)

        # Create post-commit hook for auto-build
        post_commit_hook = scripts_hooks_dir / "post-commit"
        post_commit_content = """#!/bin/bash

# Auto-build and update based on commit type
# This hook runs AFTER a commit is made

# Get the commit message
COMMIT_MSG=$(git log -1 --pretty=%B)

# Check if this is a meaningful commit that needs building
should_build=false

# ONLY skip build for these specific types that never need updates
if echo "$COMMIT_MSG" | grep -qE "^(test|style|wip|temp)(\\(.*\\))?:"; then
    # These are the ONLY commits we skip
    should_build=false
    echo "[AUTO-BUILD] Skipping build for test/style/wip/temp commit"
elif echo "$COMMIT_MSG" | grep -qE "^\\[skip[\\- ]ci\\]|\\[ci[\\- ]skip\\]"; then
    # Also skip if commit message has [skip ci] or [ci skip]
    should_build=false
    echo "[AUTO-BUILD] Skipping build due to [skip ci] flag"
else
    # BUILD for EVERYTHING ELSE: feat, fix, docs, chore, build, ci, refactor, perf, etc.
    should_build=true
    echo "[AUTO-BUILD] Detected meaningful commit - triggering build..."
fi

if [ "$should_build" = true ]; then
    # Sync templates before building
    if [ -f "scripts/sync-templates.sh" ]; then
        bash scripts/sync-templates.sh
    fi

    echo "[AUTO-BUILD] Running python -m build to update all projects..."

    # Run the build
    python3 -m build
    
    if [ $? -eq 0 ]; then
        echo "[AUTO-BUILD] Build completed successfully!"
        echo "[AUTO-BUILD] All registered projects have been updated"
        
        # Auto-reinstall the local multiagent command
        echo "[AUTO-BUILD] Updating local multiagent command..."
        WHEEL_FILE=$(ls -t dist/multiagent_core-*.whl 2>/dev/null | head -1)
        
        if [ -n "$WHEEL_FILE" ]; then
            # Check if pipx is available
            if command -v pipx >/dev/null 2>&1; then
                # Use the current repo for reinstall (editable mode)
                pipx install -e . --force >/dev/null 2>&1
                if [ $? -eq 0 ]; then
                    echo "[AUTO-BUILD] Local multiagent command updated successfully!"
                else
                    echo "[AUTO-BUILD] Warning: Could not update local command (pipx reinstall failed)"
                fi
            else
                echo "[AUTO-BUILD] Warning: pipx not found - skipping local command update"
            fi
        else
            echo "[AUTO-BUILD] Warning: No wheel file found - skipping local command update"
        fi
    else
        echo "[AUTO-BUILD] Build failed - please run manually to debug"
        exit 0  # Don't fail the commit
    fi
else
    echo "[AUTO-BUILD] Skipping build for commit type: $(echo "$COMMIT_MSG" | head -1)"
fi
"""

        with open(post_commit_hook, 'w', encoding='utf-8', newline='\n') as f:
            f.write(post_commit_content)
        post_commit_hook.chmod(0o755)

        # Configure Git to use the tracked hooks directory
        console.print("[blue]Configuring Git to use project hooks directory...[/blue]")
        try:
            subprocess.run([
                'git', 'config', 'core.hooksPath', './scripts/hooks'
            ], cwd=str(project_path), check=True, capture_output=True)
            console.print("[green]Git configured to use ./scripts/hooks[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]Warning: Could not configure hooks path: {e}[/yellow]")
            console.print("[dim]You can manually run: git config core.hooksPath ./scripts/hooks[/dim]")

        console.print("[green]Git hooks installed successfully![/green]")
        console.print("[dim]- Hooks location: scripts/hooks/ (tracked by Git)[/dim]")
        console.print("[dim]- pre-push: Professional commit strategy guidance[/dim]")
        console.print("[dim]- post-commit: Auto-build and template sync[/dim]")
        console.print("[dim]- Shared across all team members automatically[/dim]")
        return True

    except Exception as e:
        console.print(f"[red]Failed to install git hooks: {e}[/red]")
        return False



# ========================================
# Memory System Commands
# ========================================
# Memory commands removed - now available as /memory:* slash commands
# in the multiagent-memory marketplace plugin
# ========================================


# ========================================
# Bashrc Organization Command
# ========================================

@main.command()
@click.option('--dry-run', is_flag=True, help='Show what would be changed without modifying bashrc')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def bashrc_organize(dry_run, force):
    """Organize ~/.bashrc into clean three-tier structure.

    Safely reorganizes your ~/.bashrc file by:
    - Creating automatic timestamped backup
    - Organizing into clear sections with headers
    - Three-tier API key structure (MCP / Platform / Project)
    - Removing duplicates
    - Preserving all custom functions and aliases

    The organized bashrc will have these sections:
    1. Shell Configuration (history, options)
    2. Prompt Configuration
    3. Colors & Aliases
    4. Safe Delete (trash-cli aliases)
    5. Node & NPM Configuration
    6. Development Tools
    7. AI Agent Tools
    8. Project Shortcuts
    9. MCP Setup
    10. WSL Helpers
    11. Screenshot Helpers
    12. PATH Configuration
    13. API Keys (Three Tiers)
    """
    from .bashrc_organizer import BashrcOrganizer

    bashrc_path = Path.home() / '.bashrc'

    if not bashrc_path.exists():
        console.print(f"[red]Error: {bashrc_path} not found[/red]")
        return

    console.print("[bold cyan]Bashrc Organization Tool[/bold cyan]")
    console.print("=" * 70)
    console.print(f"Target: {bashrc_path}")
    console.print("")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
        console.print("")

        organizer = BashrcOrganizer(bashrc_path)
        backup_path, organized = organizer.organize(dry_run=True)

        console.print(f"[dim]Backup would be created at: {backup_path}[/dim]")
        console.print("")
        console.print("[bold]Organized content preview (first 50 lines):[/bold]")
        console.print("=" * 70)
        lines = organized.split('\n')[:50]
        for line in lines:
            console.print(line)
        console.print("=" * 70)
        console.print(f"Total lines: {len(organized.split(chr(10)))}")
        console.print(f"Original lines: {len(open(bashrc_path).readlines())}")
        console.print("")
        console.print("[yellow]Run without --dry-run to apply changes[/yellow]")
        return

    # Show warning
    console.print("[yellow]This will reorganize your ~/.bashrc file.[/yellow]")
    console.print("[yellow]A backup will be created automatically.[/yellow]")
    console.print("")

    if not force:
        response = Prompt.ask("Continue?", choices=["y", "n"], default="n")
        if response.lower() != 'y':
            console.print("[dim]Cancelled.[/dim]")
            return

    # Perform organization
    try:
        organizer = BashrcOrganizer(bashrc_path)
        backup_path, organized = organizer.organize(dry_run=False)

        console.print("")
        console.print(f"[green]✓ Backup created: {backup_path}[/green]")
        console.print(f"[green]✓ Bashrc organized: {bashrc_path}[/green]")
        console.print("")
        console.print("[bold]Next steps:[/bold]")
        console.print("1. Review the organized bashrc:")
        console.print(f"   cat {bashrc_path}")
        console.print("")
        console.print("2. Reload your shell:")
        console.print("   source ~/.bashrc")
        console.print("")
        console.print("[dim]To restore from backup:[/dim]")
        console.print(f"[dim]  cp {backup_path} {bashrc_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Error organizing bashrc: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


if __name__ == "__main__":
    main()
