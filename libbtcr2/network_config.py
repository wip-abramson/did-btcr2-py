



REGTEST = {
  "btc_network": "regtest",
  "esplora_api": "http://localhost:3000"
}

SIGNET = {
  "btc_network": "signet",
  "esplora_api": "https://mempool.space/signet/api"
}

MUTINY_NET = {
  "btc_network": "signet",
  "esplora_api": "https://mutinynet.com/api"
}

BITCOIN = {
  "btc_network": "mainnet",
  "esplora_api": "https://mempool.space/api"
}

DEFAULT_NETWORK_DEFINITIONS = {
    "regtest": REGTEST,
    "signet": SIGNET,
    "mutinynet": MUTINY_NET,
    "mainnet": BITCOIN
}