#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="matsushibadb",
    version="1.0.8",
    author="Matsushiba Systems",
    author_email="support@matsushiba.co",
    description="MatsushibaDB - Next-Generation SQL Database with Complete Enterprise Features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://db.matsushiba.co",
    project_urls={
        "Bug Reports": "https://github.com/matsushibaco/matsushibadb/issues",
        "Documentation": "https://db.matsushiba.co/docs",
        "Homepage": "https://db.matsushiba.co",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "async": [
            "aiohttp>=3.8.0",
            "websockets>=11.0.0",
        ],
        "server": [
            "flask>=2.3.0",
            "flask-cors>=4.0.0",
            "flask-limiter>=3.0.0",
            "cryptography>=41.0.0",
            "PyJWT>=2.8.0",
            "bcrypt>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "matsushiba-db=matsushiba_db.server:main",
            "matsushiba-server=matsushiba_db.server:main",
            "matsushiba-init=matsushiba_db.init:main",
            "matsushiba-welcome=matsushiba_db.welcome:main",
        ],
    },
    include_package_data=True,
    package_data={
        "matsushiba_db": ["*.py", "*.json", "*.txt"],
    },
    zip_safe=False,
    keywords="database sqlite server api web high-performance self-contained enterprise security rbac audit encryption",
    license="Commercial",
)
