from buidl.tx import Tx

# Helper function to fund a beacon address. Only designed for regtest.
async def fund_regtest_beacon_address(bitcoin_rpc, beacon_manager):
    result = await bitcoin_rpc.acall("send", {"outputs": { beacon_manager.address: 0.2}})

    funding_txid = result["txid"]
    funding_tx_hex = await bitcoin_rpc.acall("getrawtransaction", {"txid": funding_txid})
    funding_tx = Tx.parse_hex(funding_tx_hex)
    beacon_manager.add_funding_tx(funding_tx)