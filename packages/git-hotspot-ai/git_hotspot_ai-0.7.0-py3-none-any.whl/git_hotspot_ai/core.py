"""
Git热点分析工具的核心逻辑模块

该模块提供了分析Git仓库以识别代码热点的核心功能。代码热点是指频繁修改的文件，
这些文件通常是重构、文档化或其他改进的候选目标。该模块集成了AI代理，
对识别出的热点文件执行各种分析任务。

主要功能特性:
- Git日志分析：跟踪文件修改频率和代码行变更
- 热点评分算法：基于提交次数和代码行变更计算评分
- 与cursor-agent集成：提供AI驱动的代码分析
- 可配置的过滤和选择：筛选出顶级热点文件
- 支持多种分析任务：注释、结构分析、性能分析等
"""

from __future__ import annotations

import dataclasses
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Iterable


@dataclasses.dataclass()
class AnalyzerConfig:
    """
    热点分析器的配置类

    该dataclass类封装了控制仓库检查和下游AI任务执行的所有运行时参数。
    通过配置这些参数，可以灵活控制分析行为。

    属性说明:
        repo_path: 指向Git仓库根目录的绝对或相对路径
        top_selector: 热点文件选择策略，接受整数字符串或百分比字符串
        tasks: 对选中文件执行的任务标识符的有序列表
        since: 可选的ISO-8601日期字符串，传递给Git的--since参数
        dry_run: 为true时跳过cursor-agent调用，但仍生成报告
        ignore_patterns: shell风格的glob模式，用于跳过匹配的文件
        min_commits: 文件包含在热点列表中的最小提交次数阈值
        cursor_agent_path: cursor-agent二进制文件的显式路径，覆盖环境变量发现
        force_approve: 当需要绕过审批时，向cursor-agent添加--force参数
        task_prompt_overrides: 任务标识符到自定义提示文本的映射
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
    task_prompt_overrides: dict[str, str] | None = None


class ProcessingCache:
    """
    file processing cache manager
    
    this class manages a cache file that tracks which files have been processed
    by AI tasks. it helps avoid redundant processing by keeping a record of
    completed files and their associated tasks.
    
    attributes:
        cache_path: path to the cache file in the repository
        cache_data: dictionary storing file processing information
    """

    def __init__(self, repo_root: Path) -> None:
        """
        initialize the cache manager
        
        args:
            repo_root: root directory of the git repository
        """
        self.cache_path = repo_root / ".git_hotspot_cache"
        self.cache_data: dict[str, dict] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """load cache data from file if it exists"""
        if not self.cache_path.exists():
            return
        
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                self.cache_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  warning: failed to load cache file, starting fresh: {e}")
            self.cache_data = {}

    def _save_cache(self) -> None:
        """save cache data to file"""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"⚠️  warning: failed to save cache file: {e}")

    def is_processed(self, file_path: str, tasks: list[str]) -> bool:
        """
        check if a file has been processed with all specified tasks
        
        args:
            file_path: relative path to the file
            tasks: list of task identifiers to check
        
        returns:
            bool: true if all tasks have been completed for this file
        """
        if file_path not in self.cache_data:
            return False
        
        cached_tasks = self.cache_data[file_path].get("tasks_completed", [])
        return all(task in cached_tasks for task in tasks)

    def mark_processed(self, file_path: str, tasks: list[str]) -> None:
        """
        mark a file as processed with specified tasks
        
        args:
            file_path: relative path to the file
            tasks: list of task identifiers that were completed
        """
        if file_path not in self.cache_data:
            self.cache_data[file_path] = {
                "tasks_completed": [],
                "first_processed": time.time(),
            }
        
        existing_tasks = set(self.cache_data[file_path].get("tasks_completed", []))
        existing_tasks.update(tasks)
        self.cache_data[file_path]["tasks_completed"] = list(existing_tasks)
        self.cache_data[file_path]["last_processed"] = time.time()
        
        self._save_cache()

    def get_stats(self) -> dict:
        """
        get cache statistics
        
        returns:
            dict: statistics about cached files
        """
        return {
            "total_files": len(self.cache_data),
            "cache_path": str(self.cache_path),
        }


@dataclasses.dataclass()
class FileHotspot:
    """
    表示文件热点及其修改指标的数据类

    该dataclass类捕获了在热点分析期间对文件进行排名所需的活动信号，
    并提供了用于排序的评分辅助方法。

    属性说明:
        path: Git在git log输出中产生的仓库相对文件路径
        commit_count: 在检查窗口内触及该文件的提交次数
        line_changes: 从--numstat收集的添加和删除行的聚合数量

    方法说明:
        score: 计算用于热点排名的综合评分
    """

    path: Path
    commit_count: int
    line_changes: int

    def score(self) -> float:
        """
        计算文件的热点评分用于排名

        评分公式综合考虑了提交频率和代码变更量，其中提交次数权重更高，
        因为频繁修改通常比大量修改更能反映代码的活跃度。

        Returns:
            float: 综合评分值，定义为commit_count + 0.1 * line_changes。
                更高的值反映更频繁或更大的变更，将文件推向热点排序的顶部。
        """
        return self.commit_count + 0.1 * self.line_changes


# 不同AI分析任务的任务提示模板
# 这些模板定义了各种分析任务的具体指令，用于指导AI对热点文件进行分析
TASK_PROMPTS = {
    "annotate": "请为这个文件添加详细的代码注释和文档。分析代码的功能、参数、返回值，并添加适当的注释来提高代码可读性。",
    "structure": "请分析这个文件的代码结构，识别潜在的重构机会，提出改进代码组织和架构的建议。",
    "skills": "请分析这个文件需要的技能和专业知识，识别代码中使用的技术栈、设计模式和最佳实践。",
    "performance": "请分析这个文件的性能特征，识别潜在的性能瓶颈，提出优化建议和改进方案。",
    "mvp": "请基于这个文件生成 MVP（最小可行产品）建议，分析核心功能和简化方案。",
}


class HotspotAnalyzer:
    """
    用于识别和处理Git代码热点的主要分析器类

    该类协调整个热点分析流程，从收集Git日志数据到在最活跃的文件上分派AI任务。
    它在数据收集、分析和AI任务执行之间提供了清晰的分离。

    属性说明:
        config: 包含分析参数的配置对象
        analysis_path: 分析目标的解析路径
        repo_root: Git仓库的根目录
        git_cwd: Git命令的工作目录
        analysis_rel: 从仓库根目录到分析目标的相对路径
        cursor_agent_path: 经过验证的cursor-agent可执行文件路径
    """

    def __init__(self, config: AnalyzerConfig) -> None:
        """
        使用给定配置初始化热点分析器

        该方法会验证配置参数，解析路径，并确保cursor-agent可执行文件可用。
        如果验证失败，会立即退出程序以避免后续运行时错误。

        Args:
            config: 完全填充的AnalyzerConfig实例，控制运行时行为

        Raises:
            SystemExit: 当cursor-agent验证无法确认可执行文件路径时
        """
        # 存储原始配置以供后续使用
        self.config = config
        # 将分析目标解析为绝对路径，避免相对路径歧义
        self.analysis_path = config.repo_path.resolve()
        # 使用Git元数据定位仓库根目录，确保正确性
        self.repo_root = self._resolve_repo_root(self.analysis_path)
        # Git命令从仓库根目录操作，确保路径处理的一致性
        self.git_cwd = self.repo_root
        # 计算分析目标相对于仓库根目录的路径，用于过滤
        self.analysis_rel = self._compute_analysis_relative_path()
        # 立即验证cursor-agent可用性，如果配置错误则快速失败
        self.cursor_agent_path = self._validate_cursor_agent_path()
        # initialize processing cache for tracking processed files
        self.processing_cache = ProcessingCache(self.repo_root)

    # region public API
    def run(self) -> None:
        """
        执行完整的热点分析工作流程

        该方法按顺序协调数据收集、选择、报告和可选的AI执行。
        每个阶段都依赖辅助方法，使控制流程保持易于审计。

        Returns:
            None.
        """
        # 收集所有热点文件数据
        hotspots = self._collect_hotspots()
        # 根据配置选择顶级热点文件
        selected = self._select_top(hotspots)
        # 打印分析摘要报告
        self._print_summary(hotspots, selected)
        # 如果不是试运行模式，则分派AI任务
        if not self.config.dry_run:
            self._dispatch_ai_tasks(selected)

    # endregion

    # region hotspot computation
    def _collect_hotspots(self) -> list[FileHotspot]:
        """
        通过分析Git日志信息收集热点数据

        该方法执行git log命令获取文件修改历史，解析numstat输出计算每个文件的
        提交次数和代码行变更，然后根据评分对文件进行排序。

        Returns:
            list[FileHotspot]: 在仓库范围内发现的热点文件排序列表（按评分降序）

        Raises:
            subprocess.CalledProcessError: 当Git无法成功执行时传播异常
        """
        # 构建git log命令，使用numstat获取代码行变更数据
        git_cmd = ["git", "log", "--numstat", "--pretty=format:%H"]

        # 如果指定了时间范围，添加--since参数
        if self.config.since:
            git_cmd.append(f"--since={self.config.since}")

        # 如果指定了分析范围，限制到特定目录
        if self.analysis_rel:
            git_cmd.extend(["--", self.analysis_rel])

        # 在仓库根目录执行git命令
        result = subprocess.run(
            git_cmd,
            cwd=self.git_cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        # 用于跟踪文件统计数据的计数器
        commit_counts: Counter[Path] = Counter()
        line_changes: Counter[Path] = Counter()

        # 逐行处理git log输出
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # 跳过提交哈希行
            if re.fullmatch(r"[0-9a-fA-F]{40}", stripped):
                continue

            # 解析numstat格式：添加行数\t删除行数\t文件名
            parts = stripped.split("\t")
            if len(parts) != 3:
                continue
            added, deleted, filename = parts
            if not filename:
                continue
            # 标准化文件名，处理重命名等情况
            normalized_filename = self._normalize_git_filename(filename)
            if not normalized_filename:
                continue
            # 检查是否应该忽略此文件
            if self._should_ignore(normalized_filename):
                continue
            rel_path = Path(normalized_filename)
            # 如果指定了分析范围，过滤文件
            if self.analysis_rel and not rel_path.is_relative_to(self.analysis_rel):
                continue

            # 增加此文件的提交计数
            commit_counts[rel_path] += 1
            # 安全解析代码行变更数字；二进制差异使用'-'，应视为零
            additions = int(added) if added.isdigit() else 0
            deletions = int(deleted) if deleted.isdigit() else 0
            line_changes[rel_path] += additions + deletions

        # 创建热点对象并按最小提交次数过滤
        hotspots = [
            FileHotspot(path, commit_counts[path], line_changes[path])
            for path in commit_counts
            if commit_counts[path] >= self.config.min_commits
        ]
        # 按评分降序排序，使下游选择保持简单
        hotspots.sort(key=lambda item: item.score(), reverse=True)
        return hotspots

    def _select_top(self, hotspots: list[FileHotspot]) -> list[FileHotspot]:
        """
        根据配置的选择器选择顶级文件

        支持两种选择模式：
        1. 绝对数量：如"10"表示选择前10个文件
        2. 百分比：如"20%"表示选择前20%的文件

        Args:
            hotspots: 按评分排序的所有热点文件列表

        Returns:
            list[FileHotspot]: 从top_selector派生的热点文件选择

        Raises:
            ValueError: 如果选择器无法解析为有效的数量或百分比值
        """
        # 如果没有热点文件，返回空列表
        if not hotspots:
            return []
        selector = self.config.top_selector.strip()
        if not selector:
            raise ValueError("top_selector must not be empty")

        if selector.endswith("%"):
            # 基于百分比的选择，带显式验证
            percentage_value = selector.rstrip("%")
            try:
                percentage = float(percentage_value)
            except ValueError as exc:
                raise ValueError(f"invalid percentage selector: '{selector}'") from exc
            if percentage <= 0:
                raise ValueError("percentage selector must be positive")
            selection_size = int(len(hotspots) * (percentage / 100.0))
        else:
            # 绝对数量选择，带显式验证
            try:
                selection_size = int(selector)
            except ValueError as exc:
                raise ValueError(f"invalid numeric selector: '{selector}'") from exc
            if selection_size <= 0:
                raise ValueError("numeric selector must be positive")

        # 确保选择大小在有效范围内
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
        """显示分析结果的详细摘要

        该方法生成格式化的分析报告，包括：
        - 分析配置信息
        - 数据收集统计
        - 完整的热点文件排名表
        - 选中的文件列表
        - 待执行的AI任务信息

        Args:
            hotspots: 从git历史生成的完整热点文件排名
            selected: 为AI任务执行选择的热点文件子集

        Returns:
            None.
        """
        # 打印报告头部信息
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
        
        # display cache statistics
        cache_stats = self.processing_cache.get_stats()
        print(f"💾 Cache: {cache_stats['total_files']} files tracked in {cache_stats['cache_path']}")
        print()

        # 显示完整的数据收集摘要
        print("📈 Data Collection Summary:")
        print(f"   • Total files analyzed: {len(hotspots)}")
        print(f"   • Files selected for AI analysis: {len(selected)}")
        print(f"   • Selection criteria: {self.config.top_selector}")
        print()

        # 显示所有热点文件的详细指标
        if hotspots:
            print("📋 Complete Hotspot Ranking:")
            print("-" * 80)
            print(
                f"{'Rank':<6} {'File Path':<50} {'Commits':<8} {'Lines':<10} {'Score':<8}"
            )
            print("-" * 80)

            for idx, item in enumerate(hotspots, start=1):
                # 在表格中高亮显示选中的文件，便于快速扫描
                marker = "🎯" if item in selected else "  "
                print(
                    f"{marker}{idx:>3}. {str(item.path):<50} {item.commit_count:>6} {item.line_changes:>8} {item.score():>6.1f}"
                )
            print("-" * 80)

        # 显示为AI分析选中的文件
        if selected:
            print()
            print("🎯 Selected Files for AI Analysis:")
            print("-" * 60)
            for idx, item in enumerate(selected, start=1):
                print(f"{idx:>3}. {item.path}")
                print(
                    f"     📊 Metrics: {item.commit_count} commits, {item.line_changes} line changes, score: {item.score():.1f}"
                )
            print("-" * 60)

        # 显示任务信息
        if not self.config.dry_run and selected:
            print()
            print("🤖 AI Tasks to Execute:")
            for task in self.config.tasks:
                try:
                    task_desc = self._resolve_task_prompt(task)
                except KeyError:
                    task_desc = "task prompt not defined"
                print(f"   • {task}: {task_desc[:60]}...")

        if self.config.dry_run:
            print()
            print("🔍 (Dry-run mode: AI tasks will be skipped)")

        print("=" * 80)

    def _dispatch_ai_tasks(self, files: list[FileHotspot]) -> None:
        """
        为选中的热点文件分派AI分析任务

        该方法协调所有配置的AI任务在每个选中的热点文件上的执行。
        它提供详细的进度跟踪和错误处理，确保即使个别任务失败也能稳健执行。

        Args:
            files: 要用AI任务处理的热点文件列表
        """
        if not files:
            print("\n⚠️  No files selected for AI analysis.")
            return

        # filter out already processed files based on cache
        files_to_process: list[FileHotspot] = []
        skipped_files: list[FileHotspot] = []
        
        for hotspot in files:
            file_path_str = str(hotspot.path)
            if self.processing_cache.is_processed(file_path_str, self.config.tasks):
                skipped_files.append(hotspot)
            else:
                files_to_process.append(hotspot)

        # print information about skipped files
        if skipped_files:
            print(f"\n⏭️  Skipping {len(skipped_files)} already processed file(s):")
            print("=" * 80)
            for idx, hotspot in enumerate(skipped_files, 1):
                print(f"   {idx}. {hotspot.path}")
                print(f"      📊 Metrics: {hotspot.commit_count} commits, {hotspot.line_changes} line changes")
                cached_info = self.processing_cache.cache_data.get(str(hotspot.path), {})
                completed_tasks = cached_info.get("tasks_completed", [])
                print(f"      ✅ Completed tasks: {', '.join(completed_tasks)}")
            print("=" * 80)

        if not files_to_process:
            print("\n✅ All selected files have already been processed!")
            return

        total_files = len(files_to_process)
        total_tasks = len(self.config.tasks) * total_files

        print(f"\n🚀 Starting AI Analysis...")
        print(
            f"📊 Progress Overview: {total_files} files × {len(self.config.tasks)} tasks = {total_tasks} total operations"
        )
        if skipped_files:
            print(f"   ({len(skipped_files)} file(s) skipped from cache)")
        print("=" * 80)

        completed_tasks = 0

        # process each file with all configured tasks
        for file_idx, hotspot in enumerate(files_to_process, 1):
            print(f"\n📄 Processing File {file_idx}/{total_files}: {hotspot.path}")
            print(
                f"   📊 File Metrics: {hotspot.commit_count} commits, {hotspot.line_changes} line changes, score: {hotspot.score():.1f}"
            )

            file_tasks_completed = 0
            file_tasks_total = len(self.config.tasks)
            successfully_completed_tasks: list[str] = []

            # execute each task for the current file
            for task_idx, task in enumerate(self.config.tasks, 1):
                if not self._has_task_prompt(task):
                    print(
                        f"   ⚠️  Task {task_idx}/{file_tasks_total}: Unknown task '{task}', skipping..."
                    )
                    continue

                print(f"   🤖 Task {task_idx}/{file_tasks_total}: {task}")

                try:
                    success = self._invoke_cursor_agent_for_task(
                        str(self.repo_root / hotspot.path), task, hotspot
                    )
                    if success:
                        file_tasks_completed += 1
                        completed_tasks += 1
                        successfully_completed_tasks.append(task)
                        print(f"      ✅ Completed successfully")
                    else:
                        print(f"      ❌ Failed")
                except Exception as e:
                    print(f"      💥 Error: {e}")

                # show overall progress; protect against division by zero indirectly by checking total_tasks earlier
                progress_pct = (completed_tasks / total_tasks) * 100
                print(
                    f"      📈 Overall Progress: {completed_tasks}/{total_tasks} ({progress_pct:.1f}%)"
                )

            # update cache with successfully completed tasks
            if successfully_completed_tasks:
                file_path_str = str(hotspot.path)
                self.processing_cache.mark_processed(file_path_str, successfully_completed_tasks)
                print(f"   💾 Cache updated for {len(successfully_completed_tasks)} completed task(s)")

            # file completion summary
            file_success_rate = (
                (file_tasks_completed / file_tasks_total) * 100
                if file_tasks_total > 0
                else 0
            )
            print(
                f"   📋 File Summary: {file_tasks_completed}/{file_tasks_total} tasks completed ({file_success_rate:.1f}%)"
            )

        # final summary
        print("\n" + "=" * 80)
        print("🎉 AI Analysis Complete!")
        final_success_rate = (
            (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        )
        print(
            f"📊 Final Results: {completed_tasks}/{total_tasks} tasks completed ({final_success_rate:.1f}%)"
        )
        if skipped_files:
            print(f"   ({len(skipped_files)} file(s) were skipped from cache)")
        print("=" * 80)

    def _invoke_cursor_agent_for_task(
        self, file_path: str, task: str, hotspot: FileHotspot
    ) -> bool:
        """
        Invoke cursor-agent for a specific task on a file.

        Args:
            file_path: Absolute path string for the file passed to cursor-agent.
            task: Task identifier expected to exist inside ``TASK_PROMPTS``.
            hotspot: Metrics instance providing contextual information for the prompt.

        Returns:
            bool: ``True`` when cursor-agent exits successfully, ``False`` otherwise.
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
                timeout=3000,  # 3000 seconds timeout for safety
                check=False,  # don't raise exception on non-zero exit
            )

            if result.returncode == 0:
                if result.stdout.strip():
                    # show a preview of the output so the operator can skim without opening separate tools
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

    def _build_task_prompt(
        self, file_path: str, task: str, hotspot: FileHotspot
    ) -> str:
        """
        Build a comprehensive prompt for cursor-agent based on task type and file metrics.

        Args:
            file_path: Absolute path string to include inside the AI context block.
            task: Key that maps to the stored Chinese-language instructions.
            hotspot: Activity data to embed inside the generated prompt.

        Returns:
            str: Fully formatted prompt string assembled for cursor-agent consumption.
        """
        base_prompt = self._resolve_task_prompt(task)

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

    def _resolve_task_prompt(self, task: str) -> str:
        """resolve prompt text for a task identifier."""
        overrides = self.config.task_prompt_overrides or {}
        if task in overrides:
            return overrides[task]
        if task in TASK_PROMPTS:
            return TASK_PROMPTS[task]
        raise KeyError(task)

    def _has_task_prompt(self, task: str) -> bool:
        """check whether a prompt is defined for the given task."""
        overrides = self.config.task_prompt_overrides or {}
        if task in overrides:
            return True
        return task in TASK_PROMPTS

    # endregion

    # region helpers
    def _should_ignore(self, filename: str) -> bool:
        """
        Check if a filename should be ignored based on configured patterns.

        Args:
            filename: Repo-relative path string extracted from ``git log`` output.

        Returns:
            bool: ``True`` when any ignore pattern matches the file, otherwise ``False``.
        """
        patterns = self.config.ignore_patterns or []
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def _normalize_git_filename(self, raw_filename: str) -> str | None:
        """normalize filename tokens emitted by git numstat output."""
        candidate = raw_filename.strip()
        if not candidate:
            return None

        if " => " not in candidate:
            return candidate

        brace_pattern = re.compile(r"\{([^{}]+?) => ([^{}]+?)\}")
        previous = None
        normalized = candidate

        while previous != normalized:
            previous = normalized
            normalized = brace_pattern.sub(lambda match: match.group(2), normalized)

        if " => " in normalized:
            normalized_segments = normalized.split(" => ")
            normalized = normalized_segments[-1]

        normalized = normalized.strip()
        if not normalized:
            return None
        return normalized

    def _resolve_repo_root(self, path: Path) -> Path:
        """
        Resolve the Git repository root directory from a given path.

        Args:
            path: Path within the repository to start from.

        Returns:
            Path: Repository root produced by ``git rev-parse --show-toplevel``.

        Raises:
            subprocess.CalledProcessError: If the path is not within a Git repository
        """
        # rely on git metadata instead of manual parent traversal to avoid false positives
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

        Returns:
            str | None: Relative subpath when restricting analysis, otherwise ``None``.
        """
        if self.analysis_path == self.repo_root:
            return None
        return str(self.analysis_path.relative_to(self.repo_root))

    def _validate_cursor_agent_path(self) -> str:
        """Validate and return cursor-agent executable path.

        Returns:
            str: Verified file-system path pointing to the cursor-agent executable.

        Raises:
            SystemExit: When the path cannot be discovered or verified as a file.
        """
        # first check if provided in config
        if self.config.cursor_agent_path:
            cursor_path = self.config.cursor_agent_path
        else:
            # check environment variable
            cursor_path = os.environ.get("CURSOR_AGENT_PATH")

        if not cursor_path:
            print("Error: CURSOR_AGENT_PATH environment variable is not set!")
            print(
                "Please set the environment variable to point to your cursor-agent executable:"
            )
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
                check=False,
            )
            if result.returncode != 0:
                print(
                    f"Warning: {cursor_path} may not be a valid cursor-agent executable"
                )
                print(f"Version check failed with return code: {result.returncode}")
        except Exception as e:
            print(f"Warning: Could not verify cursor-agent executable: {e}")

        return cursor_path

    # endregion
