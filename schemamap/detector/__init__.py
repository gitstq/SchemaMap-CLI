"""变更检测器模块 - 对比两个Schema版本，识别差异"""

from .change_detector import ChangeDetector, SchemaDiff, TableDiff, ColumnDiff

__all__ = ["ChangeDetector", "SchemaDiff", "TableDiff", "ColumnDiff"]
