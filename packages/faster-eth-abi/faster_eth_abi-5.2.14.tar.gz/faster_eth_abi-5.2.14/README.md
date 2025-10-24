### I forked eth-abi and compiled it to C. It does the same stuff, now faster

[![PyPI](https://img.shields.io/pypi/v/faster-eth-abi.svg?logo=Python&logoColor=white)](https://pypi.org/project/faster-eth-abi/)
[![Monthly Downloads](https://img.shields.io/pypi/dm/faster-eth-abi)](https://pypistats.org/packages/faster-eth-abi)
[![Codspeed.io Status](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/BobTheBuidler/faster-eth-abi)

##### This fork will be kept up-to-date with [eth-abi](https://github.com/ethereum/eth-abi). I will pull updates as they are released and push new [faster-eth-abi](https://github.com/BobTheBuidler/faster-eth-abi) releases to [PyPI](https://pypi.org/project/faster-eth-abi/).

##### Starting in [v5.2.12](https://github.com/BobTheBuidler/faster-eth-abi/releases/tag/v5.2.12), all `faster-eth-abi` Exception classes inherit from the matching Exception class in `eth-abi`, so porting to `faster-eth-abi` does not require any change to your existing exception handlers. All existing exception handling in your codebase will continue to work as it did when originaly implemented.

##### We benchmark `faster-eth-abi` against the original `eth-abi` for your convenience. [See results](https://github.com/BobTheBuidler/faster-eth-abi/tree/master/benchmarks/results).

##### You can find the compiled C code and header files in the [build](https://github.com/BobTheBuidler/faster-eth-abi/tree/master/build) directory.

###### You may also be interested in: [faster-web3.py](https://github.com/BobTheBuidler/faster-web3.py/), [faster-hexbytes](https://github.com/BobTheBuidler/faster-hexbytes/), and [faster-eth-utils](https://github.com/BobTheBuidler/faster-eth-utils/)

##### The original eth-abi readme is below:

# Ethereum Contract Interface (ABI) Utility

[![Join the conversation on Discord](https://img.shields.io/discord/809793915578089484?color=blue&label=chat&logo=discord&logoColor=white)](https://discord.gg/GHryRvPB84)
[![Build Status](https://circleci.com/gh/ethereum/faster-eth-abi.svg?style=shield)](https://circleci.com/gh/ethereum/faster-eth-abi)
[![PyPI version](https://badge.fury.io/py/faster-eth-abi.svg)](https://badge.fury.io/py/faster-eth-abi)
[![Python versions](https://img.shields.io/pypi/pyversions/faster-eth-abi.svg)](https://pypi.python.org/pypi/faster-eth-abi)
[![Docs build](https://readthedocs.org/projects/faster-eth-abi/badge/?version=latest)](https://faster-eth-abi.readthedocs.io/en/latest/?badge=latest)

Python utilities for working with Ethereum ABI definitions, especially encoding and decoding

Read the [documentation](https://faster-eth-abi.readthedocs.io/).

View the [change log](https://faster-eth-abi.readthedocs.io/en/latest/release_notes.html).

## Installation

```sh
python -m pip install faster-eth-abi
```
