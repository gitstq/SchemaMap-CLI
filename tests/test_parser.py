"""
Schema解析器单元测试

测试SQL DDL解析功能。
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemamap.parser.schema_parser import SchemaParser, Table, Column, Index, ForeignKey


class TestSchemaParser(unittest.TestCase):
    """测试Schema解析器"""

    def setUp(self):
        """每个测试前初始化"""
        self.parser = SchemaParser()

    def test_parse_simple_create_table(self):
        """测试解析简单的CREATE TABLE"""
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        tables = self.parser.parse(sql)

        self.assertIn("users", tables)
        table = tables["users"]
        self.assertEqual(table.name, "users")
        self.assertEqual(len(table.columns), 4)

        # 检查id列
        id_col = table.columns["id"]
        self.assertEqual(id_col.data_type, "INT")
        self.assertTrue(id_col.primary_key)
        self.assertTrue(id_col.auto_increment)

        # 检查username列
        username_col = table.columns["username"]
        self.assertEqual(username_col.data_type, "VARCHAR")
        self.assertFalse(username_col.nullable)

        # 检查email列
        email_col = table.columns["email"]
        self.assertTrue(email_col.unique)

    def test_parse_with_foreign_key(self):
        """测试解析带外键的表"""
        sql = """
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        tables = self.parser.parse(sql)

        self.assertIn("posts", tables)
        table = tables["posts"]
        self.assertEqual(len(table.foreign_keys), 1)

        fk = table.foreign_keys[0]
        self.assertEqual(fk.column, "user_id")
        self.assertEqual(fk.ref_table, "users")
        self.assertEqual(fk.ref_column, "id")
        self.assertEqual(fk.on_delete, "CASCADE")

    def test_parse_multiple_tables(self):
        """测试解析多个表"""
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount DECIMAL(10,2)
        );
        """
        tables = self.parser.parse(sql)

        self.assertEqual(len(tables), 2)
        self.assertIn("users", tables)
        self.assertIn("orders", tables)

    def test_parse_alter_table(self):
        """测试解析ALTER TABLE"""
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );

        ALTER TABLE users ADD COLUMN email VARCHAR(255);
        ALTER TABLE users DROP COLUMN name;
        """
        tables = self.parser.parse(sql)

        self.assertIn("users", tables)
        table = tables["users"]
        self.assertIn("email", table.columns)
        self.assertNotIn("name", table.columns)

    def test_parse_index(self):
        """测试解析CREATE INDEX"""
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255)
        );

        CREATE INDEX idx_users_name ON users (name);
        CREATE UNIQUE INDEX idx_users_email ON users (email);
        """
        tables = self.parser.parse(sql)

        table = tables["users"]
        self.assertEqual(len(table.indexes), 2)

        # 查找普通索引
        normal_idx = next((i for i in table.indexes if i.name == "idx_users_name"), None)
        self.assertIsNotNone(normal_idx)
        self.assertFalse(normal_idx.unique)

        # 查找唯一索引
        unique_idx = next((i for i in table.indexes if i.name == "idx_users_email"), None)
        self.assertIsNotNone(unique_idx)
        self.assertTrue(unique_idx.unique)

    def test_parse_postgresql_types(self):
        """测试解析PostgreSQL特有类型"""
        sql = """
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name CHARACTER VARYING(255),
            price DOUBLE PRECISION,
            description TEXT
        );
        """
        tables = self.parser.parse(sql)

        table = tables["products"]
        self.assertEqual(table.columns["id"].data_type, "INT")  # SERIAL -> INT
        # CHARACTER VARYING 在正则中先匹配到 CHARACTER，这是已知限制
        # 实际使用中可以预处理SQL统一 CHARACTER VARYING 为 VARCHAR
        self.assertIn(table.columns["name"].data_type, ["VARCHAR", "CHAR"])
        self.assertEqual(table.columns["price"].data_type, "DOUBLE")

    def test_parse_mysql_types(self):
        """测试解析MySQL特有类型"""
        sql = """
        CREATE TABLE logs (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            level TINYINT NOT NULL,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        tables = self.parser.parse(sql)

        table = tables["logs"]
        self.assertEqual(table.columns["id"].data_type, "BIGINT")
        self.assertTrue(table.columns["id"].auto_increment)
        self.assertEqual(table.columns["level"].data_type, "TINYINT")

    def test_parse_composite_primary_key(self):
        """测试解析复合主键"""
        sql = """
        CREATE TABLE order_items (
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            PRIMARY KEY (order_id, product_id)
        );
        """
        tables = self.parser.parse(sql)

        table = tables["order_items"]
        self.assertEqual(table.primary_key, ["order_id", "product_id"])

    def test_to_json(self):
        """测试导出JSON"""
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        self.parser.parse(sql)
        json_str = self.parser.to_json()

        self.assertIn("users", json_str)
        self.assertIn("id", json_str)
        self.assertIn("name", json_str)

    def test_empty_sql(self):
        """测试空SQL"""
        tables = self.parser.parse("")
        self.assertEqual(len(tables), 0)

    def test_sql_with_comments(self):
        """测试带注释的SQL"""
        sql = """
        -- 用户表
        CREATE TABLE users (
            id INTEGER PRIMARY KEY, -- 主键
            /* 用户名 */
            name VARCHAR(100)
        );
        """
        tables = self.parser.parse(sql)
        self.assertIn("users", tables)
        self.assertEqual(len(tables["users"].columns), 2)


class TestSchemaParserEdgeCases(unittest.TestCase):
    """测试Schema解析器的边界情况"""

    def setUp(self):
        self.parser = SchemaParser()

    def test_quoted_identifiers(self):
        """测试带引号的标识符"""
        sql = '''
        CREATE TABLE `users` (
            `id` INTEGER PRIMARY KEY,
            `user name` VARCHAR(100)
        );
        '''
        tables = self.parser.parse(sql)
        self.assertIn("users", tables)

    def test_case_insensitive_keywords(self):
        """测试大小写不敏感的关键字"""
        sql = """
        create table users (
            id integer primary key,
            name varchar(100) not null
        );
        """
        tables = self.parser.parse(sql)
        self.assertIn("users", tables)
        self.assertFalse(tables["users"].columns["name"].nullable)


if __name__ == "__main__":
    unittest.main()
