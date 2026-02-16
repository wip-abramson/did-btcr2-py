import asyncio

from bitcoinrpc import BitcoinRPC
from buidl.hd import HDPrivateKey
from buidl.mnemonic import secure_mnemonic
from buidl.tx import Tx

from libbtcr2.address_manager import AddressManager
from libbtcr2.esplora_client import EsploraClient


async def test_beacon_manager():

    didkey_purpose = "11"
    ## Run this if you want a new hardware key
    mnemonic = secure_mnemonic()

    network = "regtest"

    mnemonic = (
        "camp they field lift airport satoshi path slush raccoon limit now laugh"
        " chimney youth decide nice matrix fence agent grief ankle bind stable rude"
    )
    root_hdpriv = HDPrivateKey.from_mnemonic(mnemonic, network="regtest")
    print("Mnemonic : ", mnemonic)

    beacon_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=2)
    beacon_pk = beacon_sk.point

    script_pubkey = beacon_pk.p2wpkh_script()
    address = script_pubkey.address(network="regtest")

    esplora_api = "http://localhost:3000"
    esplora_client = EsploraClient(esplora_api)

    address_manager = AddressManager(esplora_client, network, script_pubkey, beacon_sk)

    print("utxos", address_manager.utxo_tx_ins)

    regtest_api = "http://localhost:18443"

    bitcoinrpc = BitcoinRPC.from_config(regtest_api, ("polaruser", "polarpass"))

    result = await bitcoinrpc.acall("send", {"outputs": {address: 0.2}})

    funding_txid = result["txid"]
    funding_tx_hex = await bitcoinrpc.acall("getrawtransaction", {"txid": funding_txid})
    funding_tx = Tx.parse_hex(funding_tx_hex)

    print("funding tx", funding_tx.id())

    # address_manager.utxo_tx_ins = address_manager.fetch_utxos()
    address_manager.add_funding_tx(funding_tx)

    beacon_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=3)
    beacon_pk = beacon_sk.point

    script_pubkey = beacon_pk.p2wpkh_script()
    script_pubkey.address(network="regtest")

    address_manager.send_to_address(script_pubkey, 1000)

    print("UTXOs", len(address_manager.utxo_tx_ins))
    print(address_manager.utxo_tx_ins)


asyncio.run(test_beacon_manager())
