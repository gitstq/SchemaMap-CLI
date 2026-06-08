"""
变更检测器模块

对比两个Schema版本，识别新增/删除/修改的表、列、索引、外键。
生成结构化的差异报告。

纯Python标准库实现，零外部依赖。
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum

from ..parser.schema_parser import Table, Column, Index, ForeignKey


class ChangeType(Enum):
    """变更类型"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class ColumnDiff:
    """列级别的变更差异"""
    name: str
    change_type: ChangeType
    old_column: Optional[Column] = None
    new_column: Optional[Column] = None
    property_changes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "change_type": self.change_type.value,
            "old_column": self.old_column.to_dict() if self.old_column else None,
            "new_column": self.new_column.to_dict() if self.new_column else None,
            "property_changes": self.property_changes,
        }


@dataclass
class IndexDiff:
    """索引级别的变更差异"""
    name: str
    change_type: ChangeType
    old_index: Optional[Index] = None
    new_index: Optional[Index] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "change_type": self.change_type.value,
            "old_index": self.old_index.to_dict() if self.old_index else None,
            "new_index": self.new_index.to_dict() if self.new_index else None,
        }


@dataclass
class ForeignKeyDiff:
    """外键级别的变更差异"""
    name: Optional[str]
    change_type: ChangeType
    old_fk: Optional[ForeignKey] = None
    new_fk: Optional[ForeignKey] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "change_type": self.change_type.value,
            "old_fk": self.old_fk.to_dict() if self.old_fk else None,
            "new_fk": self.new_fk.to_dict() if self.new_fk else None,
        }


@dataclass
class TableDiff:
    """表级别的变更差异"""
    name: str
    change_type: ChangeType
    old_table: Optional[Table] = None
    new_table: Optional[Table] = None
    column_diffs: List[ColumnDiff] = field(default_factory=list)
    index_diffs: List[IndexDiff] = field(default_factory=list)
    fk_diffs: List[ForeignKeyDiff] = field(default_factory=list)
    primary_key_changed: bool = False
    old_primary_key: List[str] = field(default_factory=list)
    new_primary_key: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "change_type": self.change_type.value,
            "column_diffs": [d.to_dict() for d in self.column_diffs],
            "index_diffs": [d.to_dict() for d in self.index_diffs],
            "fk_diffs": [d.to_dict() for d in self.fk_diffs],
            "primary_key_changed": self.primary_key_changed,
            "old_primary_key": self.old_primary_key,
            "new_primary_key": self.new_primary_key,
        }


@dataclass
class SchemaDiff:
    """Schema级别的完整差异报告"""
    old_schema: Dict[str, Table]
    new_schema: Dict[str, Table]
    table_diffs: List[TableDiff] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "tables": [d.to_dict() for d in self.table_diffs],
        }


