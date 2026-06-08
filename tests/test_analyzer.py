"""
影响分析引擎单元测试

测试Schema变更影响分析功能。
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemamap.parser.schema_parser import SchemaParser
from schemamap.detector.change_detector import ChangeDetector
from schemamap.analyzer.impact_analyzer import ImpactAnalyzer, RiskLevel, ImpactCategory


class TestImpactAnalyzer(unittest.TestCase):
    """测试影响分析引擎"""

    def setUp(self):
        self.analyzer = ImpactAnalyzer()
        self.detector = ChangeDetector()

    def _analyze(self, old_sql, new_sql):
        """辅助方法：执行完整分析"""
        old_parser = SchemaParser()
        new_parser = SchemaParser()
        old_schema = old_parser.parse(old_sql)
        new_schema = new_parser.parse(new_sql)
        diff = self.detector.detect(old_schema, new_schema)
        return self.analyzer.analyze(diff)

    def test_no_changes(self):
        """测试无变更的情况"""
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        report = self._analyze(sql, sql)

        self.assertEqual(report.summary["overall_risk_level"], "low")
        self.assertEqual(report.statistics["total_items"], 1)  # 向后兼容信息

    def test_add_table_impact(self):
        """测试新增表的影响分析"""
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
        report = self._analyze(old_sql, new_sql)

        orm_items = [i for i in report.items if i.category == ImpactCategory.ORM_MODEL]
        self.assertTrue(len(orm_items) > 0)

        # 新增表应该是INFO级别
        add_items = [i for i in orm_items if i.risk_level == RiskLevel.INFO]
        self.assertTrue(len(add_items) > 0)

    def test_remove_table_impact(self):
        """测试删除表的影响分析"""
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
        report = self._analyze(old_sql, new_sql)

        # 应该有高风险项
        high_risk_items = [i for i in report.items if i.risk_level == RiskLevel.HIGH]
        self.assertTrue(len(high_risk_items) > 0)

        # 检查ORM影响
        orm_items = [i for i in report.items if i.category == ImpactCategory.ORM_MODEL]
        self.assertTrue(len(orm_items) > 0)

    def test_add_column_impact(self):
        """测试新增列的影响分析"""
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
        report = self._analyze(old_sql, new_sql)

        orm_items = [i for i in report.items if i.category == ImpactCategory.ORM_MODEL]
        self.assertTrue(len(orm_items) > 0)

        # 新增列应该是低风险
        low_risk = [i for i in orm_items if i.risk_level == RiskLevel.LOW]
        self.assertTrue(len(low_risk) > 0)

    def test_remove_column_impact(self):
        """测试删除列的影响分析"""
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
        report = self._analyze(old_sql, new_sql)

        # 应该有高风险项
        high_risk = [i for i in report.items if i.risk_level == RiskLevel.HIGH]
        self.assertTrue(len(high_risk) > 0)

        # 检查SQL查询影响
        sql_items = [i for i in report.items if i.category == ImpactCategory.SQL_QUERY]
        self.assertTrue(len(sql_items) > 0)

    def test_column_type_change_impact(self):
        """测试列类型变更的影响分析"""
        old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            age INTEGER
        );
        """
        new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            age VARCHAR(10)
        );
        """
        report = self._analyze(old_sql, new_sql)

        # 应该有中等风险
        medium_risk = [i for i in report.items if i.risk_level == RiskLevel.MEDIUM]
        self.assertTrue(len(medium_risk) > 0)

    def test_not_null_change_impact(self):
        """测试NOT NULL变更的影响分析"""
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
        report = self._analyze(old_sql, new_sql)

        # 应该有数据完整性影响
        integrity_items = [i for i in report.items if i.category == ImpactCategory.DATA_INTEGRITY]
        self.assertTrue(len(integrity_items) > 0)

        # 应该是高风险
        high_risk = [i for i in integrity_items if i.risk_level == RiskLevel.HIGH]
        self.assertTrue(len(high_risk) > 0)

    def test_backward_compatibility(self):
        """测试向后兼容性分析"""
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
        report = self._analyze(old_sql, new_sql)

        # 向后兼容的变更
        compat_items = [i for i in report.items if i.category == ImpactCategory.BACKWARD_COMPATIBILITY]
        self.assertTrue(len(compat_items) > 0)
        self.assertEqual(compat_items[0].risk_level, RiskLevel.INFO)

    def test_breaking_change_detection(self):
        """测试破坏性变更检测"""
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
        report = self._analyze(old_sql, new_sql)

        compat_items = [i for i in report.items if i.category == ImpactCategory.BACKWARD_COMPATIBILITY]
        self.assertTrue(len(compat_items) > 0)
        self.assertEqual(compat_items[0].risk_level, RiskLevel.HIGH)

    def test_to_json(self):
        """测试导出JSON"""
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
        report = self._analyze(old_sql, new_sql)
        json_str = report.to_json()

        self.assertIn("summary", json_str)
        self.assertIn("items", json_str)
        self.assertIn("statistics", json_str)

    def test_statistics(self):
        """测试统计信息"""
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
        report = self._analyze(old_sql, new_sql)

        self.assertIn("total_items", report.statistics)
        self.assertIn("by_category", report.statistics)
        self.assertGreater(report.statistics["total_items"], 0)


if __name__ == "__main__":
    unittest.main()
