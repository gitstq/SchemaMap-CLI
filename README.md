# SchemaMap-CLI

轻量级数据库Schema变更影响分析与智能迁移引擎

专注于数据库Schema变更时的影响分析、依赖追踪和智能迁移脚本生成。

## 核心特性

- **Schema解析器**：解析SQL DDL语句，提取表、列、索引、外键信息
- **变更检测器**：对比两个Schema版本，识别新增/删除/修改的表、列、索引
- **影响分析引擎**：
  - 分析Schema变更对ORM模型的影响
  - 分析对API接口（REST/GraphQL）的影响
  - 分析对SQL查询语句的影响
  - 生成风险等级评估（高/中/低）
- **迁移脚本生成器**：基于变更生成安全的迁移SQL脚本
- **TUI仪表盘**：美观的终端交互界面

## 技术栈

- Python 3.8+
- 零外部依赖（纯标准库）
- 支持的数据库：SQLite、PostgreSQL、MySQL（通过SQL解析）
- 输出格式：终端TUI、JSON、Markdown、HTML

## 安装

```bash
# 从源码安装
git clone https://github.com/gitstq/SchemaMap-CLI.git
cd SchemaMap-CLI
pip install .

# 或使用构建脚本
chmod +x build.sh
./build.sh
```

## 快速开始

```bash
# 解析Schema文件
schemamap parse examples/v1_schema.sql

# 对比两个Schema版本
schemamap diff examples/v1_schema.sql examples/v2_schema.sql

# 完整影响分析
schemamap analyze examples/v1_schema.sql examples/v2_schema.sql

# 生成迁移脚本
schemamap migrate examples/v1_schema.sql examples/v2_schema.sql --dialect mysql

# TUI仪表盘展示
schemamap dashboard examples/v1_schema.sql examples/v2_schema.sql
```

## 命令详解

### parse - 解析Schema

```bash
schemamap parse schema.sql
schemamap parse schema.sql -o output.json
```

### diff - 差异对比

```bash
schemamap diff old.sql new.sql
schemamap diff old.sql new.sql -f markdown -o diff.md
schemamap diff old.sql new.sql -f html -o diff.html
```

### analyze - 影响分析

```bash
schemamap analyze old.sql new.sql
schemamap analyze old.sql new.sql -f json -o analysis.json
```

### migrate - 迁移脚本

```bash
schemamap migrate old.sql new.sql --dialect sqlite
schemamap migrate old.sql new.sql --dialect postgresql -f sql -o migrate.sql
schemamap migrate old.sql new.sql --dialect mysql
```

### dashboard - TUI仪表盘

```bash
schemamap dashboard old.sql new.sql --dialect sqlite
```

## 输出格式

支持以下输出格式：

- **终端TUI**：彩色终端界面，适合人工查看
- **JSON**：结构化数据，适合程序处理
- **Markdown**：文档格式，适合放入Wiki或PR描述
- **HTML**：网页格式，适合分享和存档
- **SQL**：迁移脚本，可直接执行

## 项目结构

```
schemamap-cli/
├── schemamap/
│   ├── __init__.py
│   ├── parser/           # Schema解析器
│   │   ├── __init__.py
│   │   └── schema_parser.py
│   ├── detector/         # 变更检测器
│   │   ├── __init__.py
│   │   └── change_detector.py
│   ├── analyzer/         # 影响分析引擎
│   │   ├── __init__.py
│   │   └── impact_analyzer.py
│   ├── generator/        # 迁移脚本生成器
│   │   ├── __init__.py
│   │   └── migration_generator.py
│   ├── tui/              # TUI仪表盘
│   │   ├── __init__.py
│   │   └── dashboard.py
│   └── cli/              # CLI入口
│       ├── __init__.py
│       └── main.py
├── tests/                # 单元测试
│   ├── test_parser.py
│   ├── test_detector.py
│   ├── test_analyzer.py
│   ├── test_generator.py
│   └── test_cli.py
├── examples/             # 示例数据
│   ├── v1_schema.sql
│   └── v2_schema.sql
├── pyproject.toml
├── setup.py
├── requirements.txt
├── build.sh
└── README.md
```

## 开发

```bash
# 运行单元测试
python -m unittest discover -s tests -v

# 构建分发包
python setup.py sdist bdist_wheel
```

## 与其他工具的差异化

- **SchemaDrift-Pilot**：Schema漂移检测
- **SchemaPilot**：JSON Schema验证
- **SchemaViz**：数据库Schema可视化
- **SchemaSync-CLI**：Schema迁移

**SchemaMap-CLI** 的差异化：专注于 **Schema变更影响分析** —— 当数据库Schema发生变更时，自动分析该变更对应用代码、API接口、ORM模型、查询语句的影响范围，生成影响报告和适配建议。

## License

MIT License
