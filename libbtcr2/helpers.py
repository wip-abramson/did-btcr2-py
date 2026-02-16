from buidl.tx import Tx

from .constants import DEFAULT_FUNDING_AMOUNT


# Helper function to fund a beacon address. Only designed for regtest.
async def fund_regtest_beacon_address(bitcoin_rpc, beacon_manager, amount=DEFAULT_FUNDING_AMOUNT):
    result = await bitcoin_rpc.acall("send", {"outputs": {beacon_manager.address: amount}})

    funding_txid = result["txid"]
    funding_tx_hex = await bitcoin_rpc.acall("getrawtransaction", {"txid": funding_txid})
    funding_tx = Tx.parse_hex(funding_tx_hex)
    beacon_manager.add_funding_tx(funding_tx)
