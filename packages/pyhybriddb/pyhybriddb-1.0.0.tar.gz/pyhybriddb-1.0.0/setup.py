from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version
version = "1.0.0"

setup(
    name="pyhybriddb",
    version=version,
    author="Infant Nirmal",
    author_email="contact@adrient.com",
    description="A production-ready hybrid database system combining SQL and NoSQL with enterprise features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Adrient-tech/PyHybridDB",
    project_urls={
        "Bug Tracker": "https://github.com/Adrient-tech/PyHybridDB/issues",
        "Documentation": "https://github.com/Adrient-tech/PyHybridDB#readme",
        "Source Code": "https://github.com/Adrient-tech/PyHybridDB",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
    package_data={
        "pyhybriddb": ["py.typed"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
    ],
    keywords="database, hybrid, sql, nosql, mongodb, postgresql, fastapi, rest-api, backup, audit, encryption",
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic[email]>=2.5.0",
        "python-multipart>=0.0.6",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "sqlparse>=0.4.4",
        "aiofiles>=23.2.1",
        "python-dotenv>=1.0.0",
        "bcrypt>=4.1.1",
        "cryptography>=41.0.7",
        "email-validator>=2.1.0",
    ],
    extras_require={
        "postgresql": ["psycopg2-binary>=2.9.9"],
        "mongodb": ["pymongo>=4.6.0"],
        "all": [
            "psycopg2-binary>=2.9.9",
            "pymongo>=4.6.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pyhybriddb=pyhybriddb.cli:main",
        ],
    },
    zip_safe=False,
)
