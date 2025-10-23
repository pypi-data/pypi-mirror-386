from pathlib import Path
from setuptools import setup, find_packages

here = Path(__file__).parent
long_description = ""
readme = here / "README.md"
usage_md = here / "usage.md"
if readme.exists():
    long_description = readme.read_text(encoding="utf-8")
    # Append usage.md if present to give extra usage information on PyPI/long description
    if usage_md.exists():
        long_description += "\n\n" + usage_md.read_text(encoding="utf-8")

setup(
    name="agentic_cache",
    version="0.1.0",
    packages=find_packages(exclude=("tests", "build", "dist")),
    install_requires=[],
    author="Abinayasankar M",
    description="Core component for Agent Memory and Task Management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "agentic-cache=AgenticCache.cli:main",
        ]
    },
    # ensure usage.md is included in sdist/wheel
    include_package_data=True,
    package_data={"": ["usage.md"]},
)
