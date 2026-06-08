"""
迁移脚本生成器模块

基于Schema差异生成安全的迁移SQL脚本。
支持SQLite、PostgreSQL、MySQL的方言。

纯Python标准库实现，零外部依赖。
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

from ..parser.schema_parser import Table, Column, Index, ForeignKey
from ..detector.change_detector import SchemaDiff, ChangeType, TableDiff, ColumnDiff, IndexDiff


class Dialect(Enum):
    """数据库方言"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


@dataclass
class MigrationScript:
    """迁移脚本"""
    dialect: Dialect
    up_statements: List[str] = field(default_factory=list)
    down_statements: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dialect": self.dialect.value,
            "up": self.up_statements,
            "down": self.down_statements,
            "warnings": self.warnings,
        }

    def to_sql(self, include_down: bool = True) -> str:
        """生成完整的SQL脚本"""
        lines = []
        lines.append(f"-- Migration Script ({self.dialect.value})")
        lines.append("")
        lines.append("-- UP MIGRATION")
        lines.append("-- =============")
        lines.append("")

        if self.warnings:
            lines.append("-- WARNINGS:")
            for warning in self.warnings:
                lines.append(f"-- ! {warning}")
            lines.append("")

        lines.append("BEGIN TRANSACTION;")
        lines.append("")

        for stmt in self.up_statements:
            lines.append(stmt + ";")
            lines.append("")

        lines.append("COMMIT;")

        if include_down and self.down_statements:
            lines.append("")
            lines.append("-- DOWN MIGRATION (ROLLBACK)")
            lines.append("-- =========================")
            lines.append("")
            lines.append("BEGIN TRANSACTION;")
            lines.append("")

            for stmt in self.down_statements:
                lines.append(stmt + ";")
                lines.append("")

            lines.append("COMMIT;")

        return "\n".join(lines)


