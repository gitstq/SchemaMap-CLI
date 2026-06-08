"""
迁移脚本生成器单元测试

测试迁移SQL脚本生成功能。
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemamap.parser.schema_parser import SchemaParser
from schemamap.detector.change_detector import ChangeDetector
from schemamap.generator.migration_generator import MigrationGenerator, Dialect


class TestMigrationGenerator(unittest.TestCase):
    """测试迁移脚本生成器"""

    def setUp(self):
        self.detector = ChangeDetector()

    def _generate(self, old_sql, new_sql, dialect=Dialect.SQLITE):
        """辅助方法：生成迁移脚本"""
        old_parser = SchemaParser()
        new_parser = SchemaParser()
        old_schema = old_parser.parse(old_sql)
        new_schema = new_parser.parse(new_sql)
        diff = self.detector.detect(old_schema, new_schema)
        generator = MigrationGenerator(dialect=dialect)
        return generator.generate(diff)

    def test_add_table_sqlite(self):
        """测试SQLite新增表"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );

        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            title VARCHAR(255)
        );
        """
        script = self._generate(old_sql, new_sql, Dialect.SQLITE)

        up_sql = " ".join(script.up_statements)
        self.assertIn("CREATE TABLE posts", up_sql)

        down_sql = " ".join(script.down_statements)
        self.assertIn("DROP TABLE", down_sql)

    def test_add_column_sqlite(self):
        """测试SQLite新增列"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255)
        );
        """
        script = self._generate(old_sql, new_sql, Dialect.SQLITE)

        up_sql = " ".join(script.up_statements)
        self.assertIn("ALTER TABLE users ADD COLUMN", up_sql)
        self.assertIn("email", up_sql)

    def test_drop_column_postgresql(self):
        """测试PostgreSQL删除列"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        script = self._generate(old_sql, new_sql, Dialect.POSTGRESQL)

        up_sql = " ".join(script.up_statements)
        self.assertIn("ALTER TABLE users DROP COLUMN email", up_sql)

        # 应该有警告
        self.assertTrue(len(script.warnings) > 0)

    def test_modify_column_mysql(self):
        """测试MySQL修改列"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        );
        """
        script = self._generate(old_sql, new_sql, Dialect.MYSQL)

        up_sql = " ".join(script.up_statements)
        self.assertIn("MODIFY COLUMN", up_sql)
        self.assertIn("NOT NULL", up_sql)

    def test_add_index(self):
        """测试新增索引"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );

        CREATE INDEX idx_users_name ON users (name);
        """
        script = self._generate(old_sql, new_sql, Dialect.SQLITE)

        up_sql = " ".join(script.up_statements)
        self.assertIn("CREATE INDEX idx_users_name", up_sql)

    def test_to_sql(self):
        """测试生成完整SQL"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );

        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            title VARCHAR(255)
        );
        """
        script = self._generate(old_sql, new_sql, Dialect.SQLITE)
        sql = script.to_sql()

        self.assertIn("BEGIN TRANSACTION", sql)
        self.assertIn("COMMIT", sql)
        self.assertIn("UP MIGRATION", sql)
        self.assertIn("DOWN MIGRATION", sql)

    def test_all_dialects(self):
        """测试所有方言"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255)
        );
        """

        for dialect in Dialect:
            script = self._generate(old_sql, new_sql, dialect)
            self.assertEqual(script.dialect, dialect)
            self.assertTrue(len(script.up_statements) > 0)

    def test_warnings_for_destructive_changes(self):
        """测试破坏性变更的警告"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        script = self._generate(old_sql, new_sql, Dialect.POSTGRESQL)

        self.assertTrue(len(script.warnings) > 0)
        warnings_str = " ".join(script.warnings)
        self.assertIn("permanently delete", warnings_str.lower())


if __name__ == "__main__":
    unittest.main()
