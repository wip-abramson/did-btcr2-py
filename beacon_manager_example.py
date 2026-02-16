import asyncio

from bitcoinrpc import BitcoinRPC
from buidl.hd import HDPrivateKey
from buidl.helper import sha256
from buidl.mnemonic import secure_mnemonic
from buidl.tx import Tx
from pydid.verification_method import Multikey

from libbtcr2.beacon_manager import BeaconManager
from libbtcr2.did import PLACEHOLDER_DID
from libbtcr2.did_manager import DIDManager
from libbtcr2.diddoc.builder import (
    IntermediateBtcr2DIDDocumentBuilder,
)
from libbtcr2.multikey import get_public_key_multibase


async def test_beacon_manager():

    didkey_purpose = "11"
    ## Run this if you want a new hardware key
    mnemonic = secure_mnemonic()

    # mnemonic = (
    #     "prosper can dial lumber write coconut express imitate husband isolate inside"
    #     " release brush media please kind comic pill science repeat basic also endorse bronze"
    # )
    root_hdpriv = HDPrivateKey.from_mnemonic(mnemonic, network="regtest")
    print("Mnemonic : ", mnemonic)

    builder = IntermediateBtcr2DIDDocumentBuilder(controller=[PLACEHOLDER_DID])

    auth_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=0)
    auth_pk = auth_sk.point

    print("Secp256k1 PrivateKey", auth_sk.hex())
    print("Secp256k1 Public Key", auth_pk.sec())

    pk_multibase = get_public_key_multibase(auth_pk.sec())

    vm = builder.verification_method.add(
        Multikey, controller=PLACEHOLDER_DID, public_key_multibase=pk_multibase
    )

    builder.authentication.reference(vm.id)

    # builder.authentication.add(Multikey, public_key_multibase=pk_multibase)

    cap_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=1)
    cap_pk = cap_sk.point

    print("Secp256k1 PrivateKey", cap_sk.hex())
    print("Secp256k1 Public Key", cap_pk.sec())

    pk_multibase = get_public_key_multibase(cap_pk.sec())

    cap_vm = builder.verification_method.add(
        Multikey, controller=PLACEHOLDER_DID, public_key_multibase=pk_multibase
    )

    builder.capability_invocation.reference(cap_vm.id)
    builder.capability_delegation.reference(cap_vm.id)

    beacon_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=2)
    beacon_pk = beacon_sk.point

    script_pubkey = beacon_pk.p2wpkh_script()
    address = script_pubkey.address(network="regtest")

    print("Beacon Address", address, beacon_pk.p2wpkh_address(network="regtest"))
    beacon_service = builder.service.add_singleton_beacon(beacon_address=address)

    intermediate_doc = builder.build()

    rpc_endpoint = "http://localhost:18443"
    network = "regtest"

    bitcoinrpc = BitcoinRPC.from_config(rpc_endpoint, ("polaruser", "polarpass"))

    did_manager = DIDManager(
        network=network, rpc_endpoint=rpc_endpoint, rpcuser="polaruser", rpcpassword="polarpass"
    )

    identifier, did_doc = did_manager.create_external(intermediate_doc, network)

    beacon_service = did_doc.service[0]

    beacon_manager = BeaconManager(bitcoinrpc, network, beacon_service.id, beacon_sk, script_pubkey)

    result = await bitcoinrpc.acall("send", {"outputs": {beacon_service.address(): 0.2}})

    funding_txid = result["txid"]
    funding_tx_hex = await bitcoinrpc.acall("getrawtransaction", {"txid": funding_txid})
    funding_tx = Tx.parse_hex(funding_tx_hex)

    beacon_manager.add_funding_tx(funding_tx)

    test_commitment = sha256(b"TESTBEACONCOMMITMENT")

    pending_signal = beacon_manager.construct_beacon_signal(test_commitment)

    signed_signal = beacon_manager.sign_beacon_signal(pending_signal)

    signed_hex = signed_signal.serialize().hex()
    signal_id = await bitcoinrpc.acall("sendrawtransaction", {"hexstring": signed_hex})

    print("Successfully broadcast beacon signal", signal_id)
    print("UTXOs", len(beacon_manager.utxos))
    print(beacon_manager.utxos)


asyncio.run(test_beacon_manager())
