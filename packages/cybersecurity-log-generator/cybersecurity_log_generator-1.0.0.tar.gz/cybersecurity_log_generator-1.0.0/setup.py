#!/usr/bin/env python3
"""
Setup script for cybersecurity-log-generator package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Cybersecurity Log Generator - Generate synthetic cybersecurity logs for testing and analysis"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return [
        "fastmcp>=0.1.0",
        "faker>=20.0.0",
        "requests>=2.28.0",
        "pydantic>=2.0.0",
        "uvicorn>=0.20.0",
        "python-dotenv>=1.0.0"
    ]

setup(
    name="cybersecurity-log-generator",
    version="1.0.0",
    author="Cybersecurity Log Generator Team",
    author_email="support@cybersecurity-log-generator.com",
    description="Generate synthetic cybersecurity logs for testing and analysis across all 24 cyberdefense pillars",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/tredkar/hd-syntheticdata",
    project_urls={
        "Bug Reports": "https://github.com/tredkar/hd-syntheticdata/issues",
        "Source": "https://github.com/tredkar/hd-syntheticdata",
        "Documentation": "https://github.com/tredkar/hd-syntheticdata/blob/main/README.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "mcp": [
            "fastmcp>=0.1.0",
        ],
        "api": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cybersecurity-log-gen=cybersecurity_log_generator.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "cybersecurity_log_generator": [
            "*.yaml",
            "*.yml", 
            "*.json",
        ],
    },
    keywords=[
        "cybersecurity",
        "log generation",
        "security testing",
        "synthetic data",
        "threat simulation",
        "SIEM",
        "SOC",
        "security analysis",
        "penetration testing",
        "red team",
        "blue team",
    ],
)
