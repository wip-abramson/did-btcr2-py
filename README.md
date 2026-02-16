# Experimental did:btcr2 Python Library

> Warning: This is purely experimental and should not be used for production purposes.

A Python library for creating, managing, and resolving `did:btcr2` decentralised identifiers anchored to the Bitcoin blockchain.

## Features

- **DID Creation** - Create deterministic (key-based) or external (hash-based) DIDs
- **DID Resolution** - Resolve DIDs by traversing Bitcoin blockchain history
- **DID Updates** - Update DID documents via beacon signals committed to Bitcoin transactions
- **Multiple Networks** - Supports Bitcoin mainnet, signet, testnet3, testnet4, regtest, and mutinynet
- **Cryptographic Proofs** - BIP340 Schnorr signature proofs with JCS canonicalization

## Project Structure

```
libbtcr2/
├── did.py              # DID identifier encoding/decoding (bech32)
├── did_manager.py      # Core DID lifecycle management
├── resolver.py         # DID resolution from blockchain
├── beacon_manager.py   # Bitcoin beacon signal creation
├── address_manager.py  # Bitcoin address and UTXO management
├── esplora_client.py   # Esplora blockchain API client
├── diddoc/
│   ├── doc.py          # DID document model
│   ├── builder.py      # DID document construction
│   └── updater.py      # DID document updates via JSON-Patch
├── service.py          # Beacon service definitions
├── multikey.py         # Cryptographic key handling
├── network_config.py   # Network definitions and Esplora endpoints
├── constants.py        # Global constants and configurations
└── error.py            # Custom exceptions
```

## Setup

Requires Python >= 3.10.

```bash
python -m venv venv
source venv/bin/activate
```

### Install from source

```bash
pip install -e .
```

### Install from repository

This installs the package from the main branch of the repository. As this is an experimental, proof-of-concept implementation there is no pip package available for the time being.

```bash
pip install libbtcr2@git+https://github.com/DCD/did-btcr2-py
```

## Run Tests

```bash
pytest
```

## Example Scripts

Example scripts are provided in the `scripts/` directory:

- `scripts/regtest_create_deterministic.py` - Create a deterministic DID from a secp256k1 key on regtest
- `scripts/regtest_create_external.py` - Create an external DID from an intermediate document on regtest
- `scripts/mutinynet_create.py` - Create a DID on mutinynet
- `scripts/resolve.py` - Resolve a DID and output the resolution result
