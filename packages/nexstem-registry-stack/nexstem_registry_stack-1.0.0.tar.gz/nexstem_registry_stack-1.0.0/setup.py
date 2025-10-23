#!/usr/bin/env python3
"""
Setup script for SW Registry Stack Python SDK
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

# Read dev requirements
def read_dev_requirements():
    dev_requirements_path = os.path.join(os.path.dirname(__file__), "requirements-dev.txt")
    if os.path.exists(dev_requirements_path):
        with open(dev_requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

if __name__ == "__main__":
    setup(
        name="nexstem-registry-stack",
        version="1.0.0",
        description="Python SDK for SW Registry Stack - Operator Registry, Pipeline Registry, Executor, and Recorder",
        long_description=read_readme(),
        long_description_content_type="text/markdown",
        author="Vignesh Sambari",
        author_email="vignesh.sambari@nexstem.ai",
        url="https://github.com/sw-registry-stack/sdk",
        project_urls={
            "Homepage": "https://github.com/sw-registry-stack/sdk",
            "Documentation": "https://sw-registry-stack.readthedocs.io/",
            "Repository": "https://github.com/sw-registry-stack/sdk.git",
            "Bug Tracker": "https://github.com/sw-registry-stack/sdk/issues",
        },
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Systems Administration",
        ],
        python_requires=">=3.8",
        install_requires=read_requirements(),
        extras_require={
            "dev": [
                "pytest>=7.0.0",
                "pytest-asyncio>=0.21.0",
                "pytest-cov>=4.0.0",
                "black>=23.0.0",
                "isort>=5.12.0",
                "mypy>=1.0.0",
                "flake8>=6.0.0",
                "pre-commit>=3.0.0",
            ],
            "test": [
                "pytest>=7.0.0",
                "pytest-asyncio>=0.21.0",
                "pytest-cov>=4.0.0",
                "pytest-mock>=3.10.0",
            ],
            "docs": [
                "sphinx>=6.0.0",
                "sphinx-rtd-theme>=1.2.0",
                "myst-parser>=1.0.0",
            ],
        },
        entry_points={
            "console_scripts": [
                "sw-registry-stack=sw_registry_stack.cli:main",
            ],
        },
        include_package_data=True,
        zip_safe=False,
    )