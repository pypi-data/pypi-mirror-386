"""
Setup script for LFC Demo Library

Note: This setup.py is maintained for backward compatibility.
The preferred configuration is in pyproject.toml.
"""

from setuptools import setup
from pathlib import Path

# Read the long description from README
long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="lfcdemolib",
    version="0.0.2",
    description="Lakeflow Connect Demo Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Databricks Labs",
    author_email="labs@databricks.com",
    url="https://github.com/databricks-labs/lfcdemolib",
    license="Databricks Labs License",
    packages=["lfcdemolib"],
    package_dir={"lfcdemolib": "db/lfcdemolib"},
    python_requires=">=3.8",
    install_requires=[
        "sqlalchemy>=1.4.0,<3.0.0",
        "pandas>=1.3.0",
        "databricks-sdk>=0.1.0",
        "apscheduler>=3.9.0,<4.0.0",
        "pydantic>=1.8.0,<2.0.0",  # v1 compatibility required
        "requests>=2.25.0",
        # Database drivers (all included as core dependencies)
        "pymysql>=1.0.0",
        "psycopg2-binary>=2.9.0",
        "pymssql>=2.2.0",
        "oracledb>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=3.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.900",
            "isort>=5.10",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=[
        "databricks",
        "lakeflow",
        "federation",
        "cdc",
        "change-data-capture",
        "data-engineering",
        "etl",
        "database",
        "replication",
    ],
)
