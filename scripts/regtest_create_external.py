from buidl.mnemonic import secure_mnemonic
from buidl.hd import HDPrivateKey
from pydid.verification_method import Multikey
from pydid.doc.builder import VerificationMethodBuilder
from pydid.did import DIDUrl
import json
import asyncio
from libbtcr2.did import encode_identifier, decode_identifier, PLACEHOLDER_DID
from libbtcr2.resolver import Btcr2Resolver
from libbtcr2.service import SingletonBeaconService
from libbtcr2.diddoc.builder import Btcr2DIDDocumentBuilder, IntermediateBtcr2DIDDocumentBuilder
from libbtcr2.multikey import get_public_key_multibase
import os
from libbtcr2.did_manager import DIDManager
from libbtcr2.diddoc.builder import Btcr2ServiceBuilder
from libbtcr2.helpers import fund_regtest_beacon_address
from bitcoinrpc import BitcoinRPC

async def generate_external_test_vector():

    didkey_purpose = "11"
    ## Run this if you want a new hardware key
    mnemonic = secure_mnemonic()

    # mnemonic = "prosper can dial lumber write coconut express imitate husband isolate inside release brush media please kind comic pill science repeat basic also endorse bronze"
    root_hdpriv = HDPrivateKey.from_mnemonic(mnemonic, network="regtest")
    print("Mnemonic : ", mnemonic)
    
    builder = IntermediateBtcr2DIDDocumentBuilder(controller=[PLACEHOLDER_DID])

    auth_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=0)
    auth_pk = auth_sk.point

    print("Secp256k1 PrivateKey", auth_sk.hex())
    print("Secp256k1 Public Key", auth_pk.sec())
    
    pk_multibase = get_public_key_multibase(auth_pk.sec())

    vm = builder.verification_method.add(Multikey, controller=PLACEHOLDER_DID, public_key_multibase = pk_multibase)

    builder.authentication.reference(vm.id)

    # builder.authentication.add(Multikey, public_key_multibase=pk_multibase)
    
    cap_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=1)
    cap_pk = cap_sk.point

    print("Secp256k1 PrivateKey", cap_sk.hex())
    print("Secp256k1 Public Key", cap_pk.sec())
    

    
    pk_multibase = get_public_key_multibase(cap_pk.sec())

    cap_vm = builder.verification_method.add(Multikey, controller=PLACEHOLDER_DID, public_key_multibase=pk_multibase)
    
    keys = {
        vm.id: {
            "pk": auth_pk.sec().hex(),
            "sk": auth_sk.hex()
        },
        cap_vm.id: {
            "pk": cap_pk.sec().hex(),
            "sk": cap_sk.hex()
        },
    }
        
    builder.capability_invocation.reference(cap_vm.id)
    builder.capability_delegation.reference(cap_vm.id)
    
    beacon_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=1)
    beacon_pk = beacon_sk.point
    
    beacon_script = beacon_pk.p2wpkh_script()
    address = beacon_script.address(network="regtest")

    beacon_service = builder.service.add_singleton_beacon(beacon_address=address)

    intermediate_doc = builder.build()

    print(json.dumps(intermediate_doc.serialize(), indent=2))
    
    rpc_endpoint = "http://localhost:18443"
    network = "regtest"
    bitcoin_rpc = BitcoinRPC.from_config(rpc_endpoint, ("polaruser", "polarpass"))

    did_manager = DIDManager(network=network)

    
    
    identifier, did_doc = did_manager.create_external(intermediate_doc, network)

    for service in did_doc.service:
        if service.type == "SingletonBeacon":
            beacon_manager =did_manager.add_beacon_manager(service.id, beacon_sk, beacon_script)
            await fund_regtest_beacon_address(bitcoin_rpc, beacon_manager)
    
    
    print(json.dumps(did_doc.serialize(), indent=2))

    did_path = identifier.split(":")[2]
    
    folder_path = f"TestVectors/{network}/{did_path}"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        

    
    did_path = f"{folder_path}/did.txt"
    
    with open(did_path, "w") as f:
        f.write(identifier)
    
    intermediate_path = f"{folder_path}/intermediateDidDoc.json"
    
    with open(intermediate_path, "w") as f:
        json.dump(intermediate_doc.serialize(), f, indent=2)
    
    initial_path = f"{folder_path}/initialDidDoc.json"
    
    with open(initial_path, "w") as f:
        json.dump(did_doc.serialize(), f, indent=2)
        
        
    rpc_endpoint = "http://localhost:18443"

        
    
    updater = did_manager.updater()

    new_beacon_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=2)

    beacon_script = new_beacon_sk.point.p2wpkh_script()
    address = beacon_script.address(network=network)

    service_builder = Btcr2ServiceBuilder(identifier, services=did_doc.service)

    new_beacon_service = service_builder.add_singleton_beacon(address)

    beacon_manager = did_manager.add_beacon_manager(new_beacon_service.id, new_beacon_sk, beacon_script)
    await fund_regtest_beacon_address(bitcoin_rpc, beacon_manager)

    updater.add_service(new_beacon_service)
    
    new_vm_sk = root_hdpriv.get_private_key(didkey_purpose, address_num=3)
    
    new_vm_pk = new_vm_sk.point
    
    new_pk_multibase = get_public_key_multibase(new_vm_pk.sec())

    vm_builder = VerificationMethodBuilder(identifier, methods=did_doc.verification_method)
    
    new_vm = vm_builder.add(Multikey, public_key_multibase=new_pk_multibase)
    
    updater.add_verification_method(new_vm)

    beacon_id = DIDUrl.unparse(identifier, beacon_service.id.path, beacon_service.id.query, beacon_service.id.fragment)
    cap_vm_id = DIDUrl.unparse(identifier, cap_vm.id.path, cap_vm.id.query, cap_vm.id.fragment)

    updated_doc = await did_manager.finalize_update_payload(updater, cap_vm_id, cap_sk, beacon_id)
    
    resolver = Btcr2Resolver(logging=True)


    keys[new_beacon_service.id] = {
            "pk": new_beacon_sk.point.sec().hex(),
            "sk": new_beacon_sk.hex()
    }
    keys[new_vm.id] = {
            "pk": new_vm_pk.sec().hex(),
            "sk": new_vm_sk.hex()
    }
    
    
    keys_path = f"{folder_path}/keys.json"
    
    with open(keys_path, "w") as f:
        json.dump(keys, f, indent=2)
        
    
    print("Updated Doc")
    print(json.dumps(updated_doc.serialize(), indent=2))
    print("Sidecar data")
    print(json.dumps(did_manager.get_sidecar_data(), indent=2))
    
    resolution_options = {
        "sidecarData": did_manager.get_sidecar_data()
    }
    
    res_options_path = f"{folder_path}/resolutionOptions.json"
    
    with open(res_options_path, "w") as f:
        json.dump(resolution_options, f, indent=2)
        
    target_doc_path = f"{folder_path}/targetDidDocument.json"
    
    with open(target_doc_path, "w") as f:
        json.dump(updated_doc.serialize(), f, indent=2)
    
    
asyncio.run(generate_external_test_vector())