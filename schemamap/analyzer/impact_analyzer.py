"""
影响分析引擎模块

分析Schema变更对以下方面的影响：
- ORM模型（SQLAlchemy、Django ORM等）
- API接口（REST/GraphQL）
- SQL查询语句
- 生成风险等级评估和适配建议

纯Python标准库实现，零外部依赖。
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum

from ..parser.schema_parser import Table, Column
from ..detector.change_detector import SchemaDiff, ChangeType, TableDiff, ColumnDiff


class RiskLevel(Enum):
    """风险等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ImpactCategory(Enum):
    """影响类别"""
    ORM_MODEL = "orm_model"
    API_REST = "api_rest"
    API_GRAPHQL = "api_graphql"
    SQL_QUERY = "sql_query"
    DATA_INTEGRITY = "data_integrity"
    PERFORMANCE = "performance"
    BACKWARD_COMPATIBILITY = "backward_compatibility"


@dataclass
class ImpactItem:
    """单个影响项"""
    category: ImpactCategory
    risk_level: RiskLevel
    title: str
    description: str
    affected_entities: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    code_examples: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "title": self.title,
            "description": self.description,
            "affected_entities": self.affected_entities,
            "suggestions": self.suggestions,
            "code_examples": self.code_examples,
        }


@dataclass
class ImpactReport:
    """完整的影响分析报告"""
    summary: Dict[str, Any] = field(default_factory=dict)
    items: List[ImpactItem] = field(default_factory=list)
    statistics: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "statistics": self.statistics,
            "items": [item.to_dict() for item in self.items],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class ImpactAnalyzer:
    """
    Schema变更影响分析器

    分析Schema变更对应用各层面的影响，生成风险评估和适配建议。
    """

    # ORM框架常见模式
    ORM_PATTERNS = {
        "sqlalchemy": [
            r'Column\s*\(\s*[\'"]{1}2%s[\'"]{1}',
            r'%s\s*=\s*db\.Column',
            r'%s\s*:\s*Mapped\[',
        ],
        "django": [
            r'models\.\w+Field\s*\([^)]*%s',
            r'%s\s*=\s*models\.',
        ],
        "peewee": [
            r'%s\s*=\s*\w+Field\s*\(',
        ],
    }

    # API常见模式
    API_PATTERNS = {
        "rest": [
            r'["\']%s["\']\s*:\s*',
            r'serializer\.\w+\(\s*[^)]*%s',
            r'\.fields\s*=\s*\[([^\]]*%s[^\]]*)\]',
        ],
        "graphql": [
            r'%s\s*:\s*\w+Type',
            r'field\s*\(\s*["\']?%s["\']?',
        ],
    }

    # SQL查询模式
    SQL_PATTERNS = [
        r'SELECT\s+([^*]|%s)',
        r'WHERE\s+[^\s]+\s*=\s*[^\s]+\s+AND\s+[^\s]*%s',
        r'INSERT\s+INTO\s+\w+\s*\([^)]*%s[^)]*\)',
        r'UPDATE\s+\w+\s+SET\s+[^\s]*%s',
        r'ORDER\s+BY\s+%s',
        r'GROUP\s+BY\s+%s',
        r'JOIN\s+\w+\s+ON\s+[^\s]*%s',
    ]

    def __init__(self):
        pass

    def analyze(self, diff: SchemaDiff) -> ImpactReport:
        """
        分析Schema变更的影响

        Args:
            diff: Schema差异报告

        Returns:
            ImpactReport: 完整的影响分析报告
        """
        report = ImpactReport()

        # 分析各类影响
        orm_items = self._analyze_orm_impact(diff)
        api_items = self._analyze_api_impact(diff)
        sql_items = self._analyze_sql_impact(diff)
        integrity_items = self._analyze_data_integrity(diff)
        perf_items = self._analyze_performance_impact(diff)
        compat_items = self._analyze_backward_compatibility(diff)

        report.items = orm_items + api_items + sql_items + integrity_items + perf_items + compat_items

        # 生成统计
        report.statistics = self._generate_statistics(report)

        # 生成摘要
        report.summary = self._generate_summary(report, diff)

        return report

    def _analyze_orm_impact(self, diff: SchemaDiff) -> List[ImpactItem]:
        """分析对ORM模型的影响"""
        items = []

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.ADDED:
                items.append(ImpactItem(
                    category=ImpactCategory.ORM_MODEL,
                    risk_level=RiskLevel.INFO,
                    title=f"新增表 '{table_diff.name}' 需要创建对应的ORM模型",
                    description=f"检测到新增表 '{table_diff.name}'，需要在ORM层创建对应的模型类。",
                    affected_entities=[table_diff.name],
                    suggestions=[
                        f"创建 {self._to_class_name(table_diff.name)} 模型类",
                        "更新数据库迁移脚本",
                        "如有需要，注册到管理后台",
                    ],
                    code_examples={
                        "sqlalchemy": f"""class {self._to_class_name(table_diff.name)}(Base):
    __tablename__ = '{table_diff.name}'
    # TODO: 添加列定义
""",
                        "django": f"""class {self._to_class_name(table_diff.name)}(models.Model):
    class Meta:
        db_table = '{table_diff.name}'
    # TODO: 添加字段定义
""",
                    }
                ))

            elif table_diff.change_type == ChangeType.REMOVED:
                items.append(ImpactItem(
                    category=ImpactCategory.ORM_MODEL,
                    risk_level=RiskLevel.HIGH,
                    title=f"表 '{table_diff.name}' 被删除，需要移除ORM模型",
                    description=f"表 '{table_diff.name}' 已删除，相关ORM模型类需要移除或标记为废弃。",
                    affected_entities=[table_diff.name],
                    suggestions=[
                        f"删除 {self._to_class_name(table_diff.name)} 模型类",
                        "检查并更新所有引用该模型的代码",
                        "更新序列化器和表单",
                    ],
                ))

            elif table_diff.change_type == ChangeType.MODIFIED:
                for col_diff in table_diff.column_diffs:
                    items.extend(self._analyze_column_orm_impact(table_diff.name, col_diff))

                if table_diff.primary_key_changed:
                    items.append(ImpactItem(
                        category=ImpactCategory.ORM_MODEL,
                        risk_level=RiskLevel.HIGH,
                        title=f"表 '{table_diff.name}' 主键变更影响ORM关系",
                        description=f"主键从 {table_diff.old_primary_key} 变更为 {table_diff.new_primary_key}，所有外键引用和关系定义需要更新。",
                        affected_entities=[table_diff.name],
                        suggestions=[
                            "更新所有ForeignKey引用",
                            "检查relationship定义",
                            "验证序列化器中的主键字段",
                        ],
                    ))

        return items

    def _analyze_column_orm_impact(self, table_name: str, col_diff: ColumnDiff) -> List[ImpactItem]:
        """分析单列变更对ORM的影响"""
        items = []

        if col_diff.change_type == ChangeType.ADDED:
            items.append(ImpactItem(
                category=ImpactCategory.ORM_MODEL,
                risk_level=RiskLevel.LOW,
                title=f"表 '{table_name}' 新增列 '{col_diff.name}'",
                description=f"需要在ORM模型中添加对应字段。",
                affected_entities=[f"{table_name}.{col_diff.name}"],
                suggestions=[
                    f"在模型中添加 {col_diff.name} 字段",
                    "更新序列化器",
                    "更新表单验证规则",
                ],
                code_examples={
                    "sqlalchemy": f"{col_diff.name} = Column({self._get_sqlalchemy_type(col_diff.new_column)})",
                    "django": f"{col_diff.name} = models.{self._get_django_type(col_diff.new_column)}()",
                }
            ))

        elif col_diff.change_type == ChangeType.REMOVED:
            items.append(ImpactItem(
                category=ImpactCategory.ORM_MODEL,
                risk_level=RiskLevel.HIGH,
                title=f"表 '{table_name}' 删除列 '{col_diff.name}'",
                description=f"ORM模型中的对应字段需要移除，所有引用该字段的代码需要更新。",
                affected_entities=[f"{table_name}.{col_diff.name}"],
                suggestions=[
                    f"从模型中移除 {col_diff.name} 字段",
                    "检查并更新所有引用该字段的查询",
                    "更新序列化器和API文档",
                ],
            ))

        elif col_diff.change_type == ChangeType.MODIFIED:
            if "data_type" in col_diff.property_changes:
                change = col_diff.property_changes["data_type"]
                items.append(ImpactItem(
                    category=ImpactCategory.ORM_MODEL,
                    risk_level=RiskLevel.MEDIUM,
                    title=f"表 '{table_name}' 列 '{col_diff.name}' 数据类型变更",
                    description=f"数据类型从 '{change['old']}' 变更为 '{change['new']}'，ORM字段类型需要同步更新。",
                    affected_entities=[f"{table_name}.{col_diff.name}"],
                    suggestions=[
                        f"更新ORM字段类型为 {change['new']}",
                        "检查数据转换兼容性",
                        "验证现有数据的类型转换",
                    ],
                ))

            if "nullable" in col_diff.property_changes:
                change = col_diff.property_changes["nullable"]
                if change["old"] and not change["new"]:
                    items.append(ImpactItem(
                        category=ImpactCategory.ORM_MODEL,
                        risk_level=RiskLevel.MEDIUM,
                        title=f"表 '{table_name}' 列 '{col_diff.name}' 变为NOT NULL",
                        description=f"列从可空变为非空，ORM层需要添加nullable=False约束，并确保所有创建/更新操作提供该字段值。",
                        affected_entities=[f"{table_name}.{col_diff.name}"],
                        suggestions=[
                            "更新ORM字段添加nullable=False",
                            "检查所有创建/更新代码确保字段有值",
                            "为现有NULL数据设置默认值",
                        ],
                    ))

            if "default" in col_diff.property_changes:
                items.append(ImpactItem(
                    category=ImpactCategory.ORM_MODEL,
                    risk_level=RiskLevel.LOW,
                    title=f"表 '{table_name}' 列 '{col_diff.name}' 默认值变更",
                    description=f"默认值发生变更，ORM层default参数需要同步。",
                    affected_entities=[f"{table_name}.{col_diff.name}"],
                    suggestions=[
                        "更新ORM字段的default参数",
                        "检查业务逻辑中是否有依赖旧默认值的代码",
                    ],
                ))

        return items

    def _analyze_api_impact(self, diff: SchemaDiff) -> List[ImpactItem]:
        """分析对API接口的影响"""
        items = []

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.ADDED:
                items.append(ImpactItem(
                    category=ImpactCategory.API_REST,
                    risk_level=RiskLevel.INFO,
                    title=f"新增表 '{table_diff.name}' 需要新增API端点",
                    description=f"建议为 '{table_diff.name}' 创建CRUD API端点。",
                    affected_entities=[table_diff.name],
                    suggestions=[
                        f"创建 /api/{table_diff.name} 端点",
                        "添加序列化器",
                        "添加权限控制",
                    ],
                ))

            elif table_diff.change_type == ChangeType.REMOVED:
                items.append(ImpactItem(
                    category=ImpactCategory.API_REST,
                    risk_level=RiskLevel.HIGH,
                    title=f"表 '{table_diff.name}' 删除，相关API需要废弃",
                    description=f"所有与 '{table_diff.name}' 相关的API端点需要移除或返回410 Gone。",
                    affected_entities=[table_diff.name],
                    suggestions=[
                        "移除相关API端点或返回410状态码",
                        "更新API文档",
                        "通知API消费者",
                    ],
                ))

            elif table_diff.change_type == ChangeType.MODIFIED:
                for col_diff in table_diff.column_diffs:
                    if col_diff.change_type == ChangeType.ADDED:
                        items.append(ImpactItem(
                            category=ImpactCategory.API_REST,
                            risk_level=RiskLevel.LOW,
                            title=f"API响应中可能需要包含新列 '{table_diff.name}.{col_diff.name}'",
                            description=f"新列已添加，检查API序列化器是否需要包含该字段。",
                            affected_entities=[f"{table_diff.name}.{col_diff.name}"],
                            suggestions=[
                                "更新序列化器字段列表",
                                "更新API文档",
                            ],
                        ))

                    elif col_diff.change_type == ChangeType.REMOVED:
                        items.append(ImpactItem(
                            category=ImpactCategory.API_REST,
                            risk_level=RiskLevel.HIGH,
                            title=f"API响应中的字段 '{col_diff.name}' 将被移除",
                            description=f"列 '{col_diff.name}' 已删除，API响应中不能再包含该字段，否则会导致客户端错误。",
                            affected_entities=[f"{table_diff.name}.{col_diff.name}"],
                            suggestions=[
                                "从序列化器中移除该字段",
                                "如果必须保持兼容，先标记为废弃",
                                "更新API文档和版本说明",
                            ],
                        ))

                    elif col_diff.change_type == ChangeType.MODIFIED:
                        if "nullable" in col_diff.property_changes:
                            change = col_diff.property_changes["nullable"]
                            if change["old"] and not change["new"]:
                                items.append(ImpactItem(
                                    category=ImpactCategory.API_REST,
                                    risk_level=RiskLevel.MEDIUM,
                                    title=f"API请求验证需要要求 '{col_diff.name}' 字段",
                                    description=f"列变为NOT NULL，API层需要确保请求中包含该字段。",
                                    affected_entities=[f"{table_diff.name}.{col_diff.name}"],
                                    suggestions=[
                                        "在序列化器中添加required=True",
                                        "更新请求验证逻辑",
                                        "更新API文档",
                                    ],
                                ))

        return items

    def _analyze_sql_impact(self, diff: SchemaDiff) -> List[ImpactItem]:
        """分析对SQL查询的影响"""
        items = []

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.REMOVED:
                items.append(ImpactItem(
                    category=ImpactCategory.SQL_QUERY,
                    risk_level=RiskLevel.HIGH,
                    title=f"所有引用表 '{table_diff.name}' 的SQL查询将失败",
                    description=f"表被删除后，所有SELECT/INSERT/UPDATE/DELETE语句都需要移除或修改。",
                    affected_entities=[table_diff.name],
                    suggestions=[
                        "搜索并更新所有SQL查询",
                        "检查视图和存储过程",
                        "检查触发器定义",
                    ],
                ))

            elif table_diff.change_type == ChangeType.MODIFIED:
                for col_diff in table_diff.column_diffs:
                    if col_diff.change_type == ChangeType.REMOVED:
                        items.append(ImpactItem(
                            category=ImpactCategory.SQL_QUERY,
                            risk_level=RiskLevel.HIGH,
                            title=f"引用列 '{table_diff.name}.{col_diff.name}' 的SQL查询将失败",
                            description=f"列被删除后，所有包含该列的查询（SELECT、WHERE、ORDER BY、JOIN等）都会报错。",
                            affected_entities=[f"{table_diff.name}.{col_diff.name}"],
                            suggestions=[
                                f"搜索所有包含 '{col_diff.name}' 的SQL语句",
                                "更新SELECT列表",
                                "更新WHERE条件和JOIN条件",
                            ],
                        ))

                    elif col_diff.change_type == ChangeType.MODIFIED:
                        if "data_type" in col_diff.property_changes:
                            items.append(ImpactItem(
                                category=ImpactCategory.SQL_QUERY,
                                risk_level=RiskLevel.MEDIUM,
                                title=f"列 '{table_diff.name}.{col_diff.name}' 类型变更可能影响查询",
                                description=f"数据类型变更可能导致隐式转换失败或比较行为变化。",
                                affected_entities=[f"{table_diff.name}.{col_diff.name}"],
                                suggestions=[
                                    "检查所有WHERE条件中的类型比较",
                                    "检查JOIN条件",
                                    "验证聚合函数的使用",
                                ],
                            ))

        return items

    def _analyze_data_integrity(self, diff: SchemaDiff) -> List[ImpactItem]:
        """分析数据完整性影响"""
        items = []

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.MODIFIED:
                for col_diff in table_diff.column_diffs:
                    if col_diff.change_type == ChangeType.MODIFIED:
                        if "nullable" in col_diff.property_changes:
                            change = col_diff.property_changes["nullable"]
                            if change["old"] and not change["new"]:
                                items.append(ImpactItem(
                                    category=ImpactCategory.DATA_INTEGRITY,
                                    risk_level=RiskLevel.HIGH,
                                    title=f"列 '{table_diff.name}.{col_diff.name}' 变为NOT NULL可能导致数据迁移失败",
                                    description=f"如果现有数据中存在NULL值，迁移脚本将执行失败。",
                                    affected_entities=[f"{table_diff.name}.{col_diff.name}"],
                                    suggestions=[
                                        "先更新现有NULL数据",
                                        "设置合理的默认值",
                                        "分两步执行：先更新数据，再添加约束",
                                    ],
                                    code_examples={
                                        "migration": f"""-- 第一步：更新NULL数据
UPDATE {table_diff.name}
SET {col_diff.name} = <default_value>
WHERE {col_diff.name} IS NULL;

-- 第二步：添加NOT NULL约束
ALTER TABLE {table_diff.name}
ALTER COLUMN {col_diff.name} SET NOT NULL;
"""
                                    }
                                ))

                        if "data_type" in col_diff.property_changes:
                            items.append(ImpactItem(
                                category=ImpactCategory.DATA_INTEGRITY,
                                risk_level=RiskLevel.MEDIUM,
                                title=f"列 '{table_diff.name}.{col_diff.name}' 类型变更可能导致数据截断或丢失",
                                description=f"数据类型变更时，需要验证现有数据能否安全转换。",
                                affected_entities=[f"{table_diff.name}.{col_diff.name}"],
                                suggestions=[
                                    "备份数据后再执行变更",
                                    "检查数据转换兼容性",
                                    "考虑使用CAST进行显式转换",
                                ],
                            ))

        return items

    def _analyze_performance_impact(self, diff: SchemaDiff) -> List[ImpactItem]:
        """分析性能影响"""
        items = []

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.MODIFIED:
                for idx_diff in table_diff.index_diffs:
                    if idx_diff.change_type == ChangeType.REMOVED:
                        items.append(ImpactItem(
                            category=ImpactCategory.PERFORMANCE,
                            risk_level=RiskLevel.MEDIUM,
                            title=f"索引 '{idx_diff.name}' 被删除可能影响查询性能",
                            description=f"删除索引后，依赖该索引的查询可能会变慢。",
                            affected_entities=[f"{table_diff.name}.{idx_diff.name}"],
                            suggestions=[
                                "确认该索引不再被查询使用",
                                "检查慢查询日志",
                                "如有必要，保留索引",
                            ],
                        ))

                    elif idx_diff.change_type == ChangeType.ADDED:
                        items.append(ImpactItem(
                            category=ImpactCategory.PERFORMANCE,
                            risk_level=RiskLevel.INFO,
                            title=f"新增索引 '{idx_diff.name}' 可能提升查询性能",
                            description=f"新索引有助于提升相关查询的性能，但会增加写入开销。",
                            affected_entities=[f"{table_diff.name}.{idx_diff.name}"],
                            suggestions=[
                                "监控索引使用情况",
                                "评估写入性能影响",
                                "定期分析查询计划",
                            ],
                        ))

        return items

    def _analyze_backward_compatibility(self, diff: SchemaDiff) -> List[ImpactItem]:
        """分析向后兼容性影响"""
        items = []
        has_breaking_change = False
        breaking_changes = []

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.REMOVED:
                has_breaking_change = True
                breaking_changes.append(f"删除表 '{table_diff.name}'")
            elif table_diff.change_type == ChangeType.MODIFIED:
                for col_diff in table_diff.column_diffs:
                    if col_diff.change_type == ChangeType.REMOVED:
                        has_breaking_change = True
                        breaking_changes.append(f"删除列 '{table_diff.name}.{col_diff.name}'")
                    elif col_diff.change_type == ChangeType.MODIFIED:
                        if "data_type" in col_diff.property_changes:
                            has_breaking_change = True
                            breaking_changes.append(f"修改列类型 '{table_diff.name}.{col_diff.name}'")
                        if "nullable" in col_diff.property_changes:
                            old_null = col_diff.property_changes["nullable"]["old"]
                            new_null = col_diff.property_changes["nullable"]["new"]
                            if old_null and not new_null:
                                has_breaking_change = True
                                breaking_changes.append(f"列变为NOT NULL '{table_diff.name}.{col_diff.name}'")

        if has_breaking_change:
            items.append(ImpactItem(
                category=ImpactCategory.BACKWARD_COMPATIBILITY,
                risk_level=RiskLevel.HIGH,
                title="检测到破坏性变更，可能影响现有应用",
                description=f"发现 {len(breaking_changes)} 项破坏性变更：" + "; ".join(breaking_changes),
                affected_entities=[],
                suggestions=[
                    "考虑分阶段发布：先添加新结构，再移除旧结构",
                    "使用蓝绿部署或金丝雀发布",
                    "提前通知API消费者",
                    "准备回滚方案",
                ],
            ))
        else:
            items.append(ImpactItem(
                category=ImpactCategory.BACKWARD_COMPATIBILITY,
                risk_level=RiskLevel.INFO,
                title="未检测到破坏性变更",
                description="当前Schema变更对现有应用是向后兼容的。",
                affected_entities=[],
                suggestions=[
                    "可以安全部署",
                    "建议仍然进行充分测试",
                ],
            ))

        return items

    def _generate_statistics(self, report: ImpactReport) -> Dict[str, int]:
        """生成影响统计"""
        stats = {
            "total_items": len(report.items),
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0,
            "info": 0,
        }

        category_counts = {}
        for item in report.items:
            if item.risk_level == RiskLevel.HIGH:
                stats["high_risk"] += 1
            elif item.risk_level == RiskLevel.MEDIUM:
                stats["medium_risk"] += 1
            elif item.risk_level == RiskLevel.LOW:
                stats["low_risk"] += 1
            else:
                stats["info"] += 1

            cat = item.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        stats["by_category"] = category_counts
        return stats

    def _generate_summary(self, report: ImpactReport, diff: SchemaDiff) -> Dict[str, Any]:
        """生成影响摘要"""
        total_changes = diff.summary.get("total_changes", 0)
        high_risk = report.statistics.get("high_risk", 0)
        medium_risk = report.statistics.get("medium_risk", 0)

        overall_risk = "low"
        if high_risk > 0:
            overall_risk = "high"
        elif medium_risk > 0:
            overall_risk = "medium"

        return {
            "total_schema_changes": total_changes,
            "total_impact_items": len(report.items),
            "overall_risk_level": overall_risk,
            "recommendation": self._get_recommendation(overall_risk),
        }

    def _get_recommendation(self, risk_level: str) -> str:
        """根据风险等级给出建议"""
        recommendations = {
            "high": "检测到高风险变更！建议：1) 在 staging 环境充分测试；2) 准备回滚方案；3) 考虑分阶段发布；4) 通知所有相关团队。",
            "medium": "检测到中等风险变更。建议：1) 执行数据备份；2) 验证所有查询兼容性；3) 更新ORM模型和API文档。",
            "low": "风险较低。建议：1) 执行标准测试流程；2) 更新相关文档。",
        }
        return recommendations.get(risk_level, "建议进行标准测试后发布。")

    def _to_class_name(self, table_name: str) -> str:
        """将表名转为类名（驼峰命名）"""
        parts = table_name.split('_')
        return ''.join(p.capitalize() for p in parts if p)

    def _get_sqlalchemy_type(self, column: Optional[Column]) -> str:
        """获取SQLAlchemy类型字符串"""
        if not column:
            return "String(255)"
        type_map = {
            "INT": "Integer",
            "BIGINT": "BigInteger",
            "VARCHAR": "String(255)",
            "TEXT": "Text",
            "BOOLEAN": "Boolean",
            "DATETIME": "DateTime",
            "DATE": "Date",
            "FLOAT": "Float",
            "DOUBLE": "Float",
            "DECIMAL": "Numeric",
        }
        return type_map.get(column.data_type, "String(255)")

    def _get_django_type(self, column: Optional[Column]) -> str:
        """获取Django字段类型字符串"""
        if not column:
            return "CharField(max_length=255)"
        type_map = {
            "INT": "IntegerField",
            "BIGINT": "BigIntegerField",
            "VARCHAR": "CharField(max_length=255)",
            "TEXT": "TextField",
            "BOOLEAN": "BooleanField",
            "DATETIME": "DateTimeField",
            "DATE": "DateField",
            "FLOAT": "FloatField",
            "DOUBLE": "FloatField",
            "DECIMAL": "DecimalField(max_digits=10, decimal_places=2)",
        }
        return type_map.get(column.data_type, "CharField(max_length=255)")
