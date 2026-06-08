"""
变更检测器单元测试

测试Schema差异检测功能。
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemamap.parser.schema_parser import SchemaParser
from schemamap.detector.change_detector import ChangeDetector, ChangeType


class TestChangeDetector(unittest.TestCase):
    """测试变更检测器"""

    def setUp(self):
        self.detector = ChangeDetector()

    def _parse(self, sql):
        """辅助方法：解析SQL"""
        parser = SchemaParser()
        return parser.parse(sql)

    def test_no_changes(self):
        """测试无变更的情况"""
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        old = self._parse(sql)
        new = self._parse(sql)

        diff = self.detector.detect(old, new)
        self.assertEqual(diff.summary["total_changes"], 0)
        self.assertEqual(len(diff.table_diffs), 1)
        self.assertEqual(diff.table_diffs[0].change_type, ChangeType.UNCHANGED)

    def test_add_table(self):
        """测试新增表"""
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
        diff = self.detector.detect(self._parse(old_sql), self._parse(new_sql))

        self.assertEqual(diff.summary["tables_added"], 1)
        self.assertEqual(diff.summary["total_changes"], 1)

        added_table = next((t for t in diff.table_diffs if t.change_type == ChangeType.ADDED), None)
        self.assertIsNotNone(added_table)
        self.assertEqual(added_table.name, "posts")

    def test_remove_table(self):
        """测试删除表"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );

        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            title VARCHAR(255)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        diff = self.detector.detect(self._parse(old_sql), self._parse(new_sql))

        self.assertEqual(diff.summary["tables_removed"], 1)

        removed_table = next((t for t in diff.table_diffs if t.change_type == ChangeType.REMOVED), None)
        self.assertIsNotNone(removed_table)
        self.assertEqual(removed_table.name, "posts")

    def test_add_column(self):
        """测试新增列"""
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
        diff = self.detector.detect(self._parse(old_sql), self._parse(new_sql))

        self.assertEqual(diff.summary["columns_added"], 1)

        table_diff = diff.table_diffs[0]
        self.assertEqual(table_diff.change_type, ChangeType.MODIFIED)
        self.assertEqual(len(table_diff.column_diffs), 1)
        self.assertEqual(table_diff.column_diffs[0].change_type, ChangeType.ADDED)

    def test_remove_column(self):
        """测试删除列"""
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
        diff = self.detector.detect(self._parse(old_sql), self._parse(new_sql))

        self.assertEqual(diff.summary["columns_removed"], 1)

    def test_modify_column_type(self):
        """测试修改列类型"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        """
        diff = self.detector.detect(self._parse(old_sql), self._parse(new_sql))

        self.assertEqual(diff.summary["columns_modified"], 1)

        col_diff = diff.table_diffs[0].column_diffs[0]
        self.assertIn("data_type", col_diff.property_changes)
        self.assertEqual(col_diff.property_changes["data_type"]["old"], "VARCHAR")
        self.assertEqual(col_diff.property_changes["data_type"]["new"], "TEXT")

    def test_modify_column_nullable(self):
        """测试修改列可空性"""
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
        diff = self.detector.detect(self._parse(old_sql), self._parse(new_sql))

        self.assertEqual(diff.summary["columns_modified"], 1)

        col_diff = diff.table_diffs[0].column_diffs[0]
        self.assertIn("nullable", col_diff.property_changes)
        self.assertTrue(col_diff.property_changes["nullable"]["old"])
        self.assertFalse(col_diff.property_changes["nullable"]["new"])

    def test_primary_key_change(self):
        """测试主键变更"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER,
            name VARCHAR(100),
            PRIMARY KEY (id, name)
        );
        """
        diff = self.detector.detect(self._parse(old_sql), self._parse(new_sql))

        self.assertEqual(diff.summary["primary_keys_changed"], 1)
        table_diff = diff.table_diffs[0]
        self.assertTrue(table_diff.primary_key_changed)

    def test_risky_changes(self):
        """测试高风险变更检测"""
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
        diff = self.detector.detect(self._parse(old_sql), self._parse(new_sql))
        risky = self.detector.get_risky_changes(diff)

        self.assertTrue(len(risky) > 0)
        self.assertEqual(risky[0]["type"], "column_removed")
        self.assertEqual(risky[0]["risk"], "high")

    def test_to_dict(self):
        """测试导出字典"""
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
        diff = self.detector.detect(self._parse(old_sql), self._parse(new_sql))
        result = diff.to_dict()

        self.assertIn("summary", result)
        self.assertIn("tables", result)
        self.assertEqual(result["summary"]["columns_added"], 1)


if __name__ == "__main__":
    unittest.main()
