"""
SchemaMap-CLI 主入口

命令行接口，提供Schema解析、变更检测、影响分析、迁移生成等功能。

纯Python标准库实现，零外部依赖。
"""

import argparse
import json
import sys
import os
from typing import Optional, List

from ..parser.schema_parser import SchemaParser
from ..detector.change_detector import ChangeDetector
from ..analyzer.impact_analyzer import ImpactAnalyzer
from ..generator.migration_generator import MigrationGenerator, Dialect
from ..tui.dashboard import DashboardRenderer


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="schemamap",
        description="SchemaMap-CLI - 轻量级数据库Schema变更影响分析与智能迁移引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  schemamap parse schema.sql                    # 解析Schema文件
  schemamap diff old.sql new.sql                # 对比两个Schema
  schemamap analyze old.sql new.sql             # 完整影响分析
  schemamap migrate old.sql new.sql --dialect mysql  # 生成迁移脚本
  schemamap dashboard old.sql new.sql           # TUI仪表盘展示
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="禁用终端颜色输出",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # parse 命令
    parse_parser = subparsers.add_parser(
        "parse",
        help="解析SQL DDL文件，提取Schema结构",
    )
    parse_parser.add_argument(
        "--no-color",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parse_parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="输出文件路径",
    )
    parse_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown", "html", "sql"],
        default="json",
        help="输出格式 (默认: json)",
    )
    parse_parser.add_argument(
        "schema_file",
        type=str,
        help="SQL DDL文件路径",
    )

    # diff 命令
    diff_parser = subparsers.add_parser(
        "diff",
        help="对比两个Schema版本，识别差异",
    )
    diff_parser.add_argument(
        "--no-color",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    diff_parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="输出文件路径",
    )
    diff_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown", "html", "sql"],
        default="json",
        help="输出格式 (默认: json)",
    )
    diff_parser.add_argument(
        "old_schema",
        type=str,
        help="旧版本Schema文件路径",
    )
    diff_parser.add_argument(
        "new_schema",
        type=str,
        help="新版本Schema文件路径",
    )

    # analyze 命令
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="分析Schema变更对应用的影响",
    )
    analyze_parser.add_argument(
        "--no-color",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    analyze_parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="输出文件路径",
    )
    analyze_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown", "html", "sql"],
        default="json",
        help="输出格式 (默认: json)",
    )
    analyze_parser.add_argument(
        "old_schema",
        type=str,
        help="旧版本Schema文件路径",
    )
    analyze_parser.add_argument(
        "new_schema",
        type=str,
        help="新版本Schema文件路径",
    )

    # migrate 命令
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="生成迁移SQL脚本",
    )
    migrate_parser.add_argument(
        "--no-color",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    migrate_parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="输出文件路径",
    )
    migrate_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown", "html", "sql"],
        default="sql",
        help="输出格式 (默认: sql)",
    )
    migrate_parser.add_argument(
        "old_schema",
        type=str,
        help="旧版本Schema文件路径",
    )
    migrate_parser.add_argument(
        "new_schema",
        type=str,
        help="新版本Schema文件路径",
    )
    migrate_parser.add_argument(
        "--dialect",
        choices=["sqlite", "postgresql", "mysql"],
        default="sqlite",
        help="数据库方言 (默认: sqlite)",
    )

    # dashboard 命令
    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="TUI仪表盘展示完整分析结果",
    )
    dashboard_parser.add_argument(
        "--no-color",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    dashboard_parser.add_argument(
        "old_schema",
        type=str,
        help="旧版本Schema文件路径",
    )
    dashboard_parser.add_argument(
        "new_schema",
        type=str,
        help="新版本Schema文件路径",
    )
    dashboard_parser.add_argument(
        "--dialect",
        choices=["sqlite", "postgresql", "mysql"],
        default="sqlite",
        help="数据库方言 (默认: sqlite)",
    )

    return parser


def read_schema_file(filepath: str) -> str:
    """读取Schema文件"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Schema文件不存在: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def write_output(content: str, filepath: Optional[str] = None) -> None:
    """写入输出文件或打印到stdout"""
    if filepath:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"输出已保存到: {filepath}")
    else:
        print(content)


def format_diff_as_markdown(diff) -> str:
    """将差异报告转为Markdown格式"""
    lines = []
    lines.append("# Schema变更差异报告")
    lines.append("")
    lines.append("## 摘要")
    lines.append("")
    lines.append(f"- **总变更数**: {diff.summary.get('total_changes', 0)}")
    lines.append(f"- **新增表**: {diff.summary.get('tables_added', 0)}")
    lines.append(f"- **删除表**: {diff.summary.get('tables_removed', 0)}")
    lines.append(f"- **修改表**: {diff.summary.get('tables_modified', 0)}")
    lines.append(f"- **新增列**: {diff.summary.get('columns_added', 0)}")
    lines.append(f"- **删除列**: {diff.summary.get('columns_removed', 0)}")
    lines.append(f"- **修改列**: {diff.summary.get('columns_modified', 0)}")
    lines.append("")

    lines.append("## 表变更详情")
    lines.append("")

    for table_diff in diff.table_diffs:
        if table_diff.change_type.value == "unchanged":
            continue

        lines.append(f"### {table_diff.name} ({table_diff.change_type.value})")
        lines.append("")

        if table_diff.column_diffs:
            lines.append("**列变更:**")
            lines.append("")
            lines.append("| 列名 | 变更类型 | 详情 |")
            lines.append("|------|----------|------|")
            for col_diff in table_diff.column_diffs:
                details = ""
                if col_diff.property_changes:
                    details = "; ".join(
                        f"{v.get('label', k)}: {v.get('old', 'None')} -> {v.get('new', 'None')}"
                        for k, v in col_diff.property_changes.items()
                    )
                lines.append(f"| {col_diff.name} | {col_diff.change_type.value} | {details} |")
            lines.append("")

        if table_diff.index_diffs:
            lines.append("**索引变更:**")
            for idx_diff in table_diff.index_diffs:
                lines.append(f"- {idx_diff.name}: {idx_diff.change_type.value}")
            lines.append("")

        if table_diff.primary_key_changed:
            old_pk = ", ".join(table_diff.old_primary_key) or "None"
            new_pk = ", ".join(table_diff.new_primary_key) or "None"
            lines.append(f"**主键变更:** {old_pk} -> {new_pk}")
            lines.append("")

    return "\n".join(lines)


def format_impact_as_markdown(report) -> str:
    """将影响报告转为Markdown格式"""
    lines = []
    lines.append("# Schema变更影响分析报告")
    lines.append("")
    lines.append("## 摘要")
    lines.append("")
    lines.append(f"- **总体风险等级**: {report.summary.get('overall_risk_level', 'low')}")
    lines.append(f"- **影响项总数**: {report.statistics.get('total_items', 0)}")
    lines.append(f"- **高风险**: {report.statistics.get('high_risk', 0)}")
    lines.append(f"- **中风险**: {report.statistics.get('medium_risk', 0)}")
    lines.append(f"- **低风险**: {report.statistics.get('low_risk', 0)}")
    lines.append("")

    recommendation = report.summary.get("recommendation", "")
    if recommendation:
        lines.append("## 建议")
        lines.append("")
        for rec in recommendation.split("；"):
            rec = rec.strip()
            if rec:
                lines.append(f"- {rec}")
        lines.append("")

    lines.append("## 详细影响分析")
    lines.append("")

    for item in report.items:
        risk_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵",
        }.get(item.risk_level.value, "⚪")

        lines.append(f"### {risk_emoji} {item.title}")
        lines.append("")
        lines.append(f"- **类别**: {item.category.value}")
        lines.append(f"- **风险等级**: {item.risk_level.value}")
        lines.append(f"- **描述**: {item.description}")

        if item.affected_entities:
            lines.append(f"- **影响实体**: {', '.join(item.affected_entities)}")

        if item.suggestions:
            lines.append("- **建议**:")
            for suggestion in item.suggestions:
                lines.append(f"  - {suggestion}")

        if item.code_examples:
            lines.append("- **代码示例**:")
            for lang, code in item.code_examples.items():
                lines.append(f"  ```{lang}")
                for code_line in code.strip().split("\n"):
                    lines.append(f"  {code_line}")
                lines.append("  ```")

        lines.append("")

    return "\n".join(lines)


def format_as_html(title: str, content: str) -> str:
    """将内容包装为HTML"""
    # 简单Markdown到HTML转换
    html_content = content

    # 标题
    html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)

    # 粗体
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)

    # 列表
    html_content = re.sub(r'^- (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)

    # 段落
    paragraphs = html_content.split('\n\n')
    wrapped = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            p = f'<p>{p}</p>'
        wrapped.append(p)
    html_content = '\n'.join(wrapped)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }}
        pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""


def cmd_parse(args) -> int:
    """执行parse命令"""
    try:
        sql = read_schema_file(args.schema_file)
        parser = SchemaParser()
        tables = parser.parse(sql)

        if args.format == "json":
            output = parser.to_json()
        else:
            output = json.dumps(parser.to_dict(), indent=2, ensure_ascii=False)

        write_output(output, args.output)
        return 0
    except Exception as e:
        renderer = DashboardRenderer(use_color=not args.no_color)
        renderer.print_error(str(e))
        return 1


def cmd_diff(args) -> int:
    """执行diff命令"""
    try:
        old_sql = read_schema_file(args.old_schema)
        new_sql = read_schema_file(args.new_schema)

        old_parser = SchemaParser()
        new_parser = SchemaParser()

        old_schema = old_parser.parse(old_sql)
        new_schema = new_parser.parse(new_sql)

        detector = ChangeDetector()
        diff = detector.detect(old_schema, new_schema)

        if args.format == "json":
            output = json.dumps(diff.to_dict(), indent=2, ensure_ascii=False)
        elif args.format == "markdown":
            output = format_diff_as_markdown(diff)
        elif args.format == "html":
            md = format_diff_as_markdown(diff)
            output = format_as_html("Schema变更差异报告", md)
        else:
            output = json.dumps(diff.to_dict(), indent=2, ensure_ascii=False)

        write_output(output, args.output)
        return 0
    except Exception as e:
        renderer = DashboardRenderer(use_color=not args.no_color)
        renderer.print_error(str(e))
        return 1


def cmd_analyze(args) -> int:
    """执行analyze命令"""
    try:
        old_sql = read_schema_file(args.old_schema)
        new_sql = read_schema_file(args.new_schema)

        old_parser = SchemaParser()
        new_parser = SchemaParser()

        old_schema = old_parser.parse(old_sql)
        new_schema = new_parser.parse(new_sql)

        detector = ChangeDetector()
        diff = detector.detect(old_schema, new_schema)

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(diff)

        if args.format == "json":
            output = report.to_json()
        elif args.format == "markdown":
            output = format_impact_as_markdown(report)
        elif args.format == "html":
            md = format_impact_as_markdown(report)
            output = format_as_html("Schema变更影响分析报告", md)
        else:
            output = report.to_json()

        write_output(output, args.output)
        return 0
    except Exception as e:
        renderer = DashboardRenderer(use_color=not args.no_color)
        renderer.print_error(str(e))
        return 1


def cmd_migrate(args) -> int:
    """执行migrate命令"""
    try:
        old_sql = read_schema_file(args.old_schema)
        new_sql = read_schema_file(args.new_schema)

        old_parser = SchemaParser()
        new_parser = SchemaParser()

        old_schema = old_parser.parse(old_sql)
        new_schema = new_parser.parse(new_sql)

        detector = ChangeDetector()
        diff = detector.detect(old_schema, new_schema)

        dialect_map = {
            "sqlite": Dialect.SQLITE,
            "postgresql": Dialect.POSTGRESQL,
            "mysql": Dialect.MYSQL,
        }
        dialect = dialect_map.get(args.dialect, Dialect.SQLITE)

        generator = MigrationGenerator(dialect=dialect)
        script = generator.generate(diff)

        if args.format == "sql":
            output = script.to_sql()
        elif args.format == "json":
            output = json.dumps(script.to_dict(), indent=2, ensure_ascii=False)
        else:
            output = script.to_sql()

        write_output(output, args.output)
        return 0
    except Exception as e:
        renderer = DashboardRenderer(use_color=not args.no_color)
        renderer.print_error(str(e))
        return 1


def cmd_dashboard(args) -> int:
    """执行dashboard命令"""
    try:
        old_sql = read_schema_file(args.old_schema)
        new_sql = read_schema_file(args.new_schema)

        old_parser = SchemaParser()
        new_parser = SchemaParser()

        old_schema = old_parser.parse(old_sql)
        new_schema = new_parser.parse(new_sql)

        detector = ChangeDetector()
        diff = detector.detect(old_schema, new_schema)

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(diff)

        dialect_map = {
            "sqlite": Dialect.SQLITE,
            "postgresql": Dialect.POSTGRESQL,
            "mysql": Dialect.MYSQL,
        }
        dialect = dialect_map.get(args.dialect, Dialect.SQLITE)

        generator = MigrationGenerator(dialect=dialect)
        script = generator.generate(diff)

        renderer = DashboardRenderer(use_color=not args.no_color)
        renderer.print_full_dashboard(diff, report, script)

        return 0
    except Exception as e:
        renderer = DashboardRenderer(use_color=not args.no_color)
        renderer.print_error(str(e))
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """主入口函数"""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "parse": cmd_parse,
        "diff": cmd_diff,
        "analyze": cmd_analyze,
        "migrate": cmd_migrate,
        "dashboard": cmd_dashboard,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 0


def _main_with_error_handling(argv: Optional[List[str]] = None) -> int:
    """带错误处理的主入口，用于测试"""
    try:
        return main(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


if __name__ == "__main__":
    sys.exit(main())