class MigrationGenerator:
    """
    迁移脚本生成器

    根据Schema差异自动生成安全的迁移SQL脚本。
    """

    def __init__(self, dialect: Dialect = Dialect.SQLITE):
        self.dialect = dialect

    def generate(self, diff: SchemaDiff) -> MigrationScript:
        """
        生成迁移脚本

        Args:
            diff: Schema差异报告

        Returns:
            MigrationScript: 包含UP和DOWN迁移语句的脚本
        """
        script = MigrationScript(dialect=self.dialect)

        for table_diff in diff.table_diffs:
            if table_diff.change_type == ChangeType.ADDED:
                self._generate_add_table(table_diff, script)
            elif table_diff.change_type == ChangeType.REMOVED:
                self._generate_drop_table(table_diff, script)
            elif table_diff.change_type == ChangeType.MODIFIED:
                self._generate_alter_table(table_diff, script)

        return script

    def _generate_add_table(self, table_diff: TableDiff, script: MigrationScript) -> None:
        """生成创建表的迁移脚本"""
        table = table_diff.new_table
        if not table:
            return

        # UP: CREATE TABLE
        columns_sql = []
        for col_name in table.columns:
            col = table.columns[col_name]
            columns_sql.append(self._column_definition_sql(col))

        # 主键约束
        if table.primary_key and len(table.primary_key) > 1:
            pk_cols = ", ".join(table.primary_key)
            columns_sql.append(f"PRIMARY KEY ({pk_cols})")
        elif table.primary_key and len(table.primary_key) == 1:
            # 单列主键已在列定义中处理
            pass

        # 外键约束
        for fk in table.foreign_keys:
            columns_sql.append(self._foreign_key_sql(fk))

        # 唯一约束
        for idx in table.indexes:
            if idx.unique:
                cols = ", ".join(idx.columns)
                columns_sql.append(f"UNIQUE ({cols})")

        joined_cols = ',\n    '.join(columns_sql)
        up_sql = f"CREATE TABLE {table.name} (\n    {joined_cols}\n)"
        script.up_statements.append(up_sql)

        # 单独创建非唯一索引
        for idx in table.indexes:
            if not idx.unique:
                cols = ", ".join(idx.columns)
                script.up_statements.append(
                    f"CREATE INDEX {idx.name} ON {table.name} ({cols})"
                )

        # DOWN: DROP TABLE
        script.down_statements.insert(0, f"DROP TABLE IF EXISTS {table.name}")

    def _generate_drop_table(self, table_diff: TableDiff, script: MigrationScript) -> None:
        """生成删除表的迁移脚本"""
        table = table_diff.old_table
        if not table:
            return

        script.warnings.append(
            f"Dropping table '{table.name}' will permanently delete all data. "
            "Ensure you have a backup before running this migration."
        )

        # UP: DROP TABLE
        script.up_statements.append(f"DROP TABLE IF EXISTS {table.name}")

        # DOWN: 重新创建表（简化版，不包含数据）
        # 实际应用中可能需要更复杂的恢复逻辑
        script.down_statements.insert(
            0,
            f"-- TODO: Recreate table '{table.name}' and restore data from backup"
        )

    def _generate_alter_table(self, table_diff: TableDiff, script: MigrationScript) -> None:
        """生成修改表的迁移脚本"""
        table_name = table_diff.name

        # 列变更
        for col_diff in table_diff.column_diffs:
            if col_diff.change_type == ChangeType.ADDED:
                self._generate_add_column(table_name, col_diff, script)
            elif col_diff.change_type == ChangeType.REMOVED:
                self._generate_drop_column(table_name, col_diff, script)
            elif col_diff.change_type == ChangeType.MODIFIED:
                self._generate_modify_column(table_name, col_diff, script)

        # 索引变更
        for idx_diff in table_diff.index_diffs:
            if idx_diff.change_type == ChangeType.ADDED:
                idx = idx_diff.new_index
                if idx:
                    cols = ", ".join(idx.columns)
                    script.up_statements.append(
                        f"CREATE {'UNIQUE ' if idx.unique else ''}INDEX {idx.name} ON {table_name} ({cols})"
                    )
                    script.down_statements.insert(
                        0, f"DROP INDEX IF EXISTS {idx.name}"
                    )
            elif idx_diff.change_type == ChangeType.REMOVED:
                idx = idx_diff.old_index
                if idx:
                    script.up_statements.append(f"DROP INDEX IF EXISTS {idx.name}")
                    cols = ", ".join(idx.columns)
                    script.down_statements.insert(
                        0,
                        f"CREATE {'UNIQUE ' if idx.unique else ''}INDEX {idx.name} ON {table_name} ({cols})"
                    )

        # 外键变更
        for fk_diff in table_diff.fk_diffs:
            if fk_diff.change_type == ChangeType.ADDED:
                fk = fk_diff.new_fk
                if fk:
                    script.warnings.append(
                        f"Adding foreign key on '{table_name}.{fk.column}' requires "
                        "existing data to satisfy the constraint."
                    )
                    if self.dialect == Dialect.SQLITE:
                        # SQLite 不支持 ALTER TABLE ADD FOREIGN KEY
                        script.up_statements.append(
                            f"-- TODO: SQLite requires table recreation to add foreign key "
                            f"'{fk.name or fk.column}'"
                        )
                    else:
                        constraint_name = fk.name or f"fk_{table_name}_{fk.column}"
                        script.up_statements.append(
                            f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} "
                            f"FOREIGN KEY ({fk.column}) REFERENCES {fk.ref_table}({fk.ref_column})"
                        )
            elif fk_diff.change_type == ChangeType.REMOVED:
                fk = fk_diff.old_fk
                if fk:
                    if self.dialect == Dialect.SQLITE:
                        script.up_statements.append(
                            f"-- TODO: SQLite requires table recreation to drop foreign key"
                        )
                    else:
                        constraint_name = fk.name or f"fk_{table_name}_{fk.column}"
                        script.up_statements.append(
                            f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}"
                        )

        # 主键变更
        if table_diff.primary_key_changed:
            script.warnings.append(
                f"Changing primary key of '{table_name}' is a complex operation. "
                "Ensure all foreign key references are updated accordingly."
            )
            if self.dialect == Dialect.SQLITE:
                script.up_statements.append(
                    f"-- TODO: SQLite requires table recreation to change primary key"
                )
            elif self.dialect == Dialect.POSTGRESQL:
                if table_diff.old_primary_key:
                    old_pk = ", ".join(table_diff.old_primary_key)
                    script.up_statements.append(
                        f"ALTER TABLE {table_name} DROP CONSTRAINT {table_name}_pkey"
                    )
                if table_diff.new_primary_key:
                    new_pk = ", ".join(table_diff.new_primary_key)
                    script.up_statements.append(
                        f"ALTER TABLE {table_name} ADD PRIMARY KEY ({new_pk})"
                    )
            elif self.dialect == Dialect.MYSQL:
                script.up_statements.append(f"ALTER TABLE {table_name} DROP PRIMARY KEY")
                if table_diff.new_primary_key:
                    new_pk = ", ".join(table_diff.new_primary_key)
                    script.up_statements.append(
                        f"ALTER TABLE {table_name} ADD PRIMARY KEY ({new_pk})"
                    )

    def _generate_add_column(self, table_name: str, col_diff: ColumnDiff, script: MigrationScript) -> None:
        """生成添加列的迁移脚本"""
        col = col_diff.new_column
        if not col:
            return

        col_def = self._column_definition_sql(col)

        if self.dialect == Dialect.SQLITE:
            # SQLite 有限制，新列不能有非空约束而没有默认值
            if not col.nullable and col.default is None:
                script.warnings.append(
                    f"SQLite requires DEFAULT value for new NOT NULL column '{col.name}'. "
                    "Adding with empty default."
                )
                col_def = col_def.replace("NOT NULL", "DEFAULT '' NOT NULL")

        script.up_statements.append(f"ALTER TABLE {table_name} ADD COLUMN {col_def}")

        # DOWN: DROP COLUMN
        if self.dialect == Dialect.SQLITE:
            script.down_statements.insert(
                0,
                f"-- TODO: SQLite does not support DROP COLUMN directly"
            )
        else:
            script.down_statements.insert(
                0, f"ALTER TABLE {table_name} DROP COLUMN {col.name}"
            )

    def _generate_drop_column(self, table_name: str, col_diff: ColumnDiff, script: MigrationScript) -> None:
        """生成删除列的迁移脚本"""
        col = col_diff.old_column
        if not col:
            return

        script.warnings.append(
            f"Dropping column '{table_name}.{col.name}' will permanently delete all data in that column."
        )

        if self.dialect == Dialect.SQLITE:
            script.up_statements.append(
                f"-- TODO: SQLite requires table recreation to drop column '{col.name}'"
            )
        else:
            script.up_statements.append(f"ALTER TABLE {table_name} DROP COLUMN {col.name}")

        # DOWN: 重新添加列（无数据）
        col_def = self._column_definition_sql(col)
        script.down_statements.insert(
            0, f"ALTER TABLE {table_name} ADD COLUMN {col_def}"
        )

    def _generate_modify_column(self, table_name: str, col_diff: ColumnDiff, script: MigrationScript) -> None:
        """生成修改列的迁移脚本"""
        col = col_diff.new_column
        old_col = col_diff.old_column
        if not col or not old_col:
            return

        # 检查是否有NOT NULL变更且没有默认值
        if not col.nullable and col.default is None:
            script.warnings.append(
                f"Column '{table_name}.{col.name}' is being set to NOT NULL without a default. "
                "Ensure existing rows have values."
            )
            # 添加预处理语句
            script.up_statements.append(
                f"-- Pre-migration: Update NULL values before setting NOT NULL"
            )
            script.up_statements.append(
                f"-- UPDATE {table_name} SET {col.name} = <default_value> WHERE {col.name} IS NULL;"
            )

        if self.dialect == Dialect.SQLITE:
            # SQLite 修改列需要表重建
            script.up_statements.append(
                f"-- TODO: SQLite requires table recreation to modify column '{col.name}'"
            )
        elif self.dialect == Dialect.POSTGRESQL:
            # 数据类型变更
            if "data_type" in col_diff.property_changes:
                script.up_statements.append(
                    f"ALTER TABLE {table_name} ALTER COLUMN {col.name} TYPE {self._sql_type(col)}"
                )
            # 可空性变更
            if "nullable" in col_diff.property_changes:
                if col.nullable:
                    script.up_statements.append(
                        f"ALTER TABLE {table_name} ALTER COLUMN {col.name} DROP NOT NULL"
                    )
                else:
                    script.up_statements.append(
                        f"ALTER TABLE {table_name} ALTER COLUMN {col.name} SET NOT NULL"
                    )
            # 默认值变更
            if "default" in col_diff.property_changes:
                if col.default:
                    script.up_statements.append(
                        f"ALTER TABLE {table_name} ALTER COLUMN {col.name} SET DEFAULT {col.default}"
                    )
                else:
                    script.up_statements.append(
                        f"ALTER TABLE {table_name} ALTER COLUMN {col.name} DROP DEFAULT"
                    )
        elif self.dialect == Dialect.MYSQL:
            col_def = self._column_definition_sql(col)
            script.up_statements.append(
                f"ALTER TABLE {table_name} MODIFY COLUMN {col_def}"
            )

    def _column_definition_sql(self, col: Column) -> str:
        """生成列定义SQL"""
        parts = [col.name, self._sql_type(col)]

        if col.primary_key:
            parts.append("PRIMARY KEY")

        if col.auto_increment:
            if self.dialect == Dialect.SQLITE:
                parts.append("AUTOINCREMENT")
            elif self.dialect == Dialect.MYSQL:
                parts.append("AUTO_INCREMENT")
            elif self.dialect == Dialect.POSTGRESQL:
                # PostgreSQL 使用 SERIAL
                pass

        if not col.nullable:
            parts.append("NOT NULL")

        if col.default is not None:
            parts.append(f"DEFAULT {col.default}")

        if col.unique and not col.primary_key:
            parts.append("UNIQUE")

        return " ".join(parts)

    def _sql_type(self, col: Column) -> str:
        """根据方言生成SQL数据类型"""
        type_mapping = {
            Dialect.SQLITE: {
                "INT": "INTEGER",
                "BIGINT": "INTEGER",
                "VARCHAR": "TEXT",
                "TEXT": "TEXT",
                "BOOLEAN": "INTEGER",
                "DATETIME": "TEXT",
                "DATE": "TEXT",
                "FLOAT": "REAL",
                "DOUBLE": "REAL",
                "DECIMAL": "NUMERIC",
            },
            Dialect.POSTGRESQL: {
                "INT": "INTEGER",
                "BIGINT": "BIGINT",
                "VARCHAR": "VARCHAR(255)",
                "TEXT": "TEXT",
                "BOOLEAN": "BOOLEAN",
                "DATETIME": "TIMESTAMP",
                "DATE": "DATE",
                "FLOAT": "REAL",
                "DOUBLE": "DOUBLE PRECISION",
                "DECIMAL": "DECIMAL(10,2)",
            },
            Dialect.MYSQL: {
                "INT": "INT",
                "BIGINT": "BIGINT",
                "VARCHAR": "VARCHAR(255)",
                "TEXT": "TEXT",
                "BOOLEAN": "BOOLEAN",
                "DATETIME": "DATETIME",
                "DATE": "DATE",
                "FLOAT": "FLOAT",
                "DOUBLE": "DOUBLE",
                "DECIMAL": "DECIMAL(10,2)",
            },
        }

        mapping = type_mapping.get(self.dialect, type_mapping[Dialect.SQLITE])
        return mapping.get(col.data_type, col.data_type)

    def _foreign_key_sql(self, fk: ForeignKey) -> str:
        """生成外键约束SQL"""
        parts = ["FOREIGN KEY"]
        if fk.name:
            parts.append(f"{fk.name}")
        parts.append(f"({fk.column})")
        parts.append(f"REFERENCES {fk.ref_table}({fk.ref_column})")

        if fk.on_delete != "NO ACTION":
            parts.append(f"ON DELETE {fk.on_delete}")
        if fk.on_update != "NO ACTION":
            parts.append(f"ON UPDATE {fk.on_update}")

        return " ".join(parts)

    def set_dialect(self, dialect: Dialect) -> None:
        """设置数据库方言"""
        self.dialect = dialect

    def generate_for_dialects(self, diff: SchemaDiff) -> Dict[str, MigrationScript]:
        """为所有支持的数据库方言生成迁移脚本"""
        scripts = {}
        for dialect in Dialect:
            self.dialect = dialect
            scripts[dialect.value] = self.generate(diff)
        return scripts
