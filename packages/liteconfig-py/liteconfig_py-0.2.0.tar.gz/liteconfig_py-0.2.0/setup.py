"""
Setup file for liteconfig_py.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="liteconfig_py",
    version="0.2.0",
    author="TickTockBent",
    author_email="benttick@gmail.com",
    description="A minimal, flexible Python configuration loader with environment variable support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TickTockBent/liteconfig_py",
    packages=find_packages(),
    package_data={"liteconfig_py": ["py.typed"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "yaml": ["PyYAML"],
        "toml": ["toml"],
        "validation": ["pydantic>=2.0"],
        "all": ["PyYAML", "toml", "pydantic>=2.0"],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "PyYAML",
            "toml",
            "pydantic>=2.0",
        ],
    },
)