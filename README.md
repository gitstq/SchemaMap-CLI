# 🗺️ SchemaMap-CLI

<p align="center">
  <b>轻量级数据库Schema变更影响分析与智能迁移引擎</b><br>
  <b>Lightweight Database Schema Change Impact Analysis & Intelligent Migration Engine</b><br>
  <b>輕量級數據庫Schema變更影響分析與智能遷移引擎</b>
</p>

<p align="center">
  <a href="#-简体中文">简体中文</a> |
  <a href="#-繁體中文">繁體中文</a> |
  <a href="#-english">English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Dependencies-Zero-brightgreen.svg" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Platform-Cross--platform-lightgrey.svg" alt="Cross Platform">
</p>

---

## 🇨🇳 简体中文

### 🎉 项目介绍

SchemaMap-CLI 是一款专注于**数据库Schema变更影响分析**的轻量级终端工具。当数据库Schema发生变更时，它能够自动分析该变更对应用代码、API接口、ORM模型、查询语句的影响范围，生成详细的影响报告和适配建议。

**灵感来源**：在日常开发中，数据库Schema变更往往牵一发而动全身。开发者需要手动检查ORM模型、API接口、业务逻辑代码是否需要同步更新，这个过程既繁琐又容易遗漏。SchemaMap-CLI 旨在自动化这一流程，让Schema变更的影响一目了然。

**自研差异化亮点**：
- 🎯 **专注影响分析**：不同于Schema漂移检测或可视化工具，SchemaMap-CLI 专注于分析Schema变更对上层应用的影响
- 🧠 **智能风险评估**：自动评估每个变更的风险等级（高/中/低），并提供具体的适配建议
- 💡 **ORM代码生成**：自动生成SQLAlchemy、Django ORM等框架的模型代码片段
- 🛡️ **破坏性变更检测**：自动识别可能导致生产事故的破坏性变更

### ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🔍 **Schema解析器** | 解析SQL DDL语句，提取表、列、索引、外键、约束等完整信息 |
| 🔄 **变更检测器** | 对比两个Schema版本，精准识别新增/删除/修改的表、列、索引 |
| 🧠 **影响分析引擎** | 分析Schema变更对ORM模型、API接口、SQL查询的影响范围 |
| ⚠️ **风险评估** | 自动生成风险等级评估（🔴高/🟡中/🟢低） |
| 📝 **迁移脚本生成** | 基于变更生成SQLite/PostgreSQL/MySQL安全迁移SQL脚本 |
| 🎨 **TUI仪表盘** | 美观的终端交互界面，彩色展示分析结果 |
| 📊 **多格式输出** | 支持JSON/Markdown/HTML/SQL等多种输出格式 |
| 🚀 **零依赖** | 纯Python标准库实现，无需安装任何第三方包 |

### 🚀 快速开始

#### 环境要求

- Python 3.8 或更高版本
- 无需任何外部依赖

#### 安装

```bash
# 从源码安装
git clone https://github.com/gitstq/SchemaMap-CLI.git
cd SchemaMap-CLI
pip install .

# 或直接运行（无需安装）
python3 -m schemamap.cli.main --help
```

#### 基本使用

```bash
# 📋 解析Schema文件
schemamap parse examples/v1_schema.sql

# 🔍 对比两个Schema版本
schemamap diff examples/v1_schema.sql examples/v2_schema.sql

# 🧠 完整影响分析（JSON格式）
schemamap analyze examples/v1_schema.sql examples/v2_schema.sql -f json

# 📝 生成迁移脚本
schemamap migrate examples/v1_schema.sql examples/v2_schema.sql -f sql -o migrate.sql

# 🎨 TUI仪表盘展示
schemamap dashboard examples/v1_schema.sql examples/v2_schema.sql
```

### 📖 详细使用指南

#### 命令详解

**`parse` - 解析Schema文件**

