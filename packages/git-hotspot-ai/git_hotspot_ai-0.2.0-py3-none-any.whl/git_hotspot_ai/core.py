"""
Core logic for git-hotspot-ai.

This module provides the main functionality for analyzing Git repositories to identify
code hotspots - files that have been frequently modified and are likely candidates
for refactoring, documentation, or other improvements. It integrates with AI agents
to perform various analysis tasks on the identified hotspot files.

Key features:
- Git log analysis to track file modification frequency and line changes
- Hotspot scoring algorithm based on commit count and line changes
- Integration with cursor-agent for AI-powered code analysis
- Configurable filtering and selection of top hotspot files
- Support for various analysis tasks (annotation, structure analysis, etc.)
"""

from __future__ import annotations

import dataclasses
import fnmatch
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


@dataclasses.dataclass()
class AnalyzerConfig:
    """
    Configuration class for the hotspot analyzer.
    
    This dataclass holds all the configuration parameters needed to run
    the hotspot analysis, including repository path, selection criteria,
    and AI task settings.
    
    Attributes:
        repo_path: Path to the Git repository to analyze
        top_selector: Selection criteria for top files (number or percentage)
        tasks: List of AI tasks to perform on hotspot files
        since: Optional date filter for Git log analysis (e.g., "2023-01-01")
        dry_run: If True, skip AI task execution and only show analysis results
        ignore_patterns: List of file patterns to ignore during analysis
        min_commits: Minimum number of commits required for a file to be considered
        cursor_agent_path: Path to the cursor-agent executable
        force_approve: Whether to force approval for AI agent operations
    """
    repo_path: Path
    top_selector: str
    tasks: list[str]
    since: str | None = None
    dry_run: bool = False
    ignore_patterns: list[str] | None = None
    min_commits: int = 1
    cursor_agent_path: str | None = None
    force_approve: bool = False


@dataclasses.dataclass()
class FileHotspot:
    """
    Represents a file hotspot with its modification metrics.
    
    This class encapsulates information about a file's activity level
    in the Git repository, including how many times it was committed
    and how many lines were changed.
    
    Attributes:
        path: Relative path to the file from repository root
        commit_count: Number of commits that modified this file
        line_changes: Total number of lines added and deleted
    
    Methods:
        score: Calculate a composite score for ranking hotspots
    """
    path: Path
    commit_count: int
    line_changes: int

    def score(self) -> float:
        """
        Calculate the hotspot score for ranking files.
        
        The scoring algorithm combines commit frequency and line changes
        to identify files that are both frequently modified and have
        significant code changes. The formula prioritizes commit count
        while also considering the magnitude of changes.
        
        Returns:
            A float score where higher values indicate more active files.
            The score is calculated as: commit_count + 0.1 * line_changes
        """
        return self.commit_count + 0.1 * self.line_changes


# task prompt templates for different AI analysis tasks
TASK_PROMPTS = {
    "annotate": "请为这个文件添加详细的代码注释和文档。分析代码的功能、参数、返回值，并添加适当的注释来提高代码可读性。",
    "structure": "请分析这个文件的代码结构，识别潜在的重构机会，提出改进代码组织和架构的建议。",
    "skills": "请分析这个文件需要的技能和专业知识，识别代码中使用的技术栈、设计模式和最佳实践。",
    "performance": "请分析这个文件的性能特征，识别潜在的性能瓶颈，提出优化建议和改进方案。",
    "mvp": "请基于这个文件生成 MVP（最小可行产品）建议，分析核心功能和简化方案。"
}


