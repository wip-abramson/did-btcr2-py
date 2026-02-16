import asyncio
import json

from buidl.hd import HDPrivateKey
from buidl.mnemonic import secure_mnemonic

from libbtcr2.did_manager import DIDManager


async def generate_deterministic_test_vector():

    didkey_purpose = "11"
    ## Run this if you want a new hardware key
    mnemonic = secure_mnemonic()
    network = "mutinynet"
    btc_network = "signet"

    # mnemonic = (
    #     "prosper can dial lumber write coconut express imitate husband isolate inside"
    #     " release brush media please kind comic pill science repeat basic also endorse bronze"
    # )
    root_hdpriv = HDPrivateKey.from_mnemonic(mnemonic, network=btc_network)
    print("Mnemonic : ", mnemonic)

    initial_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=0)
    initial_pk = initial_sk.point

    print("Secp256k1 PrivateKey", initial_sk.hex())
    print("Secp256k1 Public Key", initial_pk.sec())

    did_manager = DIDManager(
        did_network=network, btc_network=btc_network, esplora_base="https://mutinynet.com/api"
    )

    identifier, did_doc = await did_manager.create_deterministic(initial_sk, network)

    print(identifier)
    print(json.dumps(did_doc.serialize(), indent=2))


asyncio.run(generate_deterministic_test_vector())