```bash
# 解析并输出到终端
schemamap parse schema.sql

# 解析并保存为JSON
schemamap parse schema.sql -o schema.json
```

**`diff` - Schema差异对比**

```bash
# 终端彩色输出
schemamap diff old.sql new.sql

# Markdown格式输出
schemamap diff old.sql new.sql -f markdown -o diff.md

# HTML格式输出
schemamap diff old.sql new.sql -f html -o diff.html
```

**`analyze` - 影响分析**

```bash
# JSON格式（默认）
schemamap analyze old.sql new.sql

# Markdown格式
schemamap analyze old.sql new.sql -f markdown -o analysis.md

# HTML格式
schemamap analyze old.sql new.sql -f html -o analysis.html
```

**`migrate` - 生成迁移脚本**

```bash
# SQLite方言
schemamap migrate old.sql new.sql -f sql --dialect sqlite

# PostgreSQL方言
schemamap migrate old.sql new.sql -f sql --dialect postgresql -o migrate.sql

# MySQL方言
schemamap migrate old.sql new.sql -f sql --dialect mysql
```

**`dashboard` - TUI仪表盘**

```bash
# 启动交互式仪表盘
schemamap dashboard old.sql new.sql
```

#### 典型使用场景

**场景1：Code Review时评估Schema变更影响**

```bash
schemamap analyze schema_v1.sql schema_v2.sql -f markdown -o impact_report.md
```

将生成的Markdown报告附在PR描述中，让Reviewer快速了解变更影响。

**场景2：生成安全的生产环境迁移脚本**

```bash
schemamap migrate production_schema.sql new_schema.sql -f sql --dialect postgresql -o safe_migration.sql
```

工具会自动添加事务包裹、破坏性变更警告和回滚建议。

**场景3：CI/CD流水线集成**

```bash
schemamap analyze base_schema.sql pr_schema.sql -f json -o analysis.json
# 后续步骤可解析analysis.json进行自动化判断
```

### 💡 设计思路与迭代规划

#### 技术选型原因

- **纯标准库实现**：确保零依赖、跨平台、易部署，适合CI/CD环境
- **SQL解析而非数据库连接**：无需真实数据库连接，离线即可分析
- **多方言支持**：覆盖SQLite、PostgreSQL、MySQL三大主流数据库

#### 后续迭代计划

- [ ] 支持更多数据库方言（SQL Server、Oracle、MongoDB）
- [ ] 集成AI能力，生成更智能的适配建议
- [ ] 支持从ORM模型反向生成Schema变更分析
- [ ] Web UI版本，提供可视化Schema对比
- [ ] 插件系统，支持自定义影响分析规则

### 📦 打包与部署

```bash
# 一键构建
chmod +x build.sh
./build.sh

# 手动构建
python3 setup.py sdist bdist_wheel

# 安装构建包
pip3 install dist/schemamap-*.whl
```

### 🤝 贡献指南

欢迎提交Issue和PR！请遵循以下规范：

- 提交前运行所有单元测试：`python3 -m unittest discover tests -v`
- 代码风格遵循PEP8
- 提交信息使用Angular规范：`feat:`, `fix:`, `docs:`, `refactor:`

### 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🇹🇼 繁體中文

### 🎉 項目介紹

SchemaMap-CLI 是一款專注於**資料庫Schema變更影響分析**的輕量級終端工具。當資料庫Schema發生變更時，它能夠自動分析該變更對應用程式碼、API接口、ORM模型、查詢語句的影響範圍，生成詳細的影響報告和適配建議。

**自研差異化亮點**：
- 🎯 **專注影響分析**：不同於Schema漂移檢測或可視化工具，SchemaMap-CLI 專注於分析Schema變更對上層應用的影響
- 🧠 **智能風險評估**：自動評估每個變更的風險等級（高/中/低），並提供具體的適配建議
- 💡 **ORM代碼生成**：自動生成SQLAlchemy、Django ORM等框架的模型代碼片段
- 🛡️ **破壞性變更檢測**：自動識別可能導致生產事故的破壞性變更

### ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🔍 **Schema解析器** | 解析SQL DDL語句，提取表、列、索引、外鍵、約束等完整資訊 |
| 🔄 **變更檢測器** | 對比兩個Schema版本，精準識別新增/刪除/修改的表、列、索引 |
| 🧠 **影響分析引擎** | 分析Schema變更對ORM模型、API接口、SQL查詢的影響範圍 |
| ⚠️ **風險評估** | 自動生成風險等級評估（🔴高/🟡中/🟢低） |
| 📝 **遷移腳本生成** | 基於變更生成SQLite/PostgreSQL/MySQL安全遷移SQL腳本 |
| 🎨 **TUI儀表板** | 美觀的終端交互界面，彩色展示分析結果 |
| 📊 **多格式輸出** | 支持JSON/Markdown/HTML/SQL等多種輸出格式 |
| 🚀 **零依賴** | 純Python標準庫實現，無需安裝任何第三方包 |

### 🚀 快速開始

#### 環境要求

- Python 3.8 或更高版本
- 無需任何外部依賴

#### 安裝

```bash
# 從源碼安裝
git clone https://github.com/gitstq/SchemaMap-CLI.git
cd SchemaMap-CLI
pip install .

# 或直接運行（無需安裝）
python3 -m schemamap.cli.main --help
```

#### 基本使用

```bash
# 解析Schema文件
schemamap parse examples/v1_schema.sql

# 對比兩個Schema版本
schemamap diff examples/v1_schema.sql examples/v2_schema.sql

# 完整影響分析（JSON格式）
schemamap analyze examples/v1_schema.sql examples/v2_schema.sql -f json

# 生成遷移腳本
schemamap migrate examples/v1_schema.sql examples/v2_schema.sql -f sql -o migrate.sql

# TUI儀表板展示
schemamap dashboard examples/v1_schema.sql examples/v2_schema.sql
```

### 📖 詳細使用指南

#### 命令詳解

**`parse` - 解析Schema文件**

```bash
# 解析並輸出到終端
schemamap parse schema.sql

# 解析並保存為JSON
schemamap parse schema.sql -o schema.json
```

**`diff` - Schema差異對比**

```bash
# 終端彩色輸出
schemamap diff old.sql new.sql

# Markdown格式輸出
schemamap diff old.sql new.sql -f markdown -o diff.md

# HTML格式輸出
schemamap diff old.sql new.sql -f html -o diff.html
```

**`analyze` - 影響分析**

```bash
# JSON格式（預設）
schemamap analyze old.sql new.sql

# Markdown格式
schemamap analyze old.sql new.sql -f markdown -o analysis.md

# HTML格式
schemamap analyze old.sql new.sql -f html -o analysis.html
```

**`migrate` - 生成遷移腳本**

```bash
# SQLite方言
schemamap migrate old.sql new.sql -f sql --dialect sqlite

# PostgreSQL方言
schemamap migrate old.sql new.sql -f sql --dialect postgresql -o migrate.sql

# MySQL方言
schemamap migrate old.sql new.sql -f sql --dialect mysql
```

**`dashboard` - TUI儀表板**

```bash
# 啟動交互式儀表板
schemamap dashboard old.sql new.sql
```

#### 典型使用場景

**場景1：Code Review時評估Schema變更影響**

```bash
schemamap analyze schema_v1.sql schema_v2.sql -f markdown -o impact_report.md
```

將生成的Markdown報告附在PR描述中，讓Reviewer快速了解變更影響。

**場景2：生成安全的生產環境遷移腳本**

```bash
schemamap migrate production_schema.sql new_schema.sql -f sql --dialect postgresql -o safe_migration.sql
```

工具會自動添加事務包裹、破壞性變更警告和回滾建議。

