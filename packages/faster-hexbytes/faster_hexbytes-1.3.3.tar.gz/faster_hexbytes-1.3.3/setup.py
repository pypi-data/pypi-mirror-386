#!/usr/bin/env python
import sys
from setuptools import (
    find_packages,
    setup,
)
from mypyc.build import mypycify


version = "1.3.3"
hexbytes_version = "1.3.1"

extras_require = {
    "dev": [
        "build>=0.9.0",
        "bump_my_version>=0.19.0",
        "ipython",
        "mypy==1.10.0",
        "pre-commit>=3.4.0",
        "tox>=4.0.0",
        "twine",
        "wheel",
    ],
    "docs": [
        "sphinx>=6.0.0",
        "sphinx-autobuild>=2021.3.14",
        "sphinx_rtd_theme>=1.0.0",
        "towncrier>=25,<26",
    ],
    "test": [
        "eth_utils>=2.0.0",
        "hypothesis>=3.44.24",
        "pytest>=7.0.0",
        "pytest-xdist>=2.4.0",
    ],
    "benchmark": [
        "pytest-benchmark",
        "pytest-codspeed>=4.2,<4.3",
        "eth-typing",
    ],
    "codspeed": [
        "pytest-codspeed>=4.2,<4.3",
        "eth-typing",
    ],
}

extras_require["dev"] = (
    extras_require["dev"] + extras_require["docs"] + extras_require["test"]
)


with open("./README.md") as readme:
    long_description = readme.read()


# we can't compile on python3.8 but we can still let the user install
skip_mypyc = sys.version_info < (3, 9) or any(
    cmd in sys.argv
    for cmd in ("sdist", "egg_info", "--name", "--version", "--help", "--help-commands")
)

if skip_mypyc:
    ext_modules = []
else:
    ext_modules = mypycify(
      ["faster_hexbytes/", "--strict", "--pretty"],
      group_name="faster_hexbytes",
      strict_dunder_typing=True,
    )


setup(
    name="faster_hexbytes",
    # *IMPORTANT*: Don't manually change the version here. See Contributing docs for the release process.
    version=version,
    description="""A faster fork of hexbytes: Python `bytes` subclass that decodes hex, with a readable console output. Implemented in C.""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="The Ethereum Foundation",
    author_email="snakecharmers@ethereum.org",
    url="https://github.com/BobTheBuidler/faster-hexbytes",
    project_urls={
        "Documentation": "https://hexbytes.readthedocs.io/en/stable/",
        "Release Notes": "https://github.com/BobTheBuidler/faster-hexbytes/releases",
        "Issues": "https://github.com/BobTheBuidler/faster-hexbytes/issues",
        "Source - Precompiled (.py)": "https://github.com/BobTheBuidler/faster-hexbytes/tree/master/faster_eth_utils",
        "Source - Compiled (.c)": "https://github.com/BobTheBuidler/faster-hexbytes/tree/master/build",
        "Benchmarks": "https://github.com/BobTheBuidler/faster-hexbytes/tree/master/benchmarks",
        "Benchmarks - Results": "https://github.com/BobTheBuidler/faster-hexbytes/tree/master/benchmarks/results",
        "Original": "https://github.com/ethereum/hexbytes",
    },
    include_package_data=True,
    install_requires=[
        f"hexbytes=={hexbytes_version}",
        "mypy_extensions>=0.4.2,<2",
        "typing-extensions>=4.0.0,<5",
    ],
    python_requires=">=3.9, <4",
    extras_require=extras_require,
    py_modules=["faster_hexbytes"],
    license="MIT",
    zip_safe=False,
    keywords="ethereum",
    packages=find_packages(
        exclude=[
            "scripts",
            "scripts.*",
            "tests",
            "tests.*",
            "benchmarks",
            "benchmarks.*",
        ]
    ),
    ext_modules=ext_modules,
    package_data={"faster_hexbytes": ["py.typed"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
)