class ChangeDetector:
    """
    Schema变更检测器

    对比两个Schema版本，识别所有差异并生成结构化报告。
    """

    def __init__(self):
        pass

    def detect(self, old_schema: Dict[str, Table], new_schema: Dict[str, Table]) -> SchemaDiff:
        """
        检测两个Schema之间的差异

        Args:
            old_schema: 旧版本Schema {table_name: Table}
            new_schema: 新版本Schema {table_name: Table}

        Returns:
            SchemaDiff: 完整的差异报告
        """
        diff = SchemaDiff(old_schema=old_schema, new_schema=new_schema)

        all_tables = set(old_schema.keys()) | set(new_schema.keys())

        for table_name in sorted(all_tables):
            old_table = old_schema.get(table_name)
            new_table = new_schema.get(table_name)

            table_diff = self._detect_table_diff(table_name, old_table, new_table)
            if table_diff:
                diff.table_diffs.append(table_diff)

        # 生成摘要
        diff.summary = self._generate_summary(diff)
        return diff

    def _detect_table_diff(self, name: str, old: Optional[Table], new: Optional[Table]) -> Optional[TableDiff]:
        """检测单个表的差异"""
        if old is None and new is None:
            return None

        if old is None:
            # 新增表
            return TableDiff(
                name=name,
                change_type=ChangeType.ADDED,
                new_table=new,
            )

        if new is None:
            # 删除表
            return TableDiff(
                name=name,
                change_type=ChangeType.REMOVED,
                old_table=old,
            )

        # 表存在，检查内部变更
        table_diff = TableDiff(
            name=name,
            change_type=ChangeType.MODIFIED,
            old_table=old,
            new_table=new,
        )

        # 检测列变更
        table_diff.column_diffs = self._detect_column_diffs(old, new)

        # 检测索引变更
        table_diff.index_diffs = self._detect_index_diffs(old, new)

        # 检测外键变更
        table_diff.fk_diffs = self._detect_fk_diffs(old, new)

        # 检测主键变更
        if old.primary_key != new.primary_key:
            table_diff.primary_key_changed = True
            table_diff.old_primary_key = old.primary_key
            table_diff.new_primary_key = new.primary_key

        # 如果没有内部变更，标记为未变更
        if (not table_diff.column_diffs and
            not table_diff.index_diffs and
            not table_diff.fk_diffs and
            not table_diff.primary_key_changed):
            table_diff.change_type = ChangeType.UNCHANGED

        return table_diff

    def _detect_column_diffs(self, old_table: Table, new_table: Table) -> List[ColumnDiff]:
        """检测列级别的差异"""
        diffs = []
        all_columns = set(old_table.columns.keys()) | set(new_table.columns.keys())

        for col_name in sorted(all_columns):
            old_col = old_table.columns.get(col_name)
            new_col = new_table.columns.get(col_name)

            if old_col is None:
                diffs.append(ColumnDiff(
                    name=col_name,
                    change_type=ChangeType.ADDED,
                    new_column=new_col,
                ))
            elif new_col is None:
                diffs.append(ColumnDiff(
                    name=col_name,
                    change_type=ChangeType.REMOVED,
                    old_column=old_col,
                ))
            else:
                # 检查属性变更
                prop_changes = self._compare_columns(old_col, new_col)
                if prop_changes:
                    diffs.append(ColumnDiff(
                        name=col_name,
                        change_type=ChangeType.MODIFIED,
                        old_column=old_col,
                        new_column=new_col,
                        property_changes=prop_changes,
                    ))

        return diffs

    def _compare_columns(self, old: Column, new: Column) -> Dict[str, Any]:
        """比较两个列的属性差异"""
        changes = {}
        properties = [
            ("data_type", "数据类型"),
            ("nullable", "可空性"),
            ("default", "默认值"),
            ("primary_key", "主键"),
            ("auto_increment", "自增"),
            ("unique", "唯一约束"),
            ("comment", "注释"),
        ]

        for prop, label in properties:
            old_val = getattr(old, prop)
            new_val = getattr(new, prop)
            if old_val != new_val:
                changes[prop] = {
                    "label": label,
                    "old": old_val,
                    "new": new_val,
                }

        return changes

    def _detect_index_diffs(self, old_table: Table, new_table: Table) -> List[IndexDiff]:
        """检测索引级别的差异"""
        diffs = []

        # 建立索引名称到索引的映射
        old_indexes = {idx.name: idx for idx in old_table.indexes}
        new_indexes = {idx.name: idx for idx in new_table.indexes}

        all_indexes = set(old_indexes.keys()) | set(new_indexes.keys())

        for idx_name in sorted(all_indexes):
            old_idx = old_indexes.get(idx_name)
            new_idx = new_indexes.get(idx_name)

            if old_idx is None:
                diffs.append(IndexDiff(
                    name=idx_name,
                    change_type=ChangeType.ADDED,
                    new_index=new_idx,
                ))
            elif new_idx is None:
                diffs.append(IndexDiff(
                    name=idx_name,
                    change_type=ChangeType.REMOVED,
                    old_index=old_idx,
                ))
            elif (old_idx.columns != new_idx.columns or
                  old_idx.unique != new_idx.unique or
                  old_idx.index_type != new_idx.index_type):
                diffs.append(IndexDiff(
                    name=idx_name,
                    change_type=ChangeType.MODIFIED,
                    old_index=old_idx,
                    new_index=new_idx,
                ))

        return diffs

    def _detect_fk_diffs(self, old_table: Table, new_table: Table) -> List[ForeignKeyDiff]:
        """检测外键级别的差异"""
        diffs = []

        # 使用外键名称或 column_refTable_refColumn 作为键
        def fk_key(fk: ForeignKey) -> str:
            return f"{fk.name or ''}:{fk.column}:{fk.ref_table}:{fk.ref_column}"

        old_fks = {fk_key(fk): fk for fk in old_table.foreign_keys}
        new_fks = {fk_key(fk): fk for fk in new_table.foreign_keys}

        all_fks = set(old_fks.keys()) | set(new_fks.keys())

        for fk_key_str in sorted(all_fks):
            old_fk = old_fks.get(fk_key_str)
            new_fk = new_fks.get(fk_key_str)

            if old_fk is None:
                diffs.append(ForeignKeyDiff(
                    name=new_fk.name if new_fk else None,
                    change_type=ChangeType.ADDED,
                    new_fk=new_fk,
                ))
            elif new_fk is None:
                diffs.append(ForeignKeyDiff(
                    name=old_fk.name if old_fk else None,
                    change_type=ChangeType.REMOVED,
                    old_fk=old_fk,
                ))
            elif (old_fk.on_delete != new_fk.on_delete or
                  old_fk.on_update != new_fk.on_update):
                diffs.append(ForeignKeyDiff(
                    name=old_fk.name if old_fk else None,
                    change_type=ChangeType.MODIFIED,
                    old_fk=old_fk,
                    new_fk=new_fk,
                ))

        return diffs

    def _generate_summary(self, diff: SchemaDiff) -> Dict[str, int]:
        """生成差异摘要统计"""
        summary = {
            "tables_added": 0,
            "tables_removed": 0,
            "tables_modified": 0,
            "tables_unchanged": 0,
            "columns_added": 0,
            "columns_removed": 0,
            "columns_modified": 0,
            "indexes_added": 0,
            "indexes_removed": 0,
            "indexes_modified": 0,
            "foreign_keys_added": 0,
            "foreign_keys_removed": 0,
            "foreign_keys_modified": 0,
            "primary_keys_changed": 0,
            "total_changes": 0,
        }

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.ADDED:
                summary["tables_added"] += 1
            elif table_diff.change_type == ChangeType.REMOVED:
                summary["tables_removed"] += 1
            elif table_diff.change_type == ChangeType.MODIFIED:
                summary["tables_modified"] += 1
            else:
                summary["tables_unchanged"] += 1

            for col_diff in table_diff.column_diffs:
                if col_diff.change_type == ChangeType.ADDED:
                    summary["columns_added"] += 1
                elif col_diff.change_type == ChangeType.REMOVED:
                    summary["columns_removed"] += 1
                elif col_diff.change_type == ChangeType.MODIFIED:
                    summary["columns_modified"] += 1

            for idx_diff in table_diff.index_diffs:
                if idx_diff.change_type == ChangeType.ADDED:
                    summary["indexes_added"] += 1
                elif idx_diff.change_type == ChangeType.REMOVED:
                    summary["indexes_removed"] += 1
                elif idx_diff.change_type == ChangeType.MODIFIED:
                    summary["indexes_modified"] += 1

            for fk_diff in table_diff.fk_diffs:
                if fk_diff.change_type == ChangeType.ADDED:
                    summary["foreign_keys_added"] += 1
                elif fk_diff.change_type == ChangeType.REMOVED:
                    summary["foreign_keys_removed"] += 1
                elif fk_diff.change_type == ChangeType.MODIFIED:
                    summary["foreign_keys_modified"] += 1

            if table_diff.primary_key_changed:
                summary["primary_keys_changed"] += 1

        # 计算总变更数
        summary["total_changes"] = (
            summary["tables_added"] + summary["tables_removed"] + summary["tables_modified"] +
            summary["columns_added"] + summary["columns_removed"] + summary["columns_modified"] +
            summary["indexes_added"] + summary["indexes_removed"] + summary["indexes_modified"] +
            summary["foreign_keys_added"] + summary["foreign_keys_removed"] + summary["foreign_keys_modified"] +
            summary["primary_keys_changed"]
        )

        return summary

    def has_changes(self, diff: SchemaDiff) -> bool:
        """检查是否有任何变更"""
        return diff.summary.get("total_changes", 0) > 0

    def get_risky_changes(self, diff: SchemaDiff) -> List[Dict[str, Any]]:
        """
        获取高风险的变更列表

        高风险变更包括：
        - 删除表
        - 删除列
        - 修改列数据类型
        - 删除主键
        - 删除外键
        """
        risky = []

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.REMOVED:
                risky.append({
                    "type": "table_removed",
                    "table": table_diff.name,
                    "risk": "high",
                    "description": f"表 '{table_diff.name}' 被删除，所有相关数据将丢失",
                })

            for col_diff in table_diff.column_diffs:
                if col_diff.change_type == ChangeType.REMOVED:
                    risky.append({
                        "type": "column_removed",
                        "table": table_diff.name,
                        "column": col_diff.name,
                        "risk": "high",
                        "description": f"表 '{table_diff.name}' 的列 '{col_diff.name}' 被删除",
                    })
                elif col_diff.change_type == ChangeType.MODIFIED:
                    if "data_type" in col_diff.property_changes:
                        risky.append({
                            "type": "column_type_changed",
                            "table": table_diff.name,
                            "column": col_diff.name,
                            "risk": "high",
                            "description": f"表 '{table_diff.name}' 的列 '{col_diff.name}' 数据类型变更",
                            "details": col_diff.property_changes["data_type"],
                        })
                    if "nullable" in col_diff.property_changes:
                        old_null = col_diff.property_changes["nullable"]["old"]
                        new_null = col_diff.property_changes["nullable"]["new"]
                        if old_null and not new_null:
                            risky.append({
                                "type": "column_not_null",
                                "table": table_diff.name,
                                "column": col_diff.name,
                                "risk": "medium",
                                "description": f"表 '{table_diff.name}' 的列 '{col_diff.name}' 变为NOT NULL",
                            })

            if table_diff.primary_key_changed and table_diff.old_primary_key and not table_diff.new_primary_key:
                risky.append({
                    "type": "primary_key_removed",
                    "table": table_diff.name,
                    "risk": "high",
                    "description": f"表 '{table_diff.name}' 的主键被移除",
                })

        return risky