**場景3：CI/CD流水線集成**

```bash
schemamap analyze base_schema.sql pr_schema.sql -f json -o analysis.json
# 後續步驟可解析analysis.json進行自動化判斷
```

### 💡 設計思路與迭代規劃

#### 技術選型原因

- **純標準庫實現**：確保零依賴、跨平台、易部署，適合CI/CD環境
- **SQL解析而非資料庫連接**：無需真實資料庫連接，離線即可分析
- **多方言支持**：覆蓋SQLite、PostgreSQL、MySQL三大主流資料庫

#### 後續迭代計劃

- [ ] 支持更多資料庫方言（SQL Server、Oracle、MongoDB）
- [ ] 集成AI能力，生成更智能的適配建議
- [ ] 支持從ORM模型反向生成Schema變更分析
- [ ] Web UI版本，提供可視化Schema對比
- [ ] 插件系統，支持自定義影響分析規則

### 📦 打包與部署

```bash
# 一鍵構建
chmod +x build.sh
./build.sh

# 手動構建
python3 setup.py sdist bdist_wheel

# 安裝構建包
pip3 install dist/schemamap-*.whl
```

### 🤝 貢獻指南

歡迎提交Issue和PR！請遵循以下規範：

- 提交前運行所有單元測試：`python3 -m unittest discover tests -v`
- 代碼風格遵循PEP8
- 提交信息使用Angular規範：`feat:`、`fix:`、`docs:`、`refactor:`

### 📄 開源協議

本項目採用 [MIT License](LICENSE) 開源協議。

---

## 🇬🇧 English

### 🎉 Introduction

SchemaMap-CLI is a lightweight terminal tool focused on **database schema change impact analysis**. When database schema changes occur, it automatically analyzes the impact on application code, API interfaces, ORM models, and SQL queries, generating detailed impact reports and adaptation suggestions.

**Inspiration**: In daily development, database schema changes often have far-reaching consequences. Developers need to manually check whether ORM models, API interfaces, and business logic code need to be updated, which is tedious and error-prone. SchemaMap-CLI aims to automate this process, making schema change impacts clear at a glance.

**Key Differentiators**:
- 🎯 **Impact-Focused Analysis**: Unlike schema drift detection or visualization tools, SchemaMap-CLI focuses on analyzing how schema changes affect upstream applications
- 🧠 **Intelligent Risk Assessment**: Automatically evaluates risk levels (High/Medium/Low) with specific adaptation recommendations
- 💡 **ORM Code Generation**: Auto-generates model code snippets for SQLAlchemy, Django ORM, and other frameworks
- 🛡️ **Breaking Change Detection**: Identifies potentially production-breaking changes automatically

### ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🔍 **Schema Parser** | Parse SQL DDL statements, extract tables, columns, indexes, foreign keys, constraints |
| 🔄 **Change Detector** | Compare two schema versions, identify added/removed/modified tables, columns, indexes |
| 🧠 **Impact Analyzer** | Analyze impact on ORM models, API interfaces, SQL queries |
| ⚠️ **Risk Assessment** | Auto-generate risk level ratings (🔴High/🟡Medium/🟢Low) |
| 📝 **Migration Generator** | Generate safe migration SQL scripts for SQLite/PostgreSQL/MySQL |
| 🎨 **TUI Dashboard** | Beautiful terminal UI with colorful analysis results |
| 📊 **Multi-Format Output** | Support JSON/Markdown/HTML/SQL output formats |
| 🚀 **Zero Dependencies** | Pure Python standard library, no third-party packages required |

### 🚀 Quick Start

#### Requirements

- Python 3.8 or higher
- No external dependencies required

#### Installation

```bash
# Install from source
git clone https://github.com/gitstq/SchemaMap-CLI.git
cd SchemaMap-CLI
pip install .

# Or run directly without installation
python3 -m schemamap.cli.main --help
```

