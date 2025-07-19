"""
Setup configuration for Gaming Setup Tool.

This file provides configuration for creating executable packages
and installing the Gaming Setup Tool as a Python package.
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
    name="gaming-setup-tool",
    version="1.0.0",
    description="Modern Python replacement for gaming tools setup batch script",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Gaming Setup Tool Team",
    author_email="support@example.com",
    url="https://github.com/example/gaming-setup-tool",
    
    # Package configuration
    packages=find_packages(),
    py_modules=[
        "gaming_setup_tool",
        "admin_manager",
        "applist_manager", 
        "cleanup_manager",
        "config",
        "configuration_handler",
        "display_managers",
        "error_manager",
        "exceptions",
        "file_operations_manager",
        "models",
        "security_config_manager",
        "shortcut_manager"
    ],
    
    # Dependencies
    install_requires=requirements,
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Entry points for command-line execution
    entry_points={
        "console_scripts": [
            "gaming-setup-tool=gaming_setup_tool:main",
            "gst=gaming_setup_tool:main",  # Short alias
        ],
    },
    
    # Package data
    package_data={
        "": [
            "assets/*.zip",
            "assets/*.json",
            "assets/*.config",
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
    keywords="gaming setup tools greenluma koalageddon automation installer",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/example/gaming-setup-tool/issues",
        "Source": "https://github.com/example/gaming-setup-tool",
        "Documentation": "https://github.com/example/gaming-setup-tool/wiki",
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
            "build_exe": "dist/gaming-setup-tool"
        }
    },
    
    # Zip safe configuration
    zip_safe=False,
)