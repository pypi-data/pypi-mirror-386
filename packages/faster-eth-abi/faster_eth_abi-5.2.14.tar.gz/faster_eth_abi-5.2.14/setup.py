#!/usr/bin/env python
import sys

from mypyc.build import (
    mypycify,
)
from setuptools import (
    find_packages,
    setup,
)

HYPOTHESIS_REQUIREMENT = "hypothesis>=6.22.0,<6.108.7"

extras_require = {
    "dev": [
        "build>=0.9.0",
        "bump_my_version>=0.19.0",
        "ipython",
        f"mypy=={'1.14.1' if sys.version_info < (3, 9) else '1.18.2'}",
        "pre-commit>=3.4.0",
        "tox>=4.0.0",
        "twine",
        "wheel",
        "pytest-benchmark",
    ],
    "docs": [
        "sphinx>=6.0.0",
        "sphinx-autobuild>=2021.3.14",
        "sphinx_rtd_theme>=1.0.0",
        "towncrier>=25,<26",
    ],
    "test": [
        "pytest>=7.0.0",
        "pytest-timeout>=2.0.0",
        "pytest-xdist>=2.4.0",
        "pytest-pythonpath>=0.7.1",
        "eth-hash[pycryptodome]",
        HYPOTHESIS_REQUIREMENT,
    ],
    "tools": [
        HYPOTHESIS_REQUIREMENT,
    ],
    "codspeed": [
        "pytest>=7.0.0",
        "pytest-codspeed",
        "pytest-test-groups",
    ],
}

extras_require["dev"] = (
    extras_require["dev"] + extras_require["docs"] + extras_require["test"]
)


with open("./README.md") as readme:
    long_description = readme.read()


skip_mypyc = any(
    cmd in sys.argv
    for cmd in ("sdist", "egg_info", "--name", "--version", "--help", "--help-commands")
)

if skip_mypyc:
    ext_modules = []
else:
    mypycify_kwargs = {"strict_dunder_typing": True}
    if sys.version_info >= (3, 9):
        mypycify_kwargs["group_name"] = "faster_eth_abi"

    ext_modules = mypycify(
        [
            "faster_eth_abi/_codec.py",
            "faster_eth_abi/_decoding.py",
            "faster_eth_abi/_encoding.py",
            "faster_eth_abi/_grammar.py",
            "faster_eth_abi/abi.py",
            "faster_eth_abi/constants.py",
            # "faster_eth_abi/exceptions.py",  segfaults on mypyc 1.18.2
            "faster_eth_abi/from_type_str.py",
            # "faster_eth_abi/io.py",
            "faster_eth_abi/packed.py",
            "faster_eth_abi/tools",
            "faster_eth_abi/utils",
            "--pretty",
            "--install-types",
            # all of these are safe to disable long term
            "--disable-error-code=override",
            "--disable-error-code=unused-ignore",
            "--disable-error-code=no-any-return",
        ],
        **mypycify_kwargs,
    )


setup(
    name="faster_eth_abi",
    # *IMPORTANT*: Don't manually change the version here. See Contributing docs for the release process.
    version="5.2.14",
    description="""A faster fork of eth_abi: Python utilities for working with Ethereum ABI definitions, especially encoding and decoding. Implemented in C.""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="The Ethereum Foundation",
    author_email="snakecharmers@ethereum.org",
    url="https://github.com/BobTheBuidler/faster-eth-abi",
    project_urls={
        "Documentation": "https://eth-abi.readthedocs.io/en/stable/",
        "Release Notes": "https://github.com/BobTheBuidler/faster-eth-abi/releases",
        "Issues": "https://github.com/BobTheBuidler/faster-eth-abi/issues",
        "Source - Precompiled (.py)": "https://github.com/BobTheBuidler/faster-eth-utils/tree/master/faster_eth_utils",
        "Source - Compiled (.c)": "https://github.com/BobTheBuidler/faster-eth-utils/tree/master/build",
        "Benchmarks": "https://github.com/BobTheBuidler/faster-eth-utils/tree/master/benchmarks",
        "Benchmarks - Results": "https://github.com/BobTheBuidler/faster-eth-utils/tree/master/benchmarks/results",
        "Original": "https://github.com/ethereum/eth-abi",
    },
    include_package_data=True,
    install_requires=[
        "cchecksum>=0.2.6,<0.4",
        "faster-eth-utils>=2.0.0",
        "eth-abi>=5.0.1,<6",
        "eth-typing>=3.0.0",
        "mypy_extensions",
        "parsimonious>=0.10.0,<0.11.0",
    ],
    python_requires=">=3.8, <4",
    extras_require=extras_require,
    py_modules=["faster_eth_abi"],
    license="MIT",
    zip_safe=False,
    keywords="ethereum",
    packages=find_packages(exclude=["scripts", "scripts.*", "tests", "tests.*"]),
    ext_modules=ext_modules,
    package_data={"faster_eth_abi": ["py.typed"]},
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
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)