#### Basic Usage

```bash
# Parse schema file
schemamap parse examples/v1_schema.sql

# Compare two schema versions
schemamap diff examples/v1_schema.sql examples/v2_schema.sql

# Full impact analysis (JSON format)
schemamap analyze examples/v1_schema.sql examples/v2_schema.sql -f json

# Generate migration script
schemamap migrate examples/v1_schema.sql examples/v2_schema.sql -f sql -o migrate.sql

# TUI dashboard
schemamap dashboard examples/v1_schema.sql examples/v2_schema.sql
```

### 📖 Detailed Usage Guide

#### Command Reference

**`parse` - Parse Schema Files**

```bash
# Parse and output to terminal
schemamap parse schema.sql

# Parse and save as JSON
schemamap parse schema.sql -o schema.json
```

**`diff` - Schema Difference Comparison**

```bash
# Terminal color output
schemamap diff old.sql new.sql

# Markdown format output
schemamap diff old.sql new.sql -f markdown -o diff.md

# HTML format output
schemamap diff old.sql new.sql -f html -o diff.html
```

**`analyze` - Impact Analysis**

```bash
# JSON format (default)
schemamap analyze old.sql new.sql

# Markdown format
schemamap analyze old.sql new.sql -f markdown -o analysis.md

# HTML format
schemamap analyze old.sql new.sql -f html -o analysis.html
```

**`migrate` - Generate Migration Scripts**

```bash
# SQLite dialect
schemamap migrate old.sql new.sql -f sql --dialect sqlite

# PostgreSQL dialect
schemamap migrate old.sql new.sql -f sql --dialect postgresql -o migrate.sql

# MySQL dialect
schemamap migrate old.sql new.sql -f sql --dialect mysql
```

**`dashboard` - TUI Dashboard**

```bash
# Launch interactive dashboard
schemamap dashboard old.sql new.sql
```

#### Typical Use Cases

**Case 1: Code Review Impact Assessment**

```bash
schemamap analyze schema_v1.sql schema_v2.sql -f markdown -o impact_report.md
```

Attach the generated Markdown report to the PR description so reviewers can quickly understand the impact of changes.

**Case 2: Safe Production Environment Migration**

```bash
schemamap migrate production_schema.sql new_schema.sql -f sql --dialect postgresql -o safe_migration.sql
```

The tool automatically adds transaction wrapping, breaking change warnings, and rollback recommendations.

**Case 3: CI/CD Pipeline Integration**

```bash
schemamap analyze base_schema.sql pr_schema.sql -f json -o analysis.json
# Subsequent steps can parse analysis.json for automated decisions
```

### 💡 Design Philosophy & Roadmap

#### Why Pure Standard Library?

- **Zero Dependencies**: Ensures cross-platform compatibility, easy deployment, perfect for CI/CD environments
- **SQL Parsing Without Database Connection**: No real database connection needed, offline analysis available
- **Multi-Dialect Support**: Covers SQLite, PostgreSQL, MySQL - the three mainstream databases

#### Roadmap

- [ ] Support more database dialects (SQL Server, Oracle, MongoDB)
- [ ] AI-powered adaptation suggestions
- [ ] Reverse ORM model analysis
- [ ] Web UI for visual schema comparison
- [ ] Plugin system for custom impact analysis rules

### 📦 Packaging & Deployment

```bash
# One-click build
chmod +x build.sh
./build.sh

# Manual build
python3 setup.py sdist bdist_wheel

# Install built package
pip3 install dist/schemamap-*.whl
```

### 🤝 Contributing

Issues and PRs are welcome! Please follow these guidelines:

- Run all unit tests before submitting: `python3 -m unittest discover tests -v`
- Code style follows PEP8
- Commit messages use Angular conventions: `feat:`, `fix:`, `docs:`, `refactor:`

### 📄 License

This project is licensed under the [MIT License](LICENSE).
