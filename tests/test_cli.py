"""
CLI单元测试

测试命令行接口功能。
"""

import unittest
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemamap.cli.main import main, read_schema_file, create_parser, _main_with_error_handling


class TestCLI(unittest.TestCase):
    """测试CLI接口"""

    def setUp(self):
        """创建临时Schema文件"""
        self.old_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        self.new_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255)
        );
        """

        self.temp_dir = tempfile.mkdtemp()
        self.old_file = os.path.join(self.temp_dir, "old.sql")
        self.new_file = os.path.join(self.temp_dir, "new.sql")

        with open(self.old_file, 'w', encoding='utf-8') as f:
            f.write(self.old_sql)

        with open(self.new_file, 'w', encoding='utf-8') as f:
            f.write(self.new_sql)

    def tearDown(self):
        """清理临时文件"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_read_schema_file(self):
        """测试读取Schema文件"""
        content = read_schema_file(self.old_file)
        self.assertIn("CREATE TABLE users", content)

    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            read_schema_file("/nonexistent/file.sql")

    def test_parse_command(self):
        """测试parse命令"""
        exit_code = _main_with_error_handling(["parse", self.old_file, "--no-color"])
        self.assertEqual(exit_code, 0)

    def test_diff_command(self):
        """测试diff命令"""
        exit_code = _main_with_error_handling(["diff", self.old_file, self.new_file, "--no-color"])
        self.assertEqual(exit_code, 0)

    def test_diff_command_json_output(self):
        """测试diff命令JSON输出"""
        output_file = os.path.join(self.temp_dir, "diff.json")
        exit_code = _main_with_error_handling([
            "diff", self.old_file, self.new_file,
            "--format", "json",
            "--output", output_file,
            "--no-color"
        ])
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIn("summary", data)

    def test_analyze_command(self):
        """测试analyze命令"""
        exit_code = _main_with_error_handling(["analyze", self.old_file, self.new_file, "--no-color"])
        self.assertEqual(exit_code, 0)

    def test_migrate_command(self):
        """测试migrate命令"""
        exit_code = _main_with_error_handling([
            "migrate", self.old_file, self.new_file,
            "--dialect", "sqlite",
            "--no-color"
        ])
        self.assertEqual(exit_code, 0)

    def test_migrate_command_sql_format(self):
        """测试migrate命令SQL格式输出"""
        output_file = os.path.join(self.temp_dir, "migrate.sql")
        exit_code = _main_with_error_handling([
            "migrate", self.old_file, self.new_file,
            "--dialect", "postgresql",
            "--format", "sql",
            "--output", output_file,
            "--no-color"
        ])
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("Migration Script", content)

    def test_dashboard_command(self):
        """测试dashboard命令"""
        exit_code = _main_with_error_handling([
            "dashboard", self.old_file, self.new_file,
            "--dialect", "sqlite",
            "--no-color"
        ])
        self.assertEqual(exit_code, 0)

    def test_no_command(self):
        """测试无命令参数"""
        exit_code = _main_with_error_handling([])
        self.assertEqual(exit_code, 0)

    def test_version_flag(self):
        """测试--version标志"""
        with self.assertRaises(SystemExit) as cm:
            main(["--version"])
        self.assertEqual(cm.exception.code, 0)

    def test_invalid_file(self):
        """测试无效文件路径"""
        exit_code = _main_with_error_handling(["parse", "/nonexistent/file.sql", "--no-color"])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
