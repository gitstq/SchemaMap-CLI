"""
TUI仪表盘模块

美观的终端交互界面，用于展示Schema分析结果。
使用纯Python标准库实现，零外部依赖。

纯Python标准库实现，零外部依赖。
"""

import shutil
import sys
from typing import List, Dict, Optional, Any

from ..detector.change_detector import SchemaDiff, ChangeType
from ..analyzer.impact_analyzer import ImpactReport, RiskLevel, ImpactCategory
from ..generator.migration_generator import MigrationScript


class Colors:
    """终端颜色代码"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # 背景色
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # 亮色
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


class DashboardRenderer:
    """
    TUI仪表盘渲染器

    在终端中渲染美观的Schema分析结果。
    """

    def __init__(self, use_color: bool = True):
        self.use_color = use_color and self._supports_color()
        self.term_width = self._get_terminal_width()

    def _supports_color(self) -> bool:
        """检查终端是否支持颜色"""
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def _get_terminal_width(self) -> int:
        """获取终端宽度"""
        try:
            return shutil.get_terminal_size().columns
        except Exception:
            return 80

    def _color(self, text: str, color: str) -> str:
        """为文本添加颜色"""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text

    def _bold(self, text: str) -> str:
        """加粗文本"""
        return self._color(text, Colors.BOLD)

    def _hr(self, char: str = "-", color: str = "") -> str:
        """水平分隔线"""
        line = char * self.term_width
        if color:
            return self._color(line, color)
        return line

    def _center(self, text: str, width: Optional[int] = None) -> str:
        """居中文本"""
        if width is None:
            width = self.term_width
        return text.center(width)

    def _box(self, title: str, content: List[str], width: Optional[int] = None) -> str:
        """绘制带标题的方框"""
        if width is None:
            width = min(self.term_width - 4, 76)

        lines = []
        top = f"┌{'─' * (width - 2)}┐"
        lines.append(self._color(top, Colors.CYAN))

        title_line = f"│ {self._bold(title):<{width - 3}}│"
        lines.append(self._color(title_line, Colors.CYAN))

        sep = f"├{'─' * (width - 2)}┤"
        lines.append(self._color(sep, Colors.CYAN))

        for line in content:
            # 截断或换行
            if len(line) > width - 4:
                line = line[:width - 7] + "..."
            formatted = f"│ {line:<{width - 3}}│"
            lines.append(self._color(formatted, Colors.CYAN))

        bottom = f"└{'─' * (width - 2)}┘"
        lines.append(self._color(bottom, Colors.CYAN))

        return "\n".join(lines)

    def _badge(self, text: str, color: str) -> str:
        """创建徽章标签"""
        return self._color(f"[{text}]", color)

    def _risk_badge(self, risk_level: RiskLevel) -> str:
        """风险等级徽章"""
        color_map = {
            RiskLevel.HIGH: Colors.BG_RED + Colors.WHITE,
            RiskLevel.MEDIUM: Colors.BG_YELLOW + Colors.BLACK,
            RiskLevel.LOW: Colors.BG_GREEN + Colors.BLACK,
            RiskLevel.INFO: Colors.BG_BLUE + Colors.WHITE,
        }
        return self._color(f" {risk_level.value.upper()} ", color_map.get(risk_level, Colors.BG_BLUE))

    def _change_type_badge(self, change_type: ChangeType) -> str:
        """变更类型徽章"""
        color_map = {
            ChangeType.ADDED: Colors.BRIGHT_GREEN,
            ChangeType.REMOVED: Colors.BRIGHT_RED,
            ChangeType.MODIFIED: Colors.BRIGHT_YELLOW,
            ChangeType.UNCHANGED: Colors.DIM,
        }
        symbol = {
            ChangeType.ADDED: "+",
            ChangeType.REMOVED: "-",
            ChangeType.MODIFIED: "~",
            ChangeType.UNCHANGED: "=",
        }
        badge = f" [{symbol.get(change_type, '?')} {change_type.value.upper()}] "
        return self._color(badge, color_map.get(change_type, Colors.WHITE))

    def render_header(self, title: str = "SchemaMap-CLI") -> str:
        """渲染标题头"""
        lines = []
        lines.append("")
        lines.append(self._hr("=", Colors.CYAN))
        lines.append("")
        lines.append(self._color(self._center(self._bold(title)), Colors.BRIGHT_CYAN))
        lines.append(self._color(self._center("轻量级数据库Schema变更影响分析与智能迁移引擎"), Colors.DIM))
        lines.append("")
        lines.append(self._hr("=", Colors.CYAN))
        return "\n".join(lines)

    def render_summary(self, diff: SchemaDiff) -> str:
        """渲染变更摘要"""
        lines = []
        lines.append("")
        lines.append(self._bold(" SCHEMA CHANGE SUMMARY "))
        lines.append(self._hr("-", Colors.CYAN))
        lines.append("")

        summary = diff.summary
        total = summary.get("total_changes", 0)

        # 总体统计
        lines.append(f"  Total Changes: {self._color(str(total), Colors.BRIGHT_CYAN)}")
        lines.append("")

        # 表变更
        table_changes = (
            summary.get("tables_added", 0) +
            summary.get("tables_removed", 0) +
            summary.get("tables_modified", 0)
        )
        if table_changes > 0:
            lines.append(self._bold("  Tables:"))
            if summary.get("tables_added", 0):
                lines.append(f"    {self._color('+', Colors.GREEN)} Added:     {summary['tables_added']}")
            if summary.get("tables_removed", 0):
                lines.append(f"    {self._color('-', Colors.RED)} Removed:   {summary['tables_removed']}")
            if summary.get("tables_modified", 0):
                lines.append(f"    {self._color('~', Colors.YELLOW)} Modified:  {summary['tables_modified']}")
            lines.append("")

        # 列变更
        col_changes = (
            summary.get("columns_added", 0) +
            summary.get("columns_removed", 0) +
            summary.get("columns_modified", 0)
        )
        if col_changes > 0:
            lines.append(self._bold("  Columns:"))
            if summary.get("columns_added", 0):
                lines.append(f"    {self._color('+', Colors.GREEN)} Added:     {summary['columns_added']}")
            if summary.get("columns_removed", 0):
                lines.append(f"    {self._color('-', Colors.RED)} Removed:   {summary['columns_removed']}")
            if summary.get("columns_modified", 0):
                lines.append(f"    {self._color('~', Colors.YELLOW)} Modified:  {summary['columns_modified']}")
            lines.append("")

        # 索引变更
        idx_changes = (
            summary.get("indexes_added", 0) +
            summary.get("indexes_removed", 0) +
            summary.get("indexes_modified", 0)
        )
        if idx_changes > 0:
            lines.append(self._bold("  Indexes:"))
            if summary.get("indexes_added", 0):
                lines.append(f"    {self._color('+', Colors.GREEN)} Added:     {summary['indexes_added']}")
            if summary.get("indexes_removed", 0):
                lines.append(f"    {self._color('-', Colors.RED)} Removed:   {summary['indexes_removed']}")
            if summary.get("indexes_modified", 0):
                lines.append(f"    {self._color('~', Colors.YELLOW)} Modified:  {summary['indexes_modified']}")
            lines.append("")

        # 外键变更
        fk_changes = (
            summary.get("foreign_keys_added", 0) +
            summary.get("foreign_keys_removed", 0) +
            summary.get("foreign_keys_modified", 0)
        )
        if fk_changes > 0:
            lines.append(self._bold("  Foreign Keys:"))
            if summary.get("foreign_keys_added", 0):
                lines.append(f"    {self._color('+', Colors.GREEN)} Added:     {summary['foreign_keys_added']}")
            if summary.get("foreign_keys_removed", 0):
                lines.append(f"    {self._color('-', Colors.RED)} Removed:   {summary['foreign_keys_removed']}")
            if summary.get("foreign_keys_modified", 0):
                lines.append(f"    {self._color('~', Colors.YELLOW)} Modified:  {summary['foreign_keys_modified']}")
            lines.append("")

        return "\n".join(lines)

    def render_table_changes(self, diff: SchemaDiff) -> str:
        """渲染表级别变更详情"""
        lines = []
        lines.append("")
        lines.append(self._bold(" TABLE CHANGE DETAILS "))
        lines.append(self._hr("-", Colors.CYAN))
        lines.append("")

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.UNCHANGED:
                continue

            badge = self._change_type_badge(table_diff.change_type)
            lines.append(f"  {badge} {self._bold(table_diff.name)}")

            if table_diff.column_diffs:
                lines.append(f"    {self._dim('Columns:')}")
                for col_diff in table_diff.column_diffs:
                    col_badge = self._change_type_badge(col_diff.change_type)
                    lines.append(f"      {col_badge} {col_diff.name}")
                    if col_diff.property_changes:
                        for prop, change in col_diff.property_changes.items():
                            old_val = change.get("old", "None")
                            new_val = change.get("new", "None")
                            lines.append(
                                f"        {self._color('->', Colors.DIM)} "
                                f"{change.get('label', prop)}: "
                                f"{self._color(str(old_val), Colors.RED)} "
                                f"{self._color('=>', Colors.YELLOW)} "
                                f"{self._color(str(new_val), Colors.GREEN)}"
                            )

            if table_diff.index_diffs:
                lines.append(f"    {self._dim('Indexes:')}")
                for idx_diff in table_diff.index_diffs:
                    idx_badge = self._change_type_badge(idx_diff.change_type)
                    lines.append(f"      {idx_badge} {idx_diff.name}")

            if table_diff.fk_diffs:
                lines.append(f"    {self._dim('Foreign Keys:')}")
                for fk_diff in table_diff.fk_diffs:
                    fk_badge = self._change_type_badge(fk_diff.change_type)
                    lines.append(f"      {fk_badge} {fk_diff.name or 'unnamed'}")

            if table_diff.primary_key_changed:
                old_pk = ", ".join(table_diff.old_primary_key) or "None"
                new_pk = ", ".join(table_diff.new_primary_key) or "None"
                lines.append(f"    {self._dim('Primary Key:')}")
                lines.append(
                    f"      {self._color('~', Colors.YELLOW)} "
                    f"{old_pk} {self._color('=>', Colors.YELLOW)} {new_pk}"
                )

            lines.append("")

        return "\n".join(lines)

    def render_impact_report(self, report: ImpactReport) -> str:
        """渲染影响分析报告"""
        lines = []
        lines.append("")
        lines.append(self._bold(" IMPACT ANALYSIS REPORT "))
        lines.append(self._hr("-", Colors.CYAN))
        lines.append("")

        # 总体风险
        overall_risk = report.summary.get("overall_risk_level", "low")
        risk_colors = {
            "high": Colors.BRIGHT_RED,
            "medium": Colors.BRIGHT_YELLOW,
            "low": Colors.BRIGHT_GREEN,
        }
        risk_color = risk_colors.get(overall_risk, Colors.BRIGHT_GREEN)
        lines.append(
            f"  Overall Risk Level: {self._color(overall_risk.upper(), risk_color + Colors.BOLD)}"
        )
        lines.append("")

        # 统计
        stats = report.statistics
        lines.append(self._bold("  Statistics:"))
        lines.append(f"    Total Impact Items: {stats.get('total_items', 0)}")
        lines.append(f"    {self._color('High Risk:', Colors.RED)}   {stats.get('high_risk', 0)}")
        lines.append(f"    {self._color('Medium Risk:', Colors.YELLOW)} {stats.get('medium_risk', 0)}")
        lines.append(f"    {self._color('Low Risk:', Colors.GREEN)}  {stats.get('low_risk', 0)}")
        lines.append(f"    {self._color('Info:', Colors.BLUE)}      {stats.get('info', 0)}")
        lines.append("")

        # 建议
        recommendation = report.summary.get("recommendation", "")
        if recommendation:
            lines.append(self._bold("  Recommendation:"))
            for rec in recommendation.split("；"):
                rec = rec.strip()
                if rec:
                    lines.append(f"    {self._color('*', Colors.CYAN)} {rec}")
            lines.append("")

        # 详细影响项
        lines.append(self._bold("  Impact Details:"))
        lines.append("")

        for item in report.items:
            risk_badge = self._risk_badge(item.risk_level)
            cat_label = item.category.value.replace("_", " ").title()
            lines.append(f"  {risk_badge} {self._bold(item.title)}")
            lines.append(f"    Category: {cat_label}")
            lines.append(f"    {item.description}")

            if item.affected_entities:
                lines.append(f"    Affected: {', '.join(item.affected_entities)}")

            if item.suggestions:
                lines.append(f"    Suggestions:")
                for suggestion in item.suggestions:
                    lines.append(f"      {self._color('-', Colors.CYAN)} {suggestion}")

            if item.code_examples:
                lines.append(f"    Code Examples:")
                for lang, code in item.code_examples.items():
                    lines.append(f"      {self._color(f'[{lang}]', Colors.DIM)}")
                    for code_line in code.strip().split("\n"):
                        lines.append(f"        {self._color(code_line, Colors.DIM)}")

            lines.append("")

        return "\n".join(lines)

    def render_migration_script(self, script: MigrationScript) -> str:
        """渲染迁移脚本预览"""
        lines = []
        lines.append("")
        lines.append(self._bold(" MIGRATION SCRIPT PREVIEW "))
        lines.append(self._hr("-", Colors.CYAN))
        lines.append("")
        lines.append(f"  Dialect: {script.dialect.value.upper()}")
        lines.append("")

        if script.warnings:
            lines.append(self._color("  WARNINGS:", Colors.BRIGHT_YELLOW))
            for warning in script.warnings:
                lines.append(f"    {self._color('!', Colors.RED)} {warning}")
            lines.append("")

        lines.append(self._bold("  UP Migration:"))
        lines.append(self._color("  " + "-" * 60, Colors.DIM))
        for stmt in script.up_statements:
            for line in stmt.split("\n"):
                lines.append(f"  {line}")
        lines.append(self._color("  " + "-" * 60, Colors.DIM))
        lines.append("")

        if script.down_statements:
            lines.append(self._bold("  DOWN Migration (Rollback):"))
            lines.append(self._color("  " + "-" * 60, Colors.DIM))
            for stmt in script.down_statements:
                for line in stmt.split("\n"):
                    lines.append(f"  {line}")
            lines.append(self._color("  " + "-" * 60, Colors.DIM))
            lines.append("")

        return "\n".join(lines)

    def render_footer(self) -> str:
        """渲染页脚"""
        lines = []
        lines.append("")
        lines.append(self._hr("=", Colors.CYAN))
        lines.append("")
        lines.append(self._color(self._center("SchemaMap-CLI v1.0.0 | github.com/gitstq/SchemaMap-CLI"), Colors.DIM))
        lines.append("")
        return "\n".join(lines)

    def render_full_dashboard(self, diff: SchemaDiff, report: ImpactReport, script: MigrationScript) -> str:
        """渲染完整的仪表盘"""
        output = []
        output.append(self.render_header())
        output.append(self.render_summary(diff))
        output.append(self.render_table_changes(diff))
        output.append(self.render_impact_report(report))
        output.append(self.render_migration_script(script))
        output.append(self.render_footer())
        return "\n".join(output)

    def _dim(self, text: str) -> str:
        """暗淡文本"""
        return self._color(text, Colors.DIM)

    def print(self, text: str) -> None:
        """输出到终端"""
        print(text)

    def print_full_dashboard(self, diff: SchemaDiff, report: ImpactReport, script: MigrationScript) -> None:
        """打印完整仪表盘"""
        self.print(self.render_full_dashboard(diff, report, script))

    def print_error(self, message: str) -> None:
        """打印错误信息"""
        self.print(self._color(f"ERROR: {message}", Colors.BRIGHT_RED))

    def print_warning(self, message: str) -> None:
        """打印警告信息"""
        self.print(self._color(f"WARNING: {message}", Colors.BRIGHT_YELLOW))

    def print_success(self, message: str) -> None:
        """打印成功信息"""
        self.print(self._color(f"SUCCESS: {message}", Colors.BRIGHT_GREEN))

    def print_info(self, message: str) -> None:
        """打印信息"""
        self.print(self._color(f"INFO: {message}", Colors.BRIGHT_BLUE))