class HotspotAnalyzer:
    """
    Main analyzer class for identifying and processing Git code hotspots.
    
    This class orchestrates the entire hotspot analysis process, from collecting
    Git log data to dispatching AI tasks on the most active files. It provides
    a clean separation between data collection, analysis, and AI task execution.
    
    Attributes:
        config: Configuration object containing analysis parameters
        analysis_path: Resolved path to the analysis target
        repo_root: Root directory of the Git repository
        git_cwd: Working directory for Git commands
        analysis_rel: Relative path from repo root to analysis target
        cursor_agent_path: Validated path to cursor-agent executable
    """
    
    def __init__(self, config: AnalyzerConfig) -> None:
        """
        Initialize the hotspot analyzer with the given configuration.
        
        Args:
            config: Configuration object containing all analysis parameters
            
        Raises:
            SystemExit: If cursor-agent path validation fails
        """
        # store raw configuration for later use
        self.config = config
        # resolve analysis target to absolute path to avoid relative path ambiguity
        self.analysis_path = config.repo_path.resolve()
        # locate repository root using Git metadata to ensure correctness
        self.repo_root = self._resolve_repo_root(self.analysis_path)
        # git commands operate from repo root for consistent path handling
        self.git_cwd = self.repo_root
        # compute path of analysis target relative to repository root for filtering
        self.analysis_rel = self._compute_analysis_relative_path()
        # verify cursor-agent availability immediately to fail fast if misconfigured
        self.cursor_agent_path = self._validate_cursor_agent_path()

    # region public API
    def run(self) -> None:
        """
        Execute the complete hotspot analysis workflow.
        
        This method orchestrates the entire analysis process:
        1. Collect hotspot data from Git log
        2. Select top files based on configuration
        3. Print analysis summary
        4. Dispatch AI tasks (unless in dry-run mode)
        """
        hotspots = self._collect_hotspots()
        selected = self._select_top(hotspots)
        self._print_summary(hotspots, selected)
        if not self.config.dry_run:
            self._dispatch_ai_tasks(selected)

    # endregion

    # region hotspot computation
    def _collect_hotspots(self) -> list[FileHotspot]:
        """
        Collect hotspot data by analyzing Git log information.
        
        This method executes a Git log command to gather file modification
        statistics, then processes the output to calculate commit counts
        and line changes for each file. Files are filtered based on
        ignore patterns and minimum commit requirements.
        
        Returns:
            List of FileHotspot objects sorted by score in descending order
            
        Raises:
            subprocess.CalledProcessError: If Git command fails
        """
        # construct git log command with numstat for line change data
        git_cmd = ["git", "log", "--numstat", "--pretty=format:%H"]

        if self.config.since:
            git_cmd.append(f"--since={self.config.since}")

        if self.analysis_rel:
            git_cmd.extend(["--", self.analysis_rel])

        # execute git command in repository root
        result = subprocess.run(
            git_cmd,
            cwd=self.git_cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        # counters to track file statistics
        commit_counts: Counter[Path] = Counter()
        line_changes: Counter[Path] = Counter()

        # process git log output line by line
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # skip commit hash lines
            if re.fullmatch(r"[0-9a-fA-F]{40}", stripped):
                continue

            # parse numstat format: additions\tdeletions\tfilename
            parts = stripped.split("\t")
            if len(parts) != 3:
                continue
            added, deleted, filename = parts
            if not filename:
                continue
            # apply ignore patterns
            if self._should_ignore(filename):
                continue
            # filepath from git log is always repo-root relative
            rel_path = Path(filename)
            # filter by analysis scope if specified
            if self.analysis_rel and not rel_path.is_relative_to(self.analysis_rel):
                continue

            # increment commit count for this file
            commit_counts[rel_path] += 1
            # safely parse line change numbers
            additions = int(added) if added.isdigit() else 0
            deletions = int(deleted) if deleted.isdigit() else 0
            line_changes[rel_path] += additions + deletions

        # create hotspot objects and filter by minimum commits
        hotspots = [
            FileHotspot(path, commit_counts[path], line_changes[path])
            for path in commit_counts
            if commit_counts[path] >= self.config.min_commits
        ]
        # sort by score in descending order (highest activity first)
        hotspots.sort(key=lambda item: item.score(), reverse=True)
        return hotspots

    def _select_top(self, hotspots: list[FileHotspot]) -> list[FileHotspot]:
        """
        Select the top N files based on the configured selector.
        
        The selector can be either a number (e.g., "10") or a percentage
        (e.g., "20%"). The method ensures at least 1 file is selected
        even if the calculation would result in 0.
        
        Args:
            hotspots: List of all hotspots sorted by score
            
        Returns:
            List of top selected hotspots

        Raises:
            ValueError: If the selector cannot be parsed into a valid count
                or percentage value
        """
        if not hotspots:
            return []
        selector = self.config.top_selector.strip()
        if not selector:
            raise ValueError("top_selector must not be empty")

        if selector.endswith("%"):
            # percentage-based selection with explicit validation
            percentage_value = selector.rstrip("%")
            try:
                percentage = float(percentage_value)
            except ValueError as exc:
                raise ValueError(
                    f"invalid percentage selector: '{selector}'"
                ) from exc
            if percentage <= 0:
                raise ValueError("percentage selector must be positive")
            selection_size = int(len(hotspots) * (percentage / 100.0))
        else:
            # absolute number selection with explicit validation
            try:
                selection_size = int(selector)
            except ValueError as exc:
                raise ValueError(
                    f"invalid numeric selector: '{selector}'"
                ) from exc
            if selection_size <= 0:
                raise ValueError("numeric selector must be positive")

        if selection_size < 1:
            selection_size = 1
        if selection_size > len(hotspots):
            selection_size = len(hotspots)
        return hotspots[:selection_size]

    # endregion

    # region reporting & AI dispatch
    def _print_summary(
        self,
        hotspots: list[FileHotspot],
        selected: list[FileHotspot],
    ) -> None:
        """display a detailed summary of the analysis results.

        Args:
            hotspots: complete hotspot ranking generated from git history
            selected: subset of hotspots chosen for AI task execution
        """
        print("=" * 80)
        print("🔥 Git Hotspot Analysis Report")
        print("=" * 80)
        print(f"📁 Repository: {self.repo_root}")
        if self.analysis_rel:
            print(f"📂 Analysis Scope: {self.analysis_rel}")
        if self.config.since:
            print(f"📅 Time Filter: since {self.config.since}")
        if self.config.ignore_patterns:
            print(f"🚫 Ignored Patterns: {', '.join(self.config.ignore_patterns)}")
        print(f"📊 Minimum Commits: {self.config.min_commits}")
        print()
        
        # show complete data collection summary
        print("📈 Data Collection Summary:")
        print(f"   • Total files analyzed: {len(hotspots)}")
        print(f"   • Files selected for AI analysis: {len(selected)}")
        print(f"   • Selection criteria: {self.config.top_selector}")
        print()
        
        # show all hotspot files with detailed metrics
        if hotspots:
            print("📋 Complete Hotspot Ranking:")
            print("-" * 80)
            print(f"{'Rank':<6} {'File Path':<50} {'Commits':<8} {'Lines':<10} {'Score':<8}")
            print("-" * 80)
            
            for idx, item in enumerate(hotspots, start=1):
                # highlight selected files
                marker = "🎯" if item in selected else "  "
                print(f"{marker}{idx:>3}. {str(item.path):<50} {item.commit_count:>6} {item.line_changes:>8} {item.score():>6.1f}")
            print("-" * 80)
        
        # show selected files for AI analysis
        if selected:
            print()
            print("🎯 Selected Files for AI Analysis:")
            print("-" * 60)
            for idx, item in enumerate(selected, start=1):
                print(f"{idx:>3}. {item.path}")
                print(f"     📊 Metrics: {item.commit_count} commits, {item.line_changes} line changes, score: {item.score():.1f}")
            print("-" * 60)
        
        # show task information
        if not self.config.dry_run and selected:
            print()
            print("🤖 AI Tasks to Execute:")
            for task in self.config.tasks:
                task_desc = TASK_PROMPTS.get(task, "Unknown task")
                print(f"   • {task}: {task_desc[:60]}...")
        
        if self.config.dry_run:
            print()
            print("🔍 (Dry-run mode: AI tasks will be skipped)")
        
        print("=" * 80)

    def _dispatch_ai_tasks(self, files: list[FileHotspot]) -> None:
        """
        Dispatch AI analysis tasks for the selected hotspot files.
        
        This method orchestrates the execution of all configured AI tasks
        on each selected hotspot file. It provides detailed progress tracking
        and error handling to ensure robust execution even if individual
        tasks fail.
        
        Args:
            files: List of hotspot files to process with AI tasks
        """
        if not files:
            print("\n⚠️  No files selected for AI analysis.")
            return
        
        total_files = len(files)
        total_tasks = len(self.config.tasks) * total_files
        
        print(f"\n🚀 Starting AI Analysis...")
        print(f"📊 Progress Overview: {total_files} files × {len(self.config.tasks)} tasks = {total_tasks} total operations")
        print("=" * 80)
        
        completed_tasks = 0
        
        # process each file with all configured tasks
        for file_idx, hotspot in enumerate(files, 1):
            print(f"\n📄 Processing File {file_idx}/{total_files}: {hotspot.path}")
            print(f"   📊 File Metrics: {hotspot.commit_count} commits, {hotspot.line_changes} line changes, score: {hotspot.score():.1f}")
            
            file_tasks_completed = 0
            file_tasks_total = len(self.config.tasks)
            
            # execute each task for the current file
            for task_idx, task in enumerate(self.config.tasks, 1):
                if task not in TASK_PROMPTS:
                    print(f"   ⚠️  Task {task_idx}/{file_tasks_total}: Unknown task '{task}', skipping...")
                    continue
                
                print(f"   🤖 Task {task_idx}/{file_tasks_total}: {task}")
                
                try:
                    success = self._invoke_cursor_agent_for_task(str(self.repo_root / hotspot.path), task, hotspot)
                    if success:
                        file_tasks_completed += 1
                        completed_tasks += 1
                        print(f"      ✅ Completed successfully")
                    else:
                        print(f"      ❌ Failed")
                except Exception as e:
                    print(f"      💥 Error: {e}")
                
                # show overall progress
                progress_pct = (completed_tasks / total_tasks) * 100
                print(f"      📈 Overall Progress: {completed_tasks}/{total_tasks} ({progress_pct:.1f}%)")
            
            # file completion summary
            file_success_rate = (file_tasks_completed / file_tasks_total) * 100 if file_tasks_total > 0 else 0
            print(f"   📋 File Summary: {file_tasks_completed}/{file_tasks_total} tasks completed ({file_success_rate:.1f}%)")
        
        # final summary
        print("\n" + "=" * 80)
        print("🎉 AI Analysis Complete!")
        final_success_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        print(f"📊 Final Results: {completed_tasks}/{total_tasks} tasks completed ({final_success_rate:.1f}%)")
        print("=" * 80)


    def _invoke_cursor_agent_for_task(self, file_path: str, task: str, hotspot: FileHotspot) -> bool:
        """
        Invoke cursor-agent for a specific task on a file.
        
        Args:
            file_path: Full path to the file to analyze
            task: The AI task to perform (annotate, structure, etc.)
            hotspot: FileHotspot object containing file metrics
            
        Returns:
            bool: True if the task completed successfully, False otherwise
        """
        
        prompt = self._build_task_prompt(file_path, task, hotspot)
        
        # construct cursor-agent command
        cmd = [
            self.cursor_agent_path,
            "--print",  # print responses to console for non-interactive use
        ]
        
        # add --force flag only if explicitly requested and allowed
        if self.config.force_approve:
            cmd.append("--force")
        
        cmd.append(prompt)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout for safety
                check=False  # don't raise exception on non-zero exit
            )
            
            if result.returncode == 0:
                if result.stdout.strip():
                    # show a preview of the output
                    output_preview = result.stdout.strip()[:150]
                    if len(result.stdout.strip()) > 150:
                        output_preview += "..."
                    print(f"      💬 Output: {output_preview}")
                return True
            else:
                if result.stderr.strip():
                    error_msg = result.stderr.strip()[:100]
                    if len(result.stderr.strip()) > 100:
                        error_msg += "..."
                    print(f"      🚨 Error (code {result.returncode}): {error_msg}")
                return False
                    
        except subprocess.TimeoutExpired:
            print(f"      ⏰ Task timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"      💥 Exception: {str(e)[:100]}")
            return False

    def _build_task_prompt(self, file_path: str, task: str, hotspot: FileHotspot) -> str:
        """
        Build a comprehensive prompt for cursor-agent based on task type and file metrics.
        
        This method constructs a detailed prompt that includes file context,
        Git activity metrics, and the specific task instructions. The prompt
        is designed to provide the AI agent with all necessary information
        to perform high-quality analysis.
        
        Args:
            file_path: Full path to the file to analyze
            task: The AI task to perform (must exist in TASK_PROMPTS)
            hotspot: FileHotspot object containing file activity metrics
            
        Returns:
            Formatted prompt string for the cursor-agent
        """
        base_prompt = TASK_PROMPTS[task]
        
        context = f"""
文件路径: {file_path}
Git 热点指标:
- 提交次数: {hotspot.commit_count}
- 代码变更行数: {hotspot.line_changes}
- 热点评分: {hotspot.score():.1f}

{base_prompt}

请分析文件 {file_path} 并提供相应的建议。
"""
        return context.strip()

    # endregion

    # region helpers
    def _should_ignore(self, filename: str) -> bool:
        """
        Check if a filename should be ignored based on configured patterns.
        
        This method applies glob pattern matching to determine if a file
        should be excluded from hotspot analysis based on the ignore_patterns
        configuration.
        
        Args:
            filename: The filename to check against ignore patterns
            
        Returns:
            True if the file should be ignored, False otherwise
        """
        patterns = self.config.ignore_patterns or []
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def _resolve_repo_root(self, path: Path) -> Path:
        """
        Resolve the Git repository root directory from a given path.
        
        This method uses Git's rev-parse command to find the repository
        root, which is more reliable than filesystem traversal.
        
        Args:
            path: Path within the repository to start from
            
        Returns:
            Path object representing the repository root directory
            
        Raises:
            subprocess.CalledProcessError: If the path is not within a Git repository
        """
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())

    def _compute_analysis_relative_path(self) -> str | None:
        """
        Compute the relative path from repository root to analysis target.
        
        This method calculates the relative path between the repository root
        and the analysis target path. If they are the same, returns None
        to indicate analysis should cover the entire repository.
        
        Returns:
            Relative path string if analysis is scoped to a subdirectory,
            None if analyzing the entire repository
        """
        if self.analysis_path == self.repo_root:
            return None
        return str(self.analysis_path.relative_to(self.repo_root))

    def _validate_cursor_agent_path(self) -> str:
        """validate and return cursor-agent executable path"""
        # first check if provided in config
        if self.config.cursor_agent_path:
            cursor_path = self.config.cursor_agent_path
        else:
            # check environment variable
            cursor_path = os.environ.get("CURSOR_AGENT_PATH")
        
        if not cursor_path:
            print("Error: CURSOR_AGENT_PATH environment variable is not set!")
            print("Please set the environment variable to point to your cursor-agent executable:")
            print("  export CURSOR_AGENT_PATH=/path/to/cursor-agent")
            print("  # or")
            print("  export CURSOR_AGENT_PATH=$(which cursor-agent)")
            sys.exit(1)
        
        # check if the path exists and is executable
        cursor_path_obj = Path(cursor_path)
        if not cursor_path_obj.exists():
            print(f"Error: cursor-agent not found at: {cursor_path}")
            print("Please check your CURSOR_AGENT_PATH environment variable.")
            sys.exit(1)
        
        if not cursor_path_obj.is_file():
            print(f"Error: {cursor_path} is not a file")
            sys.exit(1)
        
        # try to verify it's actually cursor-agent by running --version
        try:
            result = subprocess.run(
                [cursor_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            if result.returncode != 0:
                print(f"Warning: {cursor_path} may not be a valid cursor-agent executable")
                print(f"Version check failed with return code: {result.returncode}")
        except Exception as e:
            print(f"Warning: Could not verify cursor-agent executable: {e}")
        
        return cursor_path

    # endregion
