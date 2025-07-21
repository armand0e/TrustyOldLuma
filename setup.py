"""
Setup configuration for Luna Gaming Tool.

This file provides configuration for creating executable packages
and installing the Luna Gaming Tool as a Python package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements from requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="luna-gaming-tool",
    version="1.0.0",
    description="Luna Gaming Tool - Unified gaming setup and configuration tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Luna Gaming Tool Team",
    author_email="support@luna-gaming.com",
    url="https://github.com/luna-gaming/luna-gaming-tool",
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Dependencies
    install_requires=requirements,
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Entry points for command-line execution
    entry_points={
        "console_scripts": [
            "luna=luna.__main__:main",
            "luna-setup=luna.__main__:main",
            "luna-gaming-tool=luna.__main__:main",  # Full name alias
            "luna-cli=luna.cli:run",  # CLI backend
        ],
    },
    
    # Package data
    package_data={
        "": [
            "assets/luna/*.zip",
            "assets/luna/*.json",
            "assets/luna/*.jsonc",
            "assets/luna/*.config",
            "config/*.jsonc",
            "config/*.json",
            "docs/*.md",
            "scripts/*.bat",
            "scripts/*.sh",
            "*.md",
            "*.txt",
            "*.ini"
        ],
    },
    include_package_data=True,
    
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
        "Topic :: System :: Installation/Setup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Environment :: Console",
    ],
    
    # Keywords for discovery
    keywords="luna gaming tool unified setup automation installer steam dlc injection",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/luna-gaming/luna-gaming-tool/issues",
        "Source": "https://github.com/luna-gaming/luna-gaming-tool",
        "Documentation": "https://github.com/luna-gaming/luna-gaming-tool/wiki",
        "Homepage": "https://luna-gaming.com",
    },
    
    # Additional options for executable creation
    options={
        "build_exe": {
            "packages": [
                "rich",
                "pathlib",
                "asyncio",
                "zipfile",
                "argparse",
                "logging",
                "ctypes",
                "subprocess",
                "tempfile",
                "shutil"
            ],
            "include_files": [
                ("assets/", "assets/"),
                ("README.md", "README.md"),
                ("requirements.txt", "requirements.txt")
            ],
            "excludes": [
                "tkinter",
                "unittest",
                "test",
                "tests",
                "pytest"
            ],
            "optimize": 2,
            "build_exe": "dist/luna-gaming-tool"
        }
    },
    
    # Zip safe configuration
    zip_safe=False,
)