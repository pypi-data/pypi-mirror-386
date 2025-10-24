#!/usr/bin/env python3
"""
Setup script for the Cybersecurity Log Generator.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="cybersecurity-log-generator",
    version="1.0.0",
    author="Cybersecurity Log Generator Team",
    author_email="team@cybersecurity-log-generator.com",
    description="A world-class cybersecurity log generator with MCP server capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/cybersecurity-log-generator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Security",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: System :: Logging",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "auth": [
            "authlib>=1.0.0",
            "requests-oauthlib>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cybersecurity-log-generator=cybersecurity_log_generator.server:main",
            "clg-server=cybersecurity_log_generator.server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "cybersecurity_log_generator": [
            "config.yaml",
            "examples/*.py",
            "templates/*.yaml",
        ],
    },
    keywords=[
        "cybersecurity",
        "log-generation",
        "synthetic-data",
        "security-testing",
        "mcp",
        "model-context-protocol",
        "fastmcp",
        "ids",
        "endpoint",
        "firewall",
        "security-events",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-org/cybersecurity-log-generator/issues",
        "Source": "https://github.com/your-org/cybersecurity-log-generator",
        "Documentation": "https://github.com/your-org/cybersecurity-log-generator/blob/main/README.md",
    },
)
