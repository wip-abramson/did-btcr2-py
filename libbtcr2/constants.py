# DID method identifiers
DID_SCHEME = "did"
DID_METHOD = "btcr2"
DID_METHOD_PREFIX = "did:btcr2:"
PLACEHOLDER_DID = "did:btcr2:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Context URLs
W3C_DID_CONTEXT = "https://www.w3.org/TR/did-1.1"
BTCR2_CONTEXT = "https://did-btcr2/TBD/context"
DID_CONTEXT = [W3C_DID_CONTEXT, BTCR2_CONTEXT]
UPDATE_PAYLOAD_CONTEXT = [
    "https://w3id.org/security/v2",
    "https://w3id.org/zcap/v1",
    "https://w3id.org/json-ld-patch/v1",
]
ZCAP_CONTEXT = "https://w3id.org/zcap/v1"

# Networks
BITCOIN = "bitcoin"
SIGNET = "signet"
TESTNET3 = "testnet3"
TESTNET4 = "testnet4"
REGTEST = "regtest"
MUTINYNET = "mutinynet"

NETWORKS = [BITCOIN, SIGNET, REGTEST, TESTNET3, TESTNET4, MUTINYNET, None, None, None, None, None, None, 1, 2, 3, 4]

NETWORK_MAP = {
    0x0: BITCOIN,
    0x1: SIGNET,
    0x2: REGTEST,
    0x3: TESTNET3,
    0x4: TESTNET4,
    0x5: MUTINYNET,
}

NETWORK_DISPLAY_MAP = {
    "bitcoin": "mainnet",
    "testnet3": "testnet",
    "testnet4": "testnet",
    "mutinynet": "signet",
}

VERSIONS = [1]

# Identifier types & HRP
EXTERNAL = "external"
KEY = "key"

ID_TYPE_TO_HRP = {
    EXTERNAL: "x",
    KEY: "k",
}

HRP_TO_ID_TYPE = {v: k for k, v in ID_TYPE_TO_HRP.items()}

# Address types
P2PKH = "p2pkh"
P2WPKH = "p2wpkh"
P2TR = "p2tr"

# Beacon types
SINGLETON_BEACON_TYPE = "SingletonBeacon"
SMT_AGGREGATE_BEACON_TYPE = "SMTAggregateBeacon"
CID_AGGREGATE_BEACON_TYPE = "CIDAggregateBeacon"
BEACON_TYPE_NAMES = [SINGLETON_BEACON_TYPE, SMT_AGGREGATE_BEACON_TYPE, CID_AGGREGATE_BEACON_TYPE]

# Bitcoin script
OP_RETURN = 0x6a

# Coinbase TXIDs
GENESIS_COINBASE = "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"
COINBASE_TXIDS = [GENESIS_COINBASE, "0000000000000000000000000000000000000000000000000000000000000000"]

# Multikey codecs
SECP256K1_PUBLIC_KEY_CODEC = 0xe7
SECP256K1_XONLY_PUBLIC_KEY_CODEC = 0x2561
SECP256K1_XONLY_SECRET_KEY_CODEC = 0x130e
MULTIKEY_TYPE = "Multikey"

# Data integrity / proof
PROOF_TYPE = "DataIntegrityProof"
CRYPTOSUITE = "bip340-jcs-2025"
PROOF_PURPOSE = "capabilityInvocation"
CAPABILITY_ACTION = "Write"

# Bitcoin constants
MAX_BTC_SUPPLY_SATOSHIS = 21000000 * 100000000
BECH32_CHECKSUM_LEN = 6

# Configurable defaults
DEFAULT_TX_FEE = 4000
DEFAULT_ESPLORA_URL = "http://localhost:3000"
DEFAULT_ESPLORA_MUTINYNET_URL = "https://mutinynet.com/api"
DEFAULT_FUNDING_AMOUNT = 0.2
