#!/usr/bin/env python3
"""
SchemaMap-CLI setup script
轻量级数据库Schema变更影响分析与智能迁移引擎
"""

from setuptools import setup, find_packages

setup(
    name="SchemaMap-CLI",
    version="1.0.0",
    description="轻量级数据库Schema变更影响分析与智能迁移引擎",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="gitstq",
    author_email="gitstq@example.com",
    url="https://github.com/gitstq/SchemaMap-CLI",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "schemamap=schemamap.cli.main:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Tools",
    ],
    keywords="database schema migration impact-analysis cli",
    license="MIT",
)
