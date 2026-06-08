"""
Schema解析器模块

解析SQL DDL语句（CREATE TABLE、ALTER TABLE等），提取表、列、索引、外键信息。
支持SQLite、PostgreSQL、MySQL的DDL语法。

纯Python标准库实现，零外部依赖。
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any


@dataclass
class Column:
    """表示数据库表中的一个列"""
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False
    auto_increment: bool = False
    unique: bool = False
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Index:
    """表示数据库表中的一个索引"""
    name: str
    columns: List[str] = field(default_factory=list)
    unique: bool = False
    index_type: str = "BTREE"  # BTREE, HASH, etc.

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ForeignKey:
    """表示表之间的外键关系"""
    name: Optional[str] = None
    column: str = ""
    ref_table: str = ""
    ref_column: str = ""
    on_delete: str = "NO ACTION"
    on_update: str = "NO ACTION"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Table:
    """表示数据库中的一个表"""
    name: str
    columns: Dict[str, Column] = field(default_factory=dict)
    indexes: List[Index] = field(default_factory=list)
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "columns": {k: v.to_dict() for k, v in self.columns.items()},
            "indexes": [idx.to_dict() for idx in self.indexes],
            "foreign_keys": [fk.to_dict() for fk in self.foreign_keys],
            "primary_key": self.primary_key,
            "comment": self.comment,
        }


class SchemaParser:
    """
    SQL DDL解析器

    解析SQL DDL语句，提取数据库Schema结构信息。
    支持CREATE TABLE、ALTER TABLE、CREATE INDEX等语句。
    """

    # 数据类型映射（统一不同数据库的命名）
    TYPE_MAPPING = {
        # SQLite
        "INTEGER": "INT",
        "REAL": "FLOAT",
        "TEXT": "TEXT",
        "BLOB": "BLOB",
        "NUMERIC": "NUMERIC",
        # PostgreSQL
        "SERIAL": "INT",
        "BIGSERIAL": "BIGINT",
        "CHARACTER VARYING": "VARCHAR",
        "CHARACTER": "CHAR",
        "DOUBLE PRECISION": "DOUBLE",
        # MySQL
        "TINYINT": "TINYINT",
        "SMALLINT": "SMALLINT",
        "MEDIUMINT": "MEDIUMINT",
        "BIGINT": "BIGINT",
        "FLOAT": "FLOAT",
        "DOUBLE": "DOUBLE",
        "DECIMAL": "DECIMAL",
        "DATE": "DATE",
        "DATETIME": "DATETIME",
        "TIMESTAMP": "TIMESTAMP",
        "TIME": "TIME",
        "YEAR": "YEAR",
        "VARCHAR": "VARCHAR",
        "CHAR": "CHAR",
        "BINARY": "BINARY",
        "VARBINARY": "VARBINARY",
        "TINYBLOB": "TINYBLOB",
        "MEDIUMBLOB": "MEDIUMBLOB",
        "LONGBLOB": "LONGBLOB",
        "TINYTEXT": "TINYTEXT",
        "MEDIUMTEXT": "MEDIUMTEXT",
        "LONGTEXT": "LONGTEXT",
        "ENUM": "ENUM",
        "SET": "SET",
        "BOOLEAN": "BOOLEAN",
        "BOOL": "BOOLEAN",
        "INT": "INT",
    }

    def __init__(self):
        self.tables: Dict[str, Table] = {}
        self._current_table: Optional[str] = None

    def parse(self, sql: str) -> Dict[str, Table]:
        """
        解析SQL DDL字符串

        Args:
            sql: 包含DDL语句的SQL字符串

        Returns:
            解析后的表结构字典 {table_name: Table}
        """
        # 清理SQL：移除注释，标准化空白
        sql = self._clean_sql(sql)

        # 按语句分割
        statements = self._split_statements(sql)

        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue

            upper_stmt = stmt.upper()

            if upper_stmt.startswith("CREATE TABLE"):
                self._parse_create_table(stmt)
            elif upper_stmt.startswith("ALTER TABLE"):
                self._parse_alter_table(stmt)
            elif upper_stmt.startswith("CREATE INDEX") or upper_stmt.startswith("CREATE UNIQUE INDEX"):
                self._parse_create_index(stmt)

        return self.tables

    def _clean_sql(self, sql: str) -> str:
        """清理SQL字符串：移除注释，标准化"""
        # 移除单行注释
        sql = re.sub(r'--[^\n]*', '', sql)
        # 移除多行注释
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        # 标准化空白
        sql = re.sub(r'\s+', ' ', sql)
        return sql.strip()

    def _split_statements(self, sql: str) -> List[str]:
        """将SQL字符串分割为单独的语句"""
        # 按分号分割，但忽略字符串内的分号
        statements = []
        current = []
        in_string = False
        string_char = None

        i = 0
        while i < len(sql):
            char = sql[i]

            if not in_string and char in "'\"`":
                in_string = True
                string_char = char
            elif in_string and char == string_char:
                # 检查是否是转义
                if i + 1 < len(sql) and sql[i + 1] == string_char:
                    current.append(char)
                    i += 1
                else:
                    in_string = False
                    string_char = None
            elif not in_string and char == ';':
                statements.append(''.join(current))
                current = []
            else:
                current.append(char)
            i += 1

        if current:
            statements.append(''.join(current))

        return statements

    def _parse_create_table(self, sql: str) -> None:
        """解析CREATE TABLE语句"""
        # 匹配表名
        match = re.match(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\']?(\w+)[`"\']?\s*\((.*)\)',
            sql,
            re.IGNORECASE | re.DOTALL
        )
        if not match:
            return

        table_name = match.group(1)
        body = match.group(2)
        self._current_table = table_name

        table = Table(name=table_name)

        # 解析列定义和约束
        # 需要处理括号嵌套（如ENUM定义）
        parts = self._split_columns(body)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            upper_part = part.upper()

            if upper_part.startswith("PRIMARY KEY"):
                self._parse_primary_key(part, table)
            elif upper_part.startswith("FOREIGN KEY"):
                self._parse_foreign_key(part, table)
            elif upper_part.startswith("UNIQUE"):
                self._parse_unique_constraint(part, table)
            elif upper_part.startswith("INDEX") or upper_part.startswith("KEY"):
                self._parse_index_constraint(part, table)
            elif upper_part.startswith("CONSTRAINT"):
                self._parse_constraint(part, table)
            else:
                # 列定义
                column = self._parse_column_definition(part)
                if column:
                    table.columns[column.name] = column
                    if column.primary_key:
                        table.primary_key.append(column.name)

        self.tables[table_name] = table
        self._current_table = None

    def _split_columns(self, body: str) -> List[str]:
        """
        分割CREATE TABLE体中的列定义和约束
        需要处理括号嵌套
        """
        parts = []
        current = []
        depth = 0
        in_string = False
        string_char = None

        for char in body:
            if char in "'\"`" and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
            elif char == '(' and not in_string:
                depth += 1
            elif char == ')' and not in_string:
                depth -= 1
            elif char == ',' and depth == 0 and not in_string:
                parts.append(''.join(current))
                current = []
                continue

            current.append(char)

        if current:
            parts.append(''.join(current))

        return parts

    def _parse_column_definition(self, sql: str) -> Optional[Column]:
        """解析列定义"""
        # 列定义格式: name type [constraints...]
        # 匹配类型部分，需要排除约束关键字
        match = re.match(
            r'[`"\']?(\w+)[`"\']?\s+(\w+(?:\s*\([^)]*\))?)(?:\s+|$)',
            sql,
            re.IGNORECASE
        )
        if not match:
            return None

        name = match.group(1)
        data_type = match.group(2).strip().upper()

        # 标准化数据类型
        base_type = data_type.split('(')[0].strip()
        normalized_type = self.TYPE_MAPPING.get(base_type, base_type)

        column = Column(
            name=name,
            data_type=normalized_type,
        )

        upper_sql = sql.upper()

        # NOT NULL
        if "NOT NULL" in upper_sql:
            column.nullable = False

        # DEFAULT
        default_match = re.search(r'DEFAULT\s+([^,\s]+(?:\s+[^,\s]+)*)', sql, re.IGNORECASE)
        if default_match:
            column.default = default_match.group(1).strip()

        # PRIMARY KEY
        if "PRIMARY KEY" in upper_sql:
            column.primary_key = True

        # AUTO_INCREMENT / SERIAL
        if any(kw in upper_sql for kw in ["AUTO_INCREMENT", "AUTOINCREMENT", "SERIAL"]):
            column.auto_increment = True

        # UNIQUE
        if "UNIQUE" in upper_sql:
            column.unique = True

        # COMMENT
        comment_match = re.search(r'COMMENT\s+[\'"]([^\'"]+)[\'"]', sql, re.IGNORECASE)
        if comment_match:
            column.comment = comment_match.group(1)

        return column

    def _parse_primary_key(self, sql: str, table: Table) -> None:
        """解析PRIMARY KEY约束"""
        match = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', sql, re.IGNORECASE)
        if match:
            columns = [c.strip().strip('`"\'') for c in match.group(1).split(',')]
            table.primary_key = columns
            for col_name in columns:
                if col_name in table.columns:
                    table.columns[col_name].primary_key = True

    def _parse_foreign_key(self, sql: str, table: Table) -> None:
        """解析FOREIGN KEY约束"""
        match = re.search(
            r'(?:CONSTRAINT\s+[`"\']?(\w+)[`"\']?\s+)?FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+[`"\']?(\w+)[`"\']?(?:\s*\(([^)]+)\))?',
            sql,
            re.IGNORECASE
        )
        if match:
            fk = ForeignKey(
                name=match.group(1),
                column=match.group(2).strip().strip('`"\''),
                ref_table=match.group(3).strip(),
                ref_column=match.group(4).strip().strip('`"\'') if match.group(4) else "id",
            )

            # ON DELETE / ON UPDATE
            on_delete = re.search(r'ON\s+DELETE\s+(\w+(?:\s+\w+)?)', sql, re.IGNORECASE)
            if on_delete:
                fk.on_delete = on_delete.group(1).upper()

            on_update = re.search(r'ON\s+UPDATE\s+(\w+(?:\s+\w+)?)', sql, re.IGNORECASE)
            if on_update:
                fk.on_update = on_update.group(1).upper()

            table.foreign_keys.append(fk)

    def _parse_unique_constraint(self, sql: str, table: Table) -> None:
        """解析UNIQUE约束"""
        match = re.search(r'UNIQUE\s+(?:INDEX\s+)?(?:[`"\']?(\w+)[`"\']?\s*)?\(([^)]+)\)', sql, re.IGNORECASE)
        if match:
            index_name = match.group(1) or f"idx_{table.name}_{'_'.join(match.group(2).split(','))}"
            columns = [c.strip().strip('`"\'') for c in match.group(2).split(',')]
            table.indexes.append(Index(
                name=index_name,
                columns=columns,
                unique=True
            ))

    def _parse_index_constraint(self, sql: str, table: Table) -> None:
        """解析INDEX/KEY约束"""
        match = re.search(r'(?:INDEX|KEY)\s+(?:[`"\']?(\w+)[`"\']?\s*)?\(([^)]+)\)', sql, re.IGNORECASE)
        if match:
            index_name = match.group(1) or f"idx_{table.name}_{'_'.join(match.group(2).split(','))}"
            columns = [c.strip().strip('`"\'') for c in match.group(2).split(',')]
            table.indexes.append(Index(
                name=index_name,
                columns=columns,
                unique=False
            ))

    def _parse_constraint(self, sql: str, table: Table) -> None:
        """解析通用CONSTRAINT"""
        upper_sql = sql.upper()
        if "FOREIGN KEY" in upper_sql:
            self._parse_foreign_key(sql, table)
        elif "PRIMARY KEY" in upper_sql:
            self._parse_primary_key(sql, table)
        elif "UNIQUE" in upper_sql:
            self._parse_unique_constraint(sql, table)

    def _parse_alter_table(self, sql: str) -> None:
        """解析ALTER TABLE语句"""
        match = re.match(
            r'ALTER\s+TABLE\s+[`"\']?(\w+)[`"\']?\s+(.*)',
            sql,
            re.IGNORECASE | re.DOTALL
        )
        if not match:
            return

        table_name = match.group(1)
        action = match.group(2).strip()

        if table_name not in self.tables:
            return

        table = self.tables[table_name]
        upper_action = action.upper()

        if upper_action.startswith("ADD COLUMN") or upper_action.startswith("ADD"):
            # 提取列定义部分
            col_def = re.sub(r'^ADD\s+(?:COLUMN\s+)?', '', action, flags=re.IGNORECASE)
            # 检查是否是约束
            if any(col_def.upper().startswith(kw) for kw in ["CONSTRAINT", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "INDEX"]):
                # 作为CREATE TABLE体的一部分解析
                self._parse_constraint(col_def, table)
            else:
                column = self._parse_column_definition(col_def)
                if column:
                    table.columns[column.name] = column

        elif upper_action.startswith("DROP COLUMN") or upper_action.startswith("DROP"):
            col_name = re.sub(r'^DROP\s+(?:COLUMN\s+)?[`"\']?', '', action, flags=re.IGNORECASE)
            col_name = col_name.strip().strip('`"\'').split()[0]
            if col_name in table.columns:
                del table.columns[col_name]

        elif upper_action.startswith("MODIFY COLUMN") or upper_action.startswith("MODIFY") or \
             upper_action.startswith("ALTER COLUMN") or upper_action.startswith("CHANGE COLUMN") or \
             upper_action.startswith("CHANGE"):
            # 修改列
            if upper_action.startswith("CHANGE"):
                # CHANGE COLUMN old_name new_name type ...
                parts = re.sub(r'^CHANGE\s+(?:COLUMN\s+)?', '', action, flags=re.IGNORECASE)
                names = parts.split(None, 2)
                if len(names) >= 2:
                    old_name = names[0].strip('`"\'')
                    new_name = names[1].strip('`"\'')
                    col_def = names[2] if len(names) > 2 else ""
                    if old_name in table.columns:
                        del table.columns[old_name]
                    column = self._parse_column_definition(f"{new_name} {col_def}")
                    if column:
                        table.columns[column.name] = column
            else:
                col_def = re.sub(r'^(?:MODIFY|ALTER)\s+(?:COLUMN\s+)?', '', action, flags=re.IGNORECASE)
                column = self._parse_column_definition(col_def)
                if column:
                    table.columns[column.name] = column

    def _parse_create_index(self, sql: str) -> None:
        """解析CREATE INDEX语句"""
        match = re.match(
            r'CREATE\s+(UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\']?(\w+)[`"\']?\s+ON\s+[`"\']?(\w+)[`"\']?\s*\(([^)]+)\)',
            sql,
            re.IGNORECASE
        )
        if match:
            index_name = match.group(2)
            table_name = match.group(3)
            columns = [c.strip().strip('`"\'') for c in match.group(4).split(',')]

            if table_name in self.tables:
                self.tables[table_name].indexes.append(Index(
                    name=index_name,
                    columns=columns,
                    unique=bool(match.group(1))
                ))

    def parse_file(self, filepath: str) -> Dict[str, Table]:
        """从文件解析SQL DDL"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return self.parse(f.read())

    def to_dict(self) -> Dict[str, Any]:
        """将解析结果转为字典"""
        return {name: table.to_dict() for name, table in self.tables.items()}

    def to_json(self, indent: int = 2) -> str:
        """将解析结果转为JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def get_table(self, name: str) -> Optional[Table]:
        """获取指定表"""
        return self.tables.get(name)

    def get_column(self, table_name: str, column_name: str) -> Optional[Column]:
        """获取指定列"""
        table = self.tables.get(table_name)
        if table:
            return table.columns.get(column_name)
        return None
