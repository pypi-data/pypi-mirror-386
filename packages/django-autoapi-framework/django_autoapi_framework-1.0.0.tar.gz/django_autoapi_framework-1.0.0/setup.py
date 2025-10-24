"""
Setup configuration for Django AutoAPI

This script configures the Django AutoAPI package for distribution via PyPI.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.absolute()

# Read README.md
readme_path = project_root / "django_autoapi" / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "Zero-boilerplate REST APIs for Django with row-level security"

# Read version from __init__.py
version = "1.0.0"
init_path = project_root / "django_autoapi" / "__init__.py"
if init_path.exists():
    with open(init_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                # Extract version from __version__ = '1.0.0'
                version = line.split("=")[1].strip().strip("'\"")
                break

setup(
    # Package metadata
    name="django-autoapi-framework",  
    version="1.0.0",
    author="Backend Development Team",
    author_email="dev@example.com",
    maintainer="Backend Development Team",
    maintainer_email="dev@example.com",

    # Description
    description="Zero-boilerplate REST APIs for Django with row-level security",
    long_description=long_description,
    long_description_content_type="text/markdown",

    # URLs
    url="https://github.com/nakula-academy/django-autoapi",
    project_urls={
        "Bug Tracker": "https://github.com/nakula-academy/django-autoapi/issues",
        "Documentation": "https://github.com/nakula-academy/django-autoapi#readme",
        "Source Code": "https://github.com/nakula-academy/django-autoapi",
        "Changelog": "https://github.com/nakula-academy/django-autoapi/blob/main/CHANGELOG.md",
    },

    # Licensing
    license="MIT",

    # Package discovery
    packages=find_packages(
        where=".",
        include=["django_autoapi*"],
        exclude=["tests*", "*.tests", "*.tests.*"],
    ),

    # Package data
    include_package_data=True,
    package_data={
        "django_autoapi": [
            "py.typed",  # For type hints
        ],
    },

    # Classifiers for PyPI
    classifiers=[
        # Development Status
        "Development Status :: 5 - Production/Stable",

        # Intended Audience
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",

        # Topics
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Database",

        # License
        "License :: OSI Approved :: MIT License",

        # Programming Language
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",

        # Framework
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",

        # Environment
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Natural Language :: Indonesian",
    ],

    # Keywords for search
    keywords=[
        "django",
        "rest-api",
        "crud",
        "autoapi",
        "record-rules",
        "row-level-security",
        "permissions",
        "django-rest-framework",
        "drf",
        "api-framework",
        "rapid-development",
    ],

    # Python version requirement
    python_requires=">=3.8",

    # Dependencies
    install_requires=[
        "Django>=4.2",
        "djangorestframework>=3.14",
        "django-filter>=23.0",
    ],

    # Optional dependencies
    extras_require={
        # Development dependencies
        "dev": [
            "pytest>=7.0",
            "pytest-django>=4.5",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "isort>=5.0",
            "mypy>=1.0",
            "django-stubs>=4.2",
        ],

        # Documentation dependencies
        "docs": [
            "mkdocs>=1.5",
            "mkdocs-material>=9.0",
            "mkdocstrings>=0.24",
            "mkdocstrings-python>=0.10",
        ],

        # Testing dependencies
        "test": [
            "pytest>=7.0",
            "pytest-django>=4.5",
            "pytest-cov>=4.0",
            "factory-boy>=3.3",
        ],

        # All optional dependencies
        "all": [
            "pytest>=7.0",
            "pytest-django>=4.5",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "isort>=5.0",
            "mypy>=1.0",
            "django-stubs>=4.2",
            "mkdocs>=1.5",
            "mkdocs-material>=9.0",
            "mkdocstrings>=0.24",
            "mkdocstrings-python>=0.10",
        ],
    },

    # Package settings
    zip_safe=False,

    # Entry points (optional, for CLI commands if needed)
    entry_points={
        "console_scripts": [
            # Add CLI commands here if needed in future
        ],
    },
)
