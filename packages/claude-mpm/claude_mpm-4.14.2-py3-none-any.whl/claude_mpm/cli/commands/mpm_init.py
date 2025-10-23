"""
MPM-Init Command - Initialize projects for optimal Claude Code and Claude MPM success.

This command delegates to the Agentic Coder Optimizer agent to establish clear,
single-path project standards for documentation, tooling, and workflows.

Enhanced with AST inspection capabilities for generating comprehensive developer
documentation with code structure analysis.
"""

import contextlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from claude_mpm.core.logging_utils import get_logger

# Import new services
from claude_mpm.services.project.archive_manager import ArchiveManager
from claude_mpm.services.project.documentation_manager import DocumentationManager
from claude_mpm.services.project.enhanced_analyzer import EnhancedProjectAnalyzer
from claude_mpm.services.project.project_organizer import ProjectOrganizer
from claude_mpm.utils.display_helper import DisplayHelper

logger = get_logger(__name__)
console = Console()


class MPMInitCommand:
    """Initialize projects for optimal Claude Code and Claude MPM usage."""

    def __init__(self, project_path: Optional[Path] = None):
        """Initialize the MPM-Init command."""
        self.project_path = project_path or Path.cwd()
        self.claude_mpm_script = self._find_claude_mpm_script()

        # Initialize service components
        self.doc_manager = DocumentationManager(self.project_path)
        self.organizer = ProjectOrganizer(self.project_path)
        self.archive_manager = ArchiveManager(self.project_path)
        self.analyzer = EnhancedProjectAnalyzer(self.project_path)
        self.display = DisplayHelper(console)

    def initialize_project(
        self,
        project_type: Optional[str] = None,
        framework: Optional[str] = None,
        force: bool = False,
        verbose: bool = False,
        ast_analysis: bool = True,
        update_mode: bool = False,
        review_only: bool = False,
        organize_files: bool = False,
        preserve_custom: bool = True,
        skip_archive: bool = False,
        dry_run: bool = False,
        quick_update: bool = False,
        catchup: bool = False,
        non_interactive: bool = False,
        days: int = 30,
        export: Optional[str] = None,
    ) -> Dict:
        """
        Initialize project with Agentic Coder Optimizer standards.

        Args:
            project_type: Type of project (web, api, cli, library, etc.)
            framework: Specific framework if applicable
            force: Force initialization even if project already configured
            verbose: Show detailed output
            ast_analysis: Enable AST analysis for enhanced documentation
            update_mode: Update existing CLAUDE.md instead of recreating
            review_only: Review project state without making changes
            organize_files: Organize misplaced files into proper directories
            preserve_custom: Preserve custom sections when updating
            skip_archive: Skip archiving existing files
            dry_run: Show what would be done without making changes
            quick_update: Perform lightweight update based on recent git activity
            catchup: Show recent commit history from all branches for PM context
            non_interactive: Non-interactive mode - display report only without prompting
            days: Number of days for git history analysis (7, 14, 30, 60, or 90)
            export: Export report to file (path or "auto" for default location)

        Returns:
            Dict containing initialization results
        """
        try:
            # Determine initialization mode
            claude_md = self.project_path / "CLAUDE.md"
            has_existing = claude_md.exists()

            if review_only:
                return self._run_review_mode()

            if catchup:
                data = self._catchup()
                self._display_catchup(data)
                return {"status": "success", "mode": "catchup", "catchup_data": data}

            if quick_update:
                return self._run_quick_update_mode(
                    days=days,
                    non_interactive=non_interactive,
                    export=export,
                )

            if has_existing and not force and not update_mode:
                # Auto-select update mode if organize_files or dry_run is specified
                if organize_files or dry_run:
                    update_mode = True
                    console.print(
                        "[cyan]Auto-selecting update mode for organization tasks.[/cyan]\n"
                    )
                else:
                    # Offer update mode
                    console.print(
                        "[yellow]⚠️  Project already has CLAUDE.md file.[/yellow]\n"
                    )

                    # Show current documentation analysis
                    doc_analysis = self.doc_manager.analyze_existing_content()
                    self._display_documentation_status(doc_analysis)

                    # Ask user what to do
                    action = self._prompt_update_action()

                    if action == "update":
                        update_mode = True
                    elif action == "recreate":
                        force = True
                    elif action == "review":
                        return self._run_review_mode()
                    else:
                        return {
                            "status": "cancelled",
                            "message": "Initialization cancelled",
                        }

            # Handle dry-run mode
            if dry_run:
                return self._run_dry_run_mode(organize_files, has_existing)

            # Run pre-initialization checks
            if not review_only:
                pre_check_result = self._run_pre_initialization_checks(
                    organize_files, skip_archive, has_existing
                )
                if pre_check_result.get("status") == "error":
                    return pre_check_result

            # Build the delegation prompt
            if update_mode:
                prompt = self._build_update_prompt(
                    project_type, framework, ast_analysis, preserve_custom
                )
            else:
                prompt = self._build_initialization_prompt(
                    project_type, framework, ast_analysis
                )

            # Show appropriate plan based on mode
            if update_mode:
                self._show_update_plan(ast_analysis, preserve_custom)
            else:
                self._show_initialization_plan(ast_analysis)

            # Execute via claude-mpm run command
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task_desc = (
                    "[cyan]Updating documentation..."
                    if update_mode
                    else "[cyan]Delegating to Agentic Coder Optimizer..."
                )
                task = progress.add_task(task_desc, total=None)

                # Run the initialization through subprocess
                result = self._run_initialization(prompt, verbose, update_mode)

                complete_desc = (
                    "[green]✓ Update complete"
                    if update_mode
                    else "[green]✓ Initialization complete"
                )
                progress.update(task, description=complete_desc)

            # Post-processing for update mode
            if update_mode and result.get("status") == "success":
                self._handle_update_post_processing()

            return result

        except Exception as e:
            logger.error(f"Failed to initialize project: {e}")
            console.print(f"[red]❌ Error: {e}[/red]")
            return {"status": "error", "message": str(e)}

    def _find_claude_mpm_script(self) -> Path:
        """Find the claude-mpm script location."""
        # Try to find claude-mpm in the project scripts directory first
        project_root = Path(__file__).parent.parent.parent.parent.parent
        script_path = project_root / "scripts" / "claude-mpm"
        if script_path.exists():
            return script_path
        # Otherwise assume it's in PATH
        return Path("claude-mpm")

    def _build_initialization_prompt(
        self,
        project_type: Optional[str] = None,
        framework: Optional[str] = None,
        ast_analysis: bool = True,
    ) -> str:
        """Build the initialization prompt for the agent."""
        base_prompt = f"""Please delegate this task to the Agentic Coder Optimizer agent:

Initialize this project for optimal use with Claude Code and Claude MPM.

Project Path: {self.project_path}
"""

        if project_type:
            base_prompt += f"Project Type: {project_type}\n"

        if framework:
            base_prompt += f"Framework: {framework}\n"

        base_prompt += """
Please perform the following initialization tasks:

1. **Analyze Current State**:
   - Scan project structure and existing configurations
   - Identify project type, language, and frameworks
   - Check for existing documentation and tooling

2. **Create/Update CLAUDE.md**:
   - Project overview and purpose
   - Architecture and key components
   - Development guidelines
   - ONE clear way to: build, test, deploy, lint, format
   - Links to all relevant documentation
   - Common tasks and workflows

3. **Establish Single-Path Standards**:
   - ONE command for each operation (build, test, lint, etc.)
   - Clear documentation of THE way to do things
   - Remove ambiguity in workflows

4. **Configure Development Tools**:
   - Set up or verify linting configuration
   - Configure code formatting standards
   - Establish testing framework
   - Add pre-commit hooks if needed

5. **Create Project Structure Documentation**:
   - Document folder organization
   - Explain where different file types belong
   - Provide examples of proper file placement

6. **Set Up GitHub Integration** (if applicable):
   - Create/update .github/workflows
   - Add issue and PR templates
   - Configure branch protection rules documentation

7. **Initialize Memory System**:
   - Create .claude-mpm/memories/ directory
   - Add initial memory files for key project knowledge
   - Document memory usage patterns

8. **Generate Quick Start Guide**:
   - Step-by-step setup instructions
   - Common commands reference
   - Troubleshooting guide
"""

        if ast_analysis:
            base_prompt += """
9. **Perform AST Analysis** (using Code Analyzer agent if needed):
   - Parse code files to extract structure (classes, functions, methods)
   - Generate comprehensive API documentation
   - Create code architecture diagrams
   - Document function signatures and dependencies
   - Extract docstrings and inline comments
   - Map code relationships and inheritance hierarchies
   - Generate developer documentation with:
     * Module overview and purpose
     * Class hierarchies and relationships
     * Function/method documentation
     * Type annotations and parameter descriptions
     * Code complexity metrics
     * Dependency graphs
   - Create DEVELOPER.md with technical architecture details
   - Add CODE_STRUCTURE.md with AST-derived insights
"""

        base_prompt += """

10. **Holistic CLAUDE.md Organization** (CRITICAL - Do this LAST):
   After completing all initialization tasks, take a holistic look at the CLAUDE.md file and:

   a) **Reorganize Content by Priority**:
      - CRITICAL instructions (security, data handling, core business rules) at the TOP
      - Project overview and purpose
      - Key architectural decisions and constraints
      - Development guidelines and standards
      - Common tasks and workflows
      - Links to additional documentation
      - Nice-to-have or optional information at the BOTTOM

   b) **Rank Instructions by Importance**:
      - Use clear markers:
        * 🔴 CRITICAL: Security, data handling, breaking changes, core business rules
        * 🟡 IMPORTANT: Key workflows, architecture decisions, performance requirements
        * 🟢 STANDARD: Common operations, coding standards, best practices
        * ⚪ OPTIONAL: Nice-to-have features, experimental code, future considerations
      - Group related instructions together
      - Ensure no contradictory instructions exist
      - Remove redundant or outdated information
      - Add a "Priority Index" at the top listing all CRITICAL and IMPORTANT items

   c) **Optimize for AI Agent Understanding**:
      - Use consistent formatting and structure
      - Provide clear examples for complex instructions
      - Include "WHY" explanations for critical rules
      - Add quick reference sections for common operations
      - Ensure instructions are actionable and unambiguous

   d) **Validate Completeness**:
      - Ensure ALL critical project knowledge is captured
      - Verify single-path principle (ONE way to do each task)
      - Check that all referenced documentation exists
      - Confirm all tools and dependencies are documented
      - Test that a new AI agent could understand the project from CLAUDE.md alone

   e) **Add Meta-Instructions Section**:
      - Include a section about how to maintain CLAUDE.md
      - Document when and how to update instructions
      - Provide guidelines for instruction priority levels
      - Add a changelog or last-updated timestamp

   f) **Follow This CLAUDE.md Template Structure**:
      ```markdown
      # Project Name - CLAUDE.md

      ## 🎯 Priority Index
      ### 🔴 CRITICAL Instructions
      - [List all critical items with links to their sections]

      ### 🟡 IMPORTANT Instructions
      - [List all important items with links to their sections]

      ## 📋 Project Overview
      [Brief description and purpose]

      ## 🔴 CRITICAL: Security & Data Handling
      [Critical security rules and data handling requirements]

      ## 🔴 CRITICAL: Core Business Rules
      [Non-negotiable business logic and constraints]

      ## 🟡 IMPORTANT: Architecture & Design
      [Key architectural decisions and patterns]

      ## 🟡 IMPORTANT: Development Workflow
      ### ONE Way to Build
      ### ONE Way to Test
      ### ONE Way to Deploy

      ## 🟢 STANDARD: Coding Guidelines
      [Standard practices and conventions]

      ## 🟢 STANDARD: Common Tasks
      [How to perform routine operations]

      ## 📚 Documentation Links
      [Links to additional resources]

      ## ⚪ OPTIONAL: Future Enhancements
      [Nice-to-have features and ideas]

      ## 📝 Meta: Maintaining This Document
      - Last Updated: [timestamp]
      - Update Frequency: [when to update]
      - Priority Guidelines: [how to assign priorities]
      ```

Please ensure all documentation is clear, concise, and optimized for AI agents to understand and follow.
Focus on establishing ONE clear way to do ANYTHING in the project.
The final CLAUDE.md should be a comprehensive, well-organized guide that any AI agent can follow to work effectively on this project.
"""

        return base_prompt

    def _build_claude_mpm_command(self, verbose: bool) -> List[str]:
        """Build the claude-mpm run command with appropriate arguments."""
        cmd = [str(self.claude_mpm_script)]

        # Add top-level flags that go before 'run' subcommand
        cmd.append("--no-check-dependencies")

        # Now add the run subcommand
        cmd.append("run")

        # Add non-interactive mode
        # We'll pass the prompt via stdin instead of -i flag
        cmd.append("--non-interactive")

        # Add verbose flag if requested (run subcommand argument)
        if verbose:
            cmd.append("--verbose")

        return cmd

    def _display_documentation_status(self, analysis: Dict) -> None:
        """Display current documentation status."""
        self.display.display_documentation_status(analysis)

    def _prompt_update_action(self) -> str:
        """Prompt user for update action."""
        console.print("\n[bold]How would you like to proceed?[/bold]\n")

        choices = {
            "1": ("update", "Update existing CLAUDE.md (preserves custom content)"),
            "2": ("recreate", "Recreate CLAUDE.md from scratch"),
            "3": ("review", "Review project state without changes"),
            "4": ("cancel", "Cancel operation"),
        }

        for key, (_, desc) in choices.items():
            console.print(f"  [{key}] {desc}")

        choice = Prompt.ask(
            "\nSelect option", choices=list(choices.keys()), default="1"
        )
        return choices[choice][0]

    def _run_review_mode(self) -> Dict:
        """Run review mode to analyze project without changes."""
        console.print("\n[bold cyan]🔍 Project Review Mode[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Analyze project structure
            task = progress.add_task("[cyan]Analyzing project structure...", total=None)
            structure_report = self.organizer.verify_structure()
            progress.update(task, description="[green]✓ Structure analysis complete")

            # Analyze documentation
            task = progress.add_task("[cyan]Analyzing documentation...", total=None)
            doc_analysis = self.doc_manager.analyze_existing_content()
            progress.update(
                task, description="[green]✓ Documentation analysis complete"
            )

            # Analyze git history
            if self.analyzer.is_git_repo:
                task = progress.add_task("[cyan]Analyzing git history...", total=None)
                git_analysis = self.analyzer.analyze_git_history()
                progress.update(task, description="[green]✓ Git analysis complete")
            else:
                git_analysis = None

            # Detect project state
            task = progress.add_task("[cyan]Detecting project state...", total=None)
            project_state = self.analyzer.detect_project_state()
            progress.update(task, description="[green]✓ State detection complete")

        # Display comprehensive report
        self._display_review_report(
            structure_report, doc_analysis, git_analysis, project_state
        )

        return {
            "status": "success",
            "mode": "review",
            "structure_report": structure_report,
            "documentation_analysis": doc_analysis,
            "git_analysis": git_analysis,
            "project_state": project_state,
        }

    def _display_review_report(
        self, structure: Dict, docs: Dict, git: Optional[Dict], state: Dict
    ) -> None:
        """Display comprehensive review report."""
        self.display.display_header("PROJECT REVIEW REPORT")

        # Project State
        state_data = {"Phase": state.get("phase", "unknown")}
        if state.get("indicators"):
            state_data["Indicators"] = state["indicators"][:5]
        self.display.display_report_section("📊 Project State", state_data)

        # Structure Report
        structure_data = {
            "Existing directories": len(structure.get("exists", [])),
            "Missing directories": len(structure.get("missing", [])),
        }
        if structure.get("issues"):
            structure_data["Issues found"] = len(structure["issues"])
            structure_data["Issues"] = structure["issues"][:3]
        self.display.display_report_section("📁 Project Structure", structure_data)

        # Documentation Report
        self.display.display_section_title("📚 Documentation Status")
        if docs.get("exists"):
            console.print(f"  CLAUDE.md: Found ({docs.get('size', 0):,} chars)")
            console.print(f"  Sections: {len(docs.get('sections', []))}")
            console.print(
                f"  Priority markers: {'Yes' if docs.get('has_priority_markers') else 'No'}"
            )
        else:
            console.print("  CLAUDE.md: Not found")

        # Git Analysis
        if git and git.get("git_available"):
            git_metrics = {
                "Commits": len(git.get("recent_commits", [])),
                "Authors": git.get("authors", {}).get("total_authors", 0),
                "Changed files": git.get("changed_files", {}).get("total_files", 0),
            }

            if git.get("branch_info"):
                branch_info = git["branch_info"]
                git_metrics["Current branch"] = branch_info.get(
                    "current_branch", "unknown"
                )

            self.display.display_metrics_section(
                "📈 Recent Activity (30 days)", git_metrics
            )

            if git.get("branch_info", {}).get("has_uncommitted_changes"):
                self.display.display_metric_row(
                    "⚠️  Uncommitted changes",
                    f"{git['branch_info'].get('uncommitted_files', 0)} files",
                    warning=True,
                )

        # Recommendations
        if state.get("recommendations"):
            self.display.display_recommendations(state["recommendations"])

        self.display.display_separator()

    def _run_quick_update_mode(
        self,
        days: int = 30,
        non_interactive: bool = False,
        export: Optional[str] = None,
    ) -> Dict:
        """Run quick update mode - lightweight update based on recent git activity."""
        console.print("\n[bold cyan]⚡ Quick Update Mode[/bold cyan]\n")
        console.print(
            f"[dim]Analyzing recent git activity ({days} days) for lightweight documentation update...[/dim]\n"
        )

        if not self.analyzer.is_git_repo:
            console.print(
                "[yellow]⚠️  Not a git repository. Quick update requires git.[/yellow]"
            )
            console.print(
                "[dim]Tip: Use `/mpm-init --review` for non-git projects.[/dim]\n"
            )
            return {
                "status": "error",
                "message": "Quick update requires a git repository",
            }

        claude_md = self.project_path / "CLAUDE.md"
        if not claude_md.exists():
            console.print(
                "[yellow]⚠️  CLAUDE.md not found. Quick update requires existing documentation.[/yellow]"
            )
            console.print(
                "[dim]Tip: Use `/mpm-init` to create initial documentation.[/dim]\n"
            )
            return {
                "status": "error",
                "message": "Quick update requires existing CLAUDE.md",
            }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Analyze git history
            task = progress.add_task(
                f"[cyan]Analyzing git history ({days} days)...", total=None
            )
            git_analysis = self.analyzer.analyze_git_history(days_back=days)
            progress.update(task, description="[green]✓ Git analysis complete")

            # Analyze current documentation
            task = progress.add_task(
                "[cyan]Checking documentation status...", total=None
            )
            doc_analysis = self.doc_manager.analyze_existing_content()
            progress.update(task, description="[green]✓ Documentation analyzed")

        # Generate activity report
        activity_report = self._generate_activity_report(
            git_analysis, doc_analysis, days
        )

        # Display the report
        self._display_activity_report(activity_report)

        # Export report if requested
        if export:
            export_path = self._export_activity_report(activity_report, export)
            console.print(f"\n[green]✅ Report exported to: {export_path}[/green]")

        # Handle non-interactive mode
        if non_interactive:
            console.print(
                "\n[cyan]ℹ️  Non-interactive mode: Report displayed, no changes made.[/cyan]"
            )
            return {
                "status": "success",
                "mode": "quick_update",
                "activity_report": activity_report,
                "changes_made": False,
                "non_interactive": True,
            }

        # Offer to append activity notes to CLAUDE.md
        console.print("\n[bold]Update Options:[/bold]")
        console.print("  [1] Append activity summary to CLAUDE.md")
        console.print("  [2] Display report only (no changes)")
        console.print("  [3] Cancel")

        from rich.prompt import Prompt

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3"], default="2")

        if choice == "1":
            # Append activity notes
            self._append_activity_notes(claude_md, activity_report)
            console.print("\n[green]✅ Activity notes appended to CLAUDE.md[/green]")

            # Archive the update
            self.archive_manager.auto_archive_before_update(
                claude_md, update_reason="Quick update - recent activity summary"
            )

            return {
                "status": "success",
                "mode": "quick_update",
                "activity_report": activity_report,
                "changes_made": True,
            }
        if choice == "2":
            console.print("\n[cyan]Report generated - no changes made[/cyan]")
            return {
                "status": "success",
                "mode": "quick_update",
                "activity_report": activity_report,
                "changes_made": False,
            }
        console.print("\n[yellow]Quick update cancelled[/yellow]")
        return {"status": "cancelled", "message": "Quick update cancelled"}

    def _catchup(self) -> Dict[str, Any]:
        """Get recent commit history for PM context.

        Returns:
            Dict containing commit history and contributor stats
        """
        from collections import Counter
        from datetime import datetime
        from subprocess import run

        try:
            # Get last 25 commits from all branches with author info
            result = run(
                ["git", "log", "--all", "--format=%h|%an|%ai|%s", "-25"],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(self.project_path),
            )

            commits = []
            authors = []

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|", 3)
                if len(parts) == 4:
                    hash_val, author, date_str, message = parts

                    # Parse date
                    try:
                        dt = datetime.fromisoformat(date_str.replace(" ", "T", 1))
                        date_display = dt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        date_display = date_str[:16]

                    commits.append(
                        {
                            "hash": hash_val,
                            "author": author,
                            "date": date_display,
                            "message": message,
                        }
                    )
                    authors.append(author)

            # Calculate contributor stats
            author_counts = Counter(authors)

            return {
                "commits": commits,
                "total_commits": len(commits),
                "contributors": dict(author_counts),
                "contributor_count": len(author_counts),
            }

        except Exception as e:
            console.print(f"[yellow]Could not retrieve commit history: {e}[/yellow]")
            return {
                "commits": [],
                "total_commits": 0,
                "contributors": {},
                "contributor_count": 0,
                "error": str(e),
            }

    def _display_catchup(self, data: Dict[str, Any]) -> None:
        """Display catchup information to console.

        Args:
            data: Commit history data from _catchup()
        """
        from rich.panel import Panel
        from rich.table import Table

        if data.get("error"):
            console.print(
                Panel(
                    "[yellow]Not a git repository or no commits found[/yellow]",
                    title="⚠️ Catchup Status",
                    border_style="yellow",
                )
            )
            return

        # Display contributor summary
        if data["contributors"]:
            console.print("\n[bold cyan]👥 Active Contributors[/bold cyan]")
            for author, count in sorted(
                data["contributors"].items(), key=lambda x: x[1], reverse=True
            ):
                console.print(
                    f"  • [green]{author}[/green]: {count} commit{'s' if count != 1 else ''}"
                )

        # Display commit history table
        if data["commits"]:
            console.print(
                f"\n[bold cyan]📝 Last {data['total_commits']} Commits[/bold cyan]"
            )

            table = Table(
                show_header=True, header_style="bold magenta", border_style="dim"
            )
            table.add_column("#", style="dim", width=3)
            table.add_column("Hash", style="yellow", width=8)
            table.add_column("Author", style="green", width=20)
            table.add_column("Date", style="cyan", width=16)
            table.add_column("Message", style="white")

            for idx, commit in enumerate(data["commits"], 1):
                # Truncate message if too long
                msg = commit["message"]
                if len(msg) > 80:
                    msg = msg[:77] + "..."

                # Truncate author if too long
                author = commit["author"]
                if len(author) > 18:
                    author = author[:18] + "..."

                table.add_row(str(idx), commit["hash"], author, commit["date"], msg)

            console.print(table)

        # Display PM recommendations
        console.print("\n[bold cyan]💡 PM Recommendations[/bold cyan]")
        console.print(
            f"  • Total activity: {data['total_commits']} commits from {data['contributor_count']} contributor{'s' if data['contributor_count'] != 1 else ''}"
        )
        console.print("  • Review commit messages for recent project context")
        console.print("  • Identify development patterns and focus areas")
        console.print("  • Use this context to inform current work priorities\n")

    def _generate_activity_report(
        self, git_analysis: Dict, doc_analysis: Dict, days: int = 30
    ) -> Dict:
        """Generate activity report from git analysis and documentation status."""
        from datetime import datetime, timezone

        report = {
            "period": f"Last {days} days",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {},
            "recommendations": [],
        }

        # Git activity summary
        if git_analysis.get("git_available"):
            recent_commits = git_analysis.get("recent_commits", [])
            changed_files = git_analysis.get("changed_files", {})
            authors = git_analysis.get("authors", {})
            branch_info = git_analysis.get("branch_info", {})

            report["summary"] = {
                "total_commits": len(recent_commits),
                "total_authors": authors.get("total_authors", 0),
                "files_changed": changed_files.get("total_files", 0),
                "current_branch": branch_info.get("current_branch", "unknown"),
                "has_uncommitted": branch_info.get("has_uncommitted_changes", False),
                "uncommitted_count": branch_info.get("uncommitted_files", 0),
            }

            # Recent commits (last 10)
            report["recent_commits"] = recent_commits[:10]

            # Most changed files
            most_changed = changed_files.get("most_changed", {})
            report["hot_files"] = list(most_changed.items())[:10]

            # Active branches
            branches = branch_info.get("branches", [])
            report["active_branches"] = [
                b for b in branches if not b.startswith("remotes/")
            ][:5]

            # Generate recommendations
            if len(recent_commits) > 20:
                report["recommendations"].append(
                    "High activity detected - consider updating architecture docs"
                )

            if changed_files.get("total_files", 0) > 50:
                report["recommendations"].append(
                    "Many files changed - review CLAUDE.md for accuracy"
                )

            if branch_info.get("has_uncommitted_changes"):
                report["recommendations"].append(
                    "Uncommitted changes detected - commit before updating docs"
                )

            # Check for documentation changes
            doc_changes = git_analysis.get("documentation_changes", {})
            if not doc_changes.get("has_recent_doc_changes"):
                report["recommendations"].append(
                    "No recent doc updates - CLAUDE.md may be outdated"
                )

        # Documentation freshness
        if doc_analysis.get("exists"):
            report["doc_status"] = {
                "size": doc_analysis.get("size", 0),
                "lines": doc_analysis.get("lines", 0),
                "has_priority_index": doc_analysis.get("has_priority_index", False),
                "has_priority_markers": doc_analysis.get("has_priority_markers", False),
                "last_modified": doc_analysis.get("last_modified", "unknown"),
            }

            if not doc_analysis.get("has_priority_markers"):
                report["recommendations"].append(
                    "Add priority markers (🔴🟡🟢⚪) to CLAUDE.md"
                )

        return report

    def _export_activity_report(self, report: Dict, export_path: str) -> Path:
        """Export activity report to a markdown file."""
        from datetime import datetime, timezone
        from pathlib import Path

        # Determine export path
        if export_path == "auto":
            # Generate default path with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            reports_dir = self.project_path / "docs" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            file_path = reports_dir / f"activity-report-{timestamp}.md"
        else:
            # Use provided path
            file_path = Path(export_path)
            if not file_path.is_absolute():
                file_path = self.project_path / file_path
            # Create parent directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate markdown content
        summary = report.get("summary", {})
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Activity Report

**Generated**: {timestamp}
**Analysis Period**: {report.get('period', 'Last 30 days')}

## Summary

- **Total Commits**: {summary.get('total_commits', 0)}
- **Active Contributors**: {summary.get('total_authors', 0)}
- **Files Modified**: {summary.get('files_changed', 0)}
- **Current Branch**: {summary.get('current_branch', 'unknown')}
"""

        if summary.get("has_uncommitted"):
            content += f"- **⚠️  Uncommitted Changes**: {summary.get('uncommitted_count', 0)} files\n"

        # Recent commits
        recent_commits = report.get("recent_commits", [])
        if recent_commits:
            content += "\n## Recent Commits\n\n"
            for commit in recent_commits[:10]:
                content += (
                    f"- `{commit['hash']}` {commit['message']} - {commit['author']}\n"
                )

        # Hot files
        hot_files = report.get("hot_files", [])
        if hot_files:
            content += "\n## Most Changed Files\n\n"
            for hot_file_path, changes in hot_files[:10]:
                content += f"- `{hot_file_path}`: {changes} changes\n"

        # Active branches
        branches = report.get("active_branches", [])
        if branches:
            content += "\n## Active Branches\n\n"
            for branch in branches:
                marker = "→" if branch == summary.get("current_branch") else " "
                content += f"{marker} {branch}\n"

        # Documentation status
        doc_status = report.get("doc_status", {})
        if doc_status:
            content += "\n## CLAUDE.md Status\n\n"
            content += f"- **Size**: {doc_status.get('size', 0):,} characters\n"
            content += f"- **Lines**: {doc_status.get('lines', 0)}\n"
            content += f"- **Priority Markers**: {'✓' if doc_status.get('has_priority_markers') else '✗'}\n"
            content += (
                f"- **Last Modified**: {doc_status.get('last_modified', 'unknown')}\n"
            )

        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            content += "\n## Recommendations\n\n"
            for rec in recommendations:
                content += f"- {rec}\n"

        content += (
            "\n---\n\n*Generated by Claude MPM `/mpm-init --quick-update --export`*\n"
        )

        # Write to file
        file_path.write_text(content, encoding="utf-8")

        return file_path

    def _display_activity_report(self, report: Dict) -> None:
        """Display the activity report in a formatted manner."""
        self.display.display_header("RECENT ACTIVITY SUMMARY")

        summary = report.get("summary", {})
        period = report.get("period", "Last 30 days")

        # Summary statistics
        self.display.display_activity_summary(summary, period)

        # Recent commits
        recent_commits = report.get("recent_commits", [])
        if recent_commits:
            self.display.display_commit_list(recent_commits)

        # Hot files
        hot_files = report.get("hot_files", [])
        if hot_files:
            self.display.display_file_change_list(hot_files)

        # Active branches
        branches = report.get("active_branches", [])
        current_branch = summary.get("current_branch", "unknown")
        if branches:
            self.display.display_branch_list(branches, current_branch)

        # Documentation status
        doc_status = report.get("doc_status", {})
        if doc_status:
            doc_metrics = {
                "Size": f"{doc_status.get('size', 0):,} characters",
                "Lines": doc_status.get("lines", 0),
                "Priority markers": (
                    "✓" if doc_status.get("has_priority_markers") else "✗"
                ),
                "Last modified": doc_status.get("last_modified", "unknown"),
            }
            self.display.display_metrics_section("📚 CLAUDE.md Status", doc_metrics)

        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            self.display.display_recommendations(recommendations)

        self.display.display_separator()

    def _append_activity_notes(self, claude_md_path: Path, report: Dict) -> None:
        """Append activity notes to CLAUDE.md."""
        from datetime import datetime, timezone

        # Generate activity summary section
        summary = report.get("summary", {})
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        activity_section = f"""

---

## 📈 Recent Activity Summary

**Last Updated**: {timestamp}
**Analysis Period**: {report.get('period', 'Last 30 days')}

### Activity Metrics
- **Commits**: {summary.get('total_commits', 0)}
- **Contributors**: {summary.get('total_authors', 0)}
- **Files Changed**: {summary.get('files_changed', 0)}
- **Current Branch**: {summary.get('current_branch', 'unknown')}
"""

        if summary.get("has_uncommitted"):
            activity_section += f"- **⚠️  Uncommitted Changes**: {summary.get('uncommitted_count', 0)} files\n"

        # Add recent commits
        recent_commits = report.get("recent_commits", [])
        if recent_commits:
            activity_section += "\n### Recent Commits\n"
            for commit in recent_commits[:5]:
                activity_section += f"- `{commit['hash']}` {commit['message'][:60]} ({commit['author']})\n"

        # Add hot files
        hot_files = report.get("hot_files", [])
        if hot_files:
            activity_section += "\n### Most Active Files\n"
            for file_path, changes in hot_files[:5]:
                activity_section += f"- `{file_path}`: {changes} changes\n"

        # Add recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            activity_section += "\n### 💡 Recommendations\n"
            for rec in recommendations:
                activity_section += f"- {rec}\n"

        activity_section += "\n---\n"

        # Append to file
        with open(claude_md_path, "a", encoding="utf-8") as f:
            f.write(activity_section)

    def _run_dry_run_mode(self, organize_files: bool, has_existing: bool) -> Dict:
        """Run dry-run mode to show what would be done without making changes."""
        console.print("\n[bold cyan]🔍 Dry Run Mode - Preview Changes[/bold cyan]\n")

        actions_planned = []

        # Check what organization would do
        if organize_files:
            console.print("[bold]📁 File Organization Analysis:[/bold]")

            # Get structure validation without making changes
            validation = self.organizer.validate_structure()
            if validation.get("issues"):
                console.print("  [yellow]Files that would be organized:[/yellow]")
                for issue in validation["issues"][:10]:
                    actions_planned.append(
                        f"Organize: {issue.get('description', 'Unknown')}"
                    )
                    console.print(f"    • {issue.get('description', 'Unknown')}")
            else:
                console.print("  ✅ Project structure is already well-organized")

        # Check what documentation updates would occur
        if has_existing:
            console.print("\n[bold]📚 Documentation Updates:[/bold]")
            doc_analysis = self.doc_manager.analyze_existing_content()

            if not doc_analysis.get("has_priority_markers"):
                actions_planned.append("Add priority markers (🔴🟡🟢⚪)")
                console.print("  • Add priority markers (🔴🟡🟢⚪)")

            if doc_analysis.get("outdated_patterns"):
                actions_planned.append("Update outdated patterns")
                console.print("  • Update outdated patterns")

            if not doc_analysis.get("has_priority_index"):
                actions_planned.append("Add priority index section")
                console.print("  • Add priority index section")

            # Archive would be created
            actions_planned.append("Archive current CLAUDE.md to docs/_archive/")
            console.print("  • Archive current CLAUDE.md to docs/_archive/")
        else:
            console.print("\n[bold]📚 Documentation Creation:[/bold]")
            actions_planned.append("Create new CLAUDE.md with priority structure")
            console.print("  • Create new CLAUDE.md with priority structure")

        # General improvements
        console.print("\n[bold]🔧 General Improvements:[/bold]")
        actions_planned.extend(
            [
                "Update/create .gitignore if needed",
                "Verify project structure compliance",
                "Add memory system initialization",
                "Set up single-path workflows",
            ]
        )
        for action in actions_planned[-4:]:
            console.print(f"  • {action}")

        console.print(
            f"\n[bold cyan]Summary: {len(actions_planned)} actions would be performed[/bold cyan]"
        )
        console.print("\n[dim]Run without --dry-run to execute these changes.[/dim]\n")

        return {
            "status": "success",
            "mode": "dry_run",
            "actions_planned": actions_planned,
            "message": "Dry run completed - no changes made",
        }

    def _run_pre_initialization_checks(
        self, organize_files: bool, skip_archive: bool, has_existing: bool
    ) -> Dict:
        """Run pre-initialization checks and preparations."""
        checks_passed = []
        warnings = []

        # Run comprehensive project readiness check
        ready, actions = self.organizer.ensure_project_ready(
            auto_organize=organize_files,
            safe_mode=True,  # Only perform safe operations by default
        )

        if actions:
            checks_passed.extend(actions)

        # Get structure validation report
        validation = self.organizer.validate_structure()
        if validation["warnings"]:
            warnings.extend(validation["warnings"])
        if validation["errors"]:
            warnings.extend(validation["errors"])

        # Show structure grade
        if validation.get("grade"):
            checks_passed.append(f"Structure validation: {validation['grade']}")

        # Archive existing documentation if needed
        if has_existing and not skip_archive:
            if self.archive_manager.auto_archive_before_update(
                self.project_path / "CLAUDE.md", update_reason="Before mpm-init update"
            ):
                checks_passed.append("Archived existing CLAUDE.md")

        # Check for issues in validation report
        if validation.get("issues"):
            for issue in validation["issues"]:
                warnings.append(issue["description"])

        if warnings:
            console.print("\n[yellow]⚠️  Project issues detected:[/yellow]")
            for warning in warnings[:5]:
                console.print(f"  • {warning}")
            console.print()

        if checks_passed:
            console.print("[green]✅ Pre-initialization checks:[/green]")
            for check in checks_passed:
                console.print(f"  • {check}")
            console.print()

        return {
            "status": "success",
            "checks_passed": checks_passed,
            "warnings": warnings,
        }

    def _show_update_plan(self, ast_analysis: bool, preserve_custom: bool) -> None:
        """Show update mode plan."""
        console.print(
            Panel(
                "[bold cyan]🔄 Claude MPM Documentation Update[/bold cyan]\n\n"
                "This will update your existing CLAUDE.md with:\n"
                "• Smart merging of new and existing content\n"
                + ("• Preservation of custom sections\n" if preserve_custom else "")
                + "• Priority-based reorganization (🔴🟡🟢⚪)\n"
                "• Updated single-path workflows\n"
                "• Refreshed tool configurations\n"
                + (
                    "• AST analysis for enhanced documentation\n"
                    if ast_analysis
                    else ""
                )
                + "• Automatic archival of previous version\n"
                + "• Holistic review and optimization\n"
                + "\n[dim]Previous version will be archived in docs/_archive/[/dim]",
                title="Update Mode",
                border_style="blue",
            )
        )

    def _show_initialization_plan(self, ast_analysis: bool) -> None:
        """Show standard initialization plan."""
        console.print(
            Panel(
                "[bold cyan]🤖👥 Claude MPM Project Initialization[/bold cyan]\n\n"
                "This will set up your project with:\n"
                "• Clear CLAUDE.md documentation for AI agents\n"
                "• Single-path workflows (ONE way to do ANYTHING)\n"
                "• Optimized project structure\n"
                "• Tool configurations (linting, formatting, testing)\n"
                "• GitHub workflows and CI/CD setup\n"
                "• Memory system initialization\n"
                + (
                    "• AST analysis for comprehensive code documentation\n"
                    if ast_analysis
                    else ""
                )
                + "• Holistic CLAUDE.md organization with ranked instructions\n"
                + "• Priority-based content structure (🔴🟡🟢⚪)\n"
                + "\n[dim]Powered by Agentic Coder Optimizer Agent[/dim]",
                title="MPM-Init",
                border_style="cyan",
            )
        )

    def _build_update_prompt(
        self,
        project_type: Optional[str],
        framework: Optional[str],
        ast_analysis: bool,
        preserve_custom: bool,
    ) -> str:
        """Build prompt for update mode."""
        # Get existing content analysis
        doc_analysis = self.doc_manager.analyze_existing_content()

        prompt = f"""Please delegate this task to the Agentic Coder Optimizer agent:

UPDATE existing CLAUDE.md documentation for this project.

Project Path: {self.project_path}
Update Mode: Smart merge with existing content
"""
        if project_type:
            prompt += f"Project Type: {project_type}\n"
        if framework:
            prompt += f"Framework: {framework}\n"

        prompt += f"""
Existing Documentation Analysis:
- Current CLAUDE.md: {doc_analysis.get('size', 0):,} characters, {doc_analysis.get('lines', 0)} lines
- Has Priority Index: {'Yes' if doc_analysis.get('has_priority_index') else 'No'}
- Custom Sections: {len(doc_analysis.get('custom_sections', []))} found
"""
        if preserve_custom and doc_analysis.get("custom_sections"):
            prompt += f"- Preserve Custom Sections: {', '.join(doc_analysis['custom_sections'][:5])}\n"

        prompt += """
Please perform the following UPDATE tasks:

1. **Review Existing Content**:
   - Analyze current CLAUDE.md structure and content
   - Identify outdated or missing information
   - Preserve valuable custom sections and project-specific knowledge

2. **Smart Content Merge**:
   - Update project overview if needed
   - Refresh architecture documentation
   - Update development workflows to ensure single-path principle
   - Merge new standard sections while preserving custom content
   - Remove duplicate or contradictory information

3. **Update Priority Organization**:
   - Reorganize content with priority markers (🔴🟡🟢⚪)
   - Ensure critical instructions are at the top
   - Update priority index with all important items
   - Validate instruction clarity and completeness

4. **Refresh Technical Content**:
   - Update build/test/deploy commands
   - Verify tool configurations are current
   - Update dependency information
   - Refresh API documentation if applicable
"""
        if ast_analysis:
            prompt += """
5. **Update Code Documentation** (using Code Analyzer agent):
   - Re-analyze code structure for changes
   - Update API documentation
   - Refresh architecture diagrams
   - Update function/class documentation
"""
        prompt += """
6. **Final Optimization**:
   - Ensure single-path principle throughout
   - Validate all links and references
   - Add/update timestamp in meta section
   - Verify AI agent readability

IMPORTANT: This is an UPDATE operation. Intelligently merge new content with existing,
preserving valuable project-specific information while refreshing standard sections.
"""
        return prompt

    def _handle_update_post_processing(self) -> None:
        """Handle post-processing after successful update."""
        # Generate update report
        if self.doc_manager.has_existing_documentation():
            latest_archive = self.archive_manager.get_latest_archive("CLAUDE.md")
            if latest_archive:
                comparison = self.archive_manager.compare_with_archive(
                    self.project_path / "CLAUDE.md", latest_archive.name
                )

                if not comparison.get("identical"):
                    console.print("\n[bold cyan]📊 Update Summary[/bold cyan]")
                    console.print(
                        f"  Lines changed: {comparison.get('lines_added', 0):+d}"
                    )
                    console.print(
                        f"  Size change: {comparison.get('size_change', 0):+,} characters"
                    )
                    console.print(f"  Previous version: {latest_archive.name}")

    def _run_initialization(
        self,
        prompt: str,
        verbose: bool,
        update_mode: bool = False,
    ) -> Dict:
        """Run the initialization through subprocess calling claude-mpm."""
        import tempfile

        try:
            # Write prompt to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as tmp_file:
                tmp_file.write(prompt)
                prompt_file = tmp_file.name

            try:
                # Build the command
                cmd = self._build_claude_mpm_command(verbose)
                # Add the input file flag
                cmd.extend(["-i", prompt_file])

                # Log the command if verbose
                if verbose:
                    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
                    console.print(f"[dim]Prompt file: {prompt_file}[/dim]")

                # Execute the command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_path),
                    check=False,
                )
            finally:
                # Clean up temporary file

                with contextlib.suppress(Exception):
                    Path(prompt_file).unlink()

            # Display output if verbose
            if verbose and result.stdout:
                console.print(result.stdout)
            if verbose and result.stderr:
                console.print(f"[yellow]{result.stderr}[/yellow]")

            # Check result - be more lenient with return codes
            if result.returncode == 0 or (self.project_path / "CLAUDE.md").exists():
                response = {
                    "status": "success",
                    "message": "Project initialized successfully",
                    "files_created": [],
                    "files_updated": [],
                    "next_steps": [],
                }

                # Check if CLAUDE.md was created
                claude_md = self.project_path / "CLAUDE.md"
                if claude_md.exists():
                    response["files_created"].append("CLAUDE.md")

                # Check for other common files
                for file_name in ["CODE.md", "DEVELOPER.md", "STRUCTURE.md", "OPS.md"]:
                    file_path = self.project_path / file_name
                    if file_path.exists():
                        response["files_created"].append(file_name)

                # Add next steps
                response["next_steps"] = [
                    "Review the generated CLAUDE.md documentation",
                    "Verify the project structure meets your needs",
                    "Run 'claude-mpm run' to start using the optimized setup",
                ]

                # Display results
                self._display_results(response, verbose)

                return response
            # Extract meaningful error message
            error_msg = (
                result.stderr
                if result.stderr
                else result.stdout if result.stdout else "Unknown error occurred"
            )

            logger.error(f"claude-mpm run failed: {error_msg}")
            return {
                "status": "error",
                "message": f"Initialization failed: {error_msg}",
            }

        except FileNotFoundError:
            logger.error("claude-mpm command not found")
            console.print(
                "[red]Error: claude-mpm command not found. Ensure Claude MPM is properly installed.[/red]"
            )
            return {"status": "error", "message": "claude-mpm not found"}
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return {"status": "error", "message": str(e)}

    def handle_context(
        self,
        session_id: Optional[str] = None,
        list_sessions: bool = False,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Provide intelligent context for resuming work based on git history.

        Analyzes recent commits to identify:
        - Active work streams (what was being worked on)
        - Intent and motivation (why this work)
        - Risks and blockers
        - Recommended next actions

        This delegates to Research agent for deep analysis.

        Args:
            session_id: Unused parameter (for compatibility)
            list_sessions: Unused parameter (for compatibility)
            days: Number of days of git history to analyze (default: 7)

        Returns:
            Dict containing context result
        """
        from claude_mpm.utils.git_analyzer import analyze_recent_activity

        # 1. Analyze git history with adaptive window
        console.print(f"\n🔍 Analyzing last {days} days of git history...\n")
        git_analysis = analyze_recent_activity(
            repo_path=str(self.project_path), days=days, max_commits=50, min_commits=25
        )

        # Show adaptive behavior to user
        if git_analysis.get("adaptive_mode"):
            console.print(
                f"[cyan]ℹ️  Note: Analyzed {git_analysis.get('actual_time_span', 'extended period')} "
                f"to get meaningful context[/cyan]"
            )
            if git_analysis.get("reason"):
                console.print(f"[dim]    Reason: {git_analysis['reason']}[/dim]\n")
            else:
                console.print()

        if git_analysis.get("error"):
            console.print(
                f"[yellow]⚠️  Could not analyze git history: {git_analysis['error']}[/yellow]"
            )
            console.print(
                "[dim]Ensure this is a git repository with commit history.[/dim]\n"
            )
            return {
                "status": "error",
                "message": git_analysis["error"],
            }

        if not git_analysis.get("has_activity"):
            console.print(
                f"[yellow]⚠️  No git activity found in the last {days} days.[/yellow]"
            )
            console.print("[dim]Try increasing the --days parameter.[/dim]\n")
            return {
                "status": "error",
                "message": f"No git activity in last {days} days",
            }

        # 2. Build Research delegation prompt
        research_prompt = self._build_research_context_prompt(git_analysis, days)

        # 3. Display prompt for PM to delegate
        console.print("\n" + "=" * 80)
        console.print("📋 DELEGATE TO RESEARCH AGENT:")
        console.print("=" * 80 + "\n")
        console.print(research_prompt)
        console.print("\n" + "=" * 80 + "\n")

        return {
            "status": "context_ready",
            "git_analysis": git_analysis,
            "research_prompt": research_prompt,
            "recommendation": "PM should delegate this prompt to Research agent",
        }

    def _build_research_context_prompt(
        self, git_analysis: Dict[str, Any], days: int
    ) -> str:
        """Build structured Research agent delegation prompt from git analysis."""

        # Extract key data
        commits = git_analysis.get("commits", [])
        branches = git_analysis.get("branches", [])
        contributors = git_analysis.get("contributors", {})
        file_changes = git_analysis.get("file_changes", {})

        # Build prompt following Prompt Engineer's template
        prompt = f"""# Project Context Analysis Mission

You are Research agent analyzing git history to provide PM with intelligent project context for resuming work.

## Analysis Scope
- **Time Range**: Last {days} days"""

        # Add adaptive mode note if applicable
        if git_analysis.get("adaptive_mode"):
            actual_days = git_analysis.get("actual_time_span", "extended period")
            prompt += f""" (adaptive: {actual_days} days analyzed)
- **Note**: {git_analysis.get('reason', 'Analysis window adjusted to ensure meaningful context')}"""

        prompt += f"""
- **Commits Analyzed**: {len(commits)} commits
- **Branches**: {', '.join(branches[:5]) if branches else 'main'}
- **Contributors**: {', '.join(contributors.keys()) if contributors else 'Unknown'}

## Your Mission

Analyze git history to answer these questions for PM:

1. **What was being worked on?** (Active work streams)
2. **Why was this work happening?** (Intent and motivation)
3. **What's the natural next step?** (Continuation recommendations)
4. **What needs attention?** (Risks, stalls, conflicts)

## Git Data Provided

### Recent Commits ({min(len(commits), 10)} most recent):
"""

        # Add recent commits
        for commit in commits[:10]:
            author = commit.get("author", "Unknown")
            timestamp = commit.get("timestamp", "Unknown date")
            message = commit.get("message", "No message")
            files = commit.get("files", [])

            prompt += f"\n- **{timestamp}** by {author}"
            prompt += f"\n  {message}"
            prompt += f"\n  Files changed: {len(files)}\n"

        # Add file change summary
        if file_changes:
            # Sort by modifications count
            sorted_files = sorted(
                file_changes.items(),
                key=lambda x: x[1].get("modifications", 0),
                reverse=True,
            )
            prompt += "\n### Most Changed Files:\n"
            for file_path, file_data in sorted_files[:10]:
                modifications = file_data.get("modifications", 0)
                file_contributors = file_data.get("contributors", [])
                prompt += f"- {file_path}: {modifications} changes ({len(file_contributors)} contributor{'s' if len(file_contributors) != 1 else ''})\n"

        # Add contributor summary
        if contributors:
            prompt += "\n### Contributors:\n"
            sorted_contributors = sorted(
                contributors.items(),
                key=lambda x: x[1].get("commits", 0),
                reverse=True,
            )
            for name, info in sorted_contributors[:5]:
                commit_count = info.get("commits", 0)
                prompt += f"- {name}: {commit_count} commit{'s' if commit_count != 1 else ''}\n"

        # Add analysis instructions
        prompt += """

## Analysis Instructions

### Phase 1: Work Stream Identification
Group related commits into thematic work streams. For each stream:
- **Name**: Infer from commit messages (e.g., "Authentication refactor")
- **Status**: ongoing/completed/stalled
- **Commits**: Count of commits in this stream
- **Intent**: WHY this work (from commit bodies/messages)
- **Key Files**: Most changed files in this stream

### Phase 2: Risk Detection
Identify:
- **Stalled Work**: Work streams with no activity >3 days
- **Anti-Patterns**: WIP commits, temp commits, debug commits
- **Documentation Lag**: Code changes without doc updates
- **Conflicts**: Merge conflicts or divergent branches

### Phase 3: Recommendations
Based on analysis:
1. **Primary Focus**: Most active/recent work to continue
2. **Quick Wins**: Small tasks that could be finished
3. **Blockers**: Issues preventing progress
4. **Next Steps**: Logical continuation points

## Output Format

Provide a clear markdown summary with:

1. **Active Work Streams** (What was being worked on)
2. **Intent Summary** (Why this work matters)
3. **Risks Detected** (What needs attention)
4. **Recommended Next Actions** (What to work on)

Keep it concise (<1000 words) but actionable.

## Success Criteria
- Work streams accurately reflect development themes
- Intent captures the "why" not just "what"
- Recommendations are specific and actionable
- Risks are prioritized by impact
"""

        return prompt

    def _display_results(self, result: Dict, verbose: bool):
        """Display initialization results."""
        if result["status"] == "success":
            console.print("\n[green]✅ Project Initialization Complete![/green]\n")

            # Display files created
            if result.get("files_created"):
                self.display.display_files_list(
                    "Files Created:", result["files_created"]
                )

            # Display files updated
            if result.get("files_updated"):
                self.display.display_files_list(
                    "Files Updated:", result["files_updated"]
                )

            # Display next steps
            if result.get("next_steps"):
                self.display.display_next_steps(result["next_steps"])

            # Display success panel
            success_content = (
                "[green]Your project is now optimized for Claude Code and Claude MPM![/green]\n\n"
                "Key files:\n"
                "• [cyan]CLAUDE.md[/cyan] - Main documentation for AI agents\n"
                "  - Organized with priority rankings (🔴🟡🟢⚪)\n"
                "  - Instructions ranked by importance for AI understanding\n"
                "  - Holistic documentation review completed\n"
                "• [cyan].claude-mpm/[/cyan] - Configuration and memories\n"
                "• [cyan]CODE_STRUCTURE.md[/cyan] - AST-derived architecture documentation (if enabled)\n\n"
                "[dim]Run 'claude-mpm run' to start using the optimized setup[/dim]"
            )
            self.display.display_success_panel("Success", success_content)


@click.group(name="mpm-init", invoke_without_command=True)
@click.option(
    "--project-type",
    type=click.Choice(
        ["web", "api", "cli", "library", "mobile", "desktop", "fullstack"]
    ),
    help="Type of project to initialize",
)
@click.option(
    "--framework",
    type=str,
    help="Specific framework (e.g., react, django, fastapi, express)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force reinitialization even if project is already configured",
)
@click.option(
    "--update",
    is_flag=True,
    help="Update existing CLAUDE.md instead of recreating",
)
@click.option(
    "--review",
    is_flag=True,
    help="Review project state without making changes",
)
@click.option(
    "--organize",
    is_flag=True,
    help="Automatically organize misplaced files into proper directories",
)
@click.option(
    "--auto-safe/--no-auto-safe",
    default=True,
    help="Only move files with high confidence (default: safe mode on)",
)
@click.option(
    "--preserve-custom/--no-preserve-custom",
    default=True,
    help="Preserve custom sections when updating (default: preserve)",
)
@click.option(
    "--skip-archive",
    is_flag=True,
    help="Skip archiving existing files before updating",
)
@click.option(
    "--verbose", is_flag=True, help="Show detailed output during initialization"
)
@click.option(
    "--ast-analysis/--no-ast-analysis",
    default=True,
    help="Enable/disable AST analysis for enhanced documentation (default: enabled)",
)
@click.option(
    "--quick-update",
    is_flag=True,
    help="Perform lightweight update based on recent git activity (default: 30 days)",
)
@click.option(
    "--catchup",
    is_flag=True,
    help="Show recent commit history from all branches for PM context",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Non-interactive mode - display report only without prompting (use with --quick-update)",
)
@click.option(
    "--days",
    type=int,
    default=30,
    help="Number of days for git history analysis in quick update mode (default: 30)",
)
@click.option(
    "--export",
    type=str,
    default=None,
    help="Export activity report to file (default: docs/reports/activity-report-{timestamp}.md)",
)
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
    default=".",
)
@click.pass_context
def mpm_init(
    ctx,
    project_type,
    framework,
    force,
    update,
    review,
    organize,
    auto_safe,
    preserve_custom,
    skip_archive,
    verbose,
    ast_analysis,
    quick_update,
    catchup,
    non_interactive,
    days,
    export,
    project_path,
):
    """
    Initialize or update a project for optimal use with Claude Code and Claude MPM.

    This command uses the Agentic Coder Optimizer agent to:
    - Create or update comprehensive CLAUDE.md documentation
    - Establish single-path workflows (ONE way to do ANYTHING)
    - Configure development tools and standards
    - Set up memory systems for project knowledge
    - Optimize for AI agent understanding
    - Perform AST analysis for enhanced developer documentation

    Context Management:
    - resume: Analyze git history to provide context for resuming work
    - --catchup: Show recent commit history for PM context

    Update Mode:
    When CLAUDE.md exists, the command offers to update rather than recreate,
    preserving custom content while refreshing standard sections.

    Examples:
        claude-mpm mpm-init                           # Initialize/update current directory
        claude-mpm mpm-init --catchup                 # Show recent git history for context
        claude-mpm mpm-init --review                  # Review project state without changes
        claude-mpm mpm-init --update                  # Force update mode
        claude-mpm mpm-init --organize                # Organize misplaced files
        claude-mpm mpm-init --project-type web        # Initialize as web project
        claude-mpm mpm-init /path/to/project --force  # Force reinitialize project
    """
    # If a subcommand is being invoked, don't run the main command
    if ctx.invoked_subcommand is not None:
        return

    try:
        # Create command instance
        command = MPMInitCommand(Path(project_path))

        # Run initialization (now synchronous)
        result = command.initialize_project(
            project_type=project_type,
            framework=framework,
            force=force,
            verbose=verbose,
            ast_analysis=ast_analysis,
            update_mode=update,
            review_only=review,
            organize_files=organize,
            preserve_custom=preserve_custom,
            skip_archive=skip_archive,
            quick_update=quick_update,
            catchup=catchup,
            non_interactive=non_interactive,
            days=days,
            export=export,
        )

        # Exit with appropriate code
        if result["status"] == "success":
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Initialization cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Initialization failed: {e}[/red]")
        sys.exit(1)


@mpm_init.command(name="context")
@click.option(
    "--session-id",
    "-i",
    type=str,
    help="Unused (for compatibility) - will be removed in future version",
)
@click.option(
    "--days",
    type=int,
    default=7,
    help="Number of days of git history to analyze (default: 7)",
)
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
    default=".",
)
def context_command(session_id, days, project_path):
    """
    Provide intelligent context for resuming work based on git history.

    Analyzes recent git history and generates a Research agent delegation
    prompt for intelligent project context reconstruction.

    Examples:
        claude-mpm mpm-init context                  # Analyze last 7 days
        claude-mpm mpm-init context --days 14        # Analyze last 14 days
        claude-mpm mpm-init context --days 30        # Analyze last 30 days

    Note: 'resume' is deprecated, use 'context' instead.
    """
    try:
        command = MPMInitCommand(Path(project_path))

        result = command.handle_context(session_id=session_id, days=days)

        if result["status"] == "success" or result["status"] == "context_ready":
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Context analysis cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Context analysis failed: {e}[/red]")
        sys.exit(1)


# Add deprecated 'resume' alias for backward compatibility
@mpm_init.command(name="resume", hidden=True)
@click.option(
    "--session-id",
    "-i",
    type=str,
    help="Unused (for compatibility) - will be removed in future version",
)
@click.option(
    "--days",
    type=int,
    default=7,
    help="Number of days of git history to analyze (default: 7)",
)
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
    default=".",
)
def resume_session(session_id, days, project_path):
    """
    [DEPRECATED] Use 'context' instead.

    This command is deprecated and will be removed in a future version.
    Please use 'claude-mpm mpm-init context' instead.
    """
    console.print(
        "[yellow]⚠️  Warning: 'resume' is deprecated. Use 'context' instead.[/yellow]"
    )
    console.print("[dim]Run: claude-mpm mpm-init context[/dim]\n")

    try:
        command = MPMInitCommand(Path(project_path))
        result = command.handle_context(session_id=session_id, days=days)

        if result["status"] == "success" or result["status"] == "context_ready":
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Context analysis cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Context analysis failed: {e}[/red]")
        sys.exit(1)


# Export for CLI registration
__all__ = ["mpm_init"]
