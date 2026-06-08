"""迁移脚本生成器模块 - 基于变更生成安全的迁移SQL脚本"""

from .migration_generator import MigrationGenerator, MigrationScript

__all__ = ["MigrationGenerator", "MigrationScript"]
