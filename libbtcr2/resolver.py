from buidl.ecc import S256Point
from buidl.tx import Tx
from buidl.helper import sha256, bytes_to_str
import base58
import jcs
import os
import json
import copy
from ipfs_cid import cid_sha256_wrap_digest
import urllib
import jsonpatch
from pydid.doc import DIDDocument
from pydid.doc.builder import VerificationMethodBuilder
from pydid.verification_method import Multikey
from di_bip340.cryptosuite import Bip340JcsCryptoSuite
from di_bip340.data_integrity_proof import DataIntegrityProof
from di_bip340.multikey import SchnorrSecp256k1Multikey
from .bech32 import decode_bech32_identifier
from .verificationMethod import get_verification_method
from .did import decode_identifier, KEY, EXTERNAL, InvalidDidError
from .diddoc.builder import Btcr2DIDDocumentBuilder, IntermediateBtcr2DIDDocumentBuilder
from .diddoc.doc import Btcr2Document, IntermediateBtcr2DIDDocument
from .helper import canonicalize_and_hash
from .service import BeaconTypeNames, SingletonBeaconService
from .esplora_client import EsploraClient
import datetime
import logging

logger = logging.getLogger(__name__)

CONTEXT = ["https://www.w3.org/ns/did/v1", "https://did-btcr2/TBD/context"]


GENESIS_COINBASE = "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"
COINBASE_TXIDS = [GENESIS_COINBASE, "0000000000000000000000000000000000000000000000000000000000000000"]

SINGLETON_BEACON_TYPE = "SingletonBeacon"
P2PKH = "p2pkh"
P2WPKH = "p2wpkh"
P2TR = "p2tr"

DEFAULT_NETWORK_DEFINITIONS = {
    "regtest": {
        "btc_network": "regtest",
        "esplora_api": "http://localhost:3000",
    }
}


class Btcr2Resolver():
    
    def __init__(self, networkDefinitions=DEFAULT_NETWORK_DEFINITIONS, logging=False, log_folder="TestVectors"):
        self.logging = logging
        self.log_base_folder = log_folder
        self.networks = self.configure_networks(networkDefinitions)

    def configure_networks(self, networkDefinitions):
        networks = {}
        for network, networkDefinition in networkDefinitions.items():
            definition = {
                "btc_network": networkDefinition.get("btc_network"),
                "esplora_client": EsploraClient(networkDefinition.get("esplora_api")),
            }
            networks[network] = definition
        return networks

    async def resolve(self, identifier, resolution_options=None):
    
        id_type, version, network, genesis_bytes = decode_identifier(identifier)

        if not self.networks.get(network):
            raise Exception("Unsupported Network")

        logger.info("ID Components: %s %s %s %s", id_type, version, network, genesis_bytes.hex())

        if self.logging == True:
            did_path = identifier.split(":")[2]
            self.log_folder = f"{self.log_base_folder}/{network}/{did_path}"
            if not os.path.exists(self.log_folder):
                os.makedirs(self.log_folder)


        if id_type == KEY:
            initial_did_document = self.resolve_deterministic(identifier, 
                                                        genesis_bytes, 
                                                        version, 
                                                        network)
        elif id_type == EXTERNAL:
            initial_did_document = await self.resolve_external(identifier, genesis_bytes, version, network, resolution_options)

        else:
            raise Exception("Invalid HRP")
        
        # TODO: Process Beacon Signals
        logger.info("Initial DID document")
        logger.debug("%s", json.dumps(initial_did_document.serialize(), indent=2))
        target_document, version_id = await self.resolve_target_document(initial_did_document, resolution_options, network)


        logger.info("Target DID document")
        logger.debug("%s", target_document)

        resolution_result = {
            "didDocument": target_document.serialize(),
            "didResolutionMetadata": {
                
            },
            "didDocumentMetadata": {
                "network": network,
                "version": version_id
            }
        }

        return resolution_result



    def resolve_deterministic(self, btcr2_identifier, key_bytes, version, network):
        logger.debug("Resolving deterministic DID: %s", btcr2_identifier)
        pubkey = S256Point.parse_sec(key_bytes)

        builder = Btcr2DIDDocumentBuilder.from_secp256k1_key(pubkey, network, version)

        did_document = builder.build()

        if btcr2_identifier != did_document.id:
            raise InvalidDidError("identifier does not match, deterministic document id")

        return did_document
    
    async def resolve_external(self, btcr2_identifier, genesis_bytes, version, network, resolution_options):
        sidecar_data = resolution_options.get("sidecarData")
        initial_document = None
        if sidecar_data:
            doc_json = sidecar_data.get("initialDocument")
            logger.info("Sidecar Initial External Resolve")
            logger.debug("%s", json.dumps(doc_json, indent=2))
            initial_document = Btcr2Document.deserialize(doc_json)
            
        
        if initial_document:
            initial_document = self.sidecar_initial_document_validation(btcr2_identifier, genesis_bytes, version, network, initial_document)
        else:
            initial_document = self.cas_retrieval(btcr2_identifier, genesis_bytes, version, network)

        # TODO: validate initial document

        return initial_document

    def sidecar_initial_document_validation(self, btcr2_identifier, genesis_bytes, version, network, initial_document):
        logger.info("Initial Doc")
        logger.debug("%s", json.dumps(initial_document.serialize(), indent=2))
        intermediate_doc = IntermediateBtcr2DIDDocument.from_did_document(initial_document)

        logger.info("Intermediate Doc")
        logger.debug("%s", json.dumps(intermediate_doc.serialize(), indent=2))
        logger.info("Initial Doc")
        logger.debug("%s", json.dumps(initial_document.serialize(), indent=2))
        hash_bytes = intermediate_doc.canonicalize()
        
        if hash_bytes != genesis_bytes:
            raise InvalidDidError("Initial document provided, does not match identifier genesis bytes")

        return initial_document
    
    async def cas_retrieval(self, btcr2_identifier, genesis_bytes, version, network):
        cid = cid_sha256_wrap_digest(genesis_bytes)
        # TODO: Attempt to fetch content for CID from IPFS
        raise NotImplemented

    async def resolve_target_document(self, initial_document: DIDDocument, resolution_options, network):
        request_version_id = resolution_options.get("versionId")
        version_time = resolution_options.get("versionTime")
        logger.debug("Resolving target document: versionId=%s, versionTime=%s", request_version_id, version_time)

        if request_version_id and version_time:
            raise Exception("InvalidResolutionOptions - cannot have versionTime and versionId")

        if not request_version_id and not version_time:
            version_time = datetime.datetime.now().timestamp()

        sidecar_data = resolution_options.get("sidecarData")

        signals_metadata = None
        if sidecar_data:
            signals_metadata = sidecar_data.get("signalsMetadata")

        current_version_id = 1

        if current_version_id == request_version_id:
            return initial_document, current_version_id
        
        update_hash_history = []

        contemporary_blockheight = 0

        contemporary_document = initial_document.model_copy()

        target_document, current_version_id = await self.traverse_blockchain_history(contemporary_document, 
                                                           contemporary_blockheight, 
                                                           current_version_id, 
                                                           request_version_id, 
                                                           version_time, 
                                                           update_hash_history, 
                                                           signals_metadata, 
                                                           network)

        return target_document, current_version_id

    

    async def traverse_blockchain_history(self, 
                                          contemporary_document: Btcr2Document, 
                                          contemporary_blockheight, 
                                          current_version_id, 
                                          request_version_id, 
                                          target_time, 
                                          update_hash_history, 
                                          signals_metadata,
                                          network):
        contemporary_hash = contemporary_document.model_copy(deep=True).canonicalize()    
        beacons = []
        for service in contemporary_document.service:
            # print("SERVICETYPE", service.type, type(service))
            if service.type in BeaconTypeNames:
                beacons.append(service)

        next_signals = await self.find_next_signals(beacons, contemporary_blockheight, network)
        logger.debug("Next Signals: %s", next_signals)
        if len(next_signals) == 0:
            return contemporary_document, current_version_id
        
        
        # print("Next Signals", next_signals[0]['status']["block_time"], target_time)
        if next_signals[0]["block_time"] > target_time:
            return contemporary_document, current_version_id
        
        

        contemporary_blockheight = next_signals[0]["block_height"]
        logger.debug("Block height: %s, target time: %s", contemporary_blockheight, target_time)
        # signals = next_signals["signals"]

        updates = self.process_beacon_signals(next_signals, signals_metadata)
        
        logger.debug("Updates: %s", updates)

        if self.logging and len(updates) != 0:
            self.block_folder = f"{self.log_folder}/block{contemporary_blockheight}"
            if not os.path.exists(self.block_folder):
                os.makedirs(self.block_folder)
            # next_signals_path = f"{block_folder}/next_signals.json"
            
            # with open(next_signals_path, "w") as f:
            #     print(next_signals)
            #     serialized_signals = copy.deepcopy(next_signals)
            #     for index, tx in enumerate(serialized_signals["signals"]):
            #         serialized_signals["signals"][index] = tx.serialize().hex()
            #     json.dump(serialized_signals, f, indent=2)
            
            
            updates_path = f"{self.block_folder}/updates.json"
            
            with open(updates_path, "w") as f:
                json.dump(updates, f, indent=2)

        updates.sort(key=lambda update: update["targetVersionId"])

        for update in updates:
            target_version_id = update["targetVersionId"]
            if target_version_id <= current_version_id:
                self.confirm_duplicate_update(update, update_hash_history)
            elif target_version_id == current_version_id + 1:
                logger.debug("Source hash: %s, contemporary hash: %s", update["sourceHash"], bytes_to_str(base58.b58encode(contemporary_hash)))
                if update["sourceHash"] != bytes_to_str(base58.b58encode(contemporary_hash)):
                    raise Exception("Late Publishing")
                logger.info("Apply DID Update: %s", update)
                contemporary_document = self.apply_did_update(contemporary_document, update).model_copy(deep=True)
                if self.logging:
                    contemporary_path = f"{self.block_folder}/contemporaryDidDocument.json"
                    with open(contemporary_path, "w") as f:
                        json.dump(contemporary_document.serialize(), f, indent=2)
                        
                current_version_id += 1
                updateHash = sha256(jcs.canonicalize(update))
                update_hash_history.append(updateHash)
                contemporary_hash = bytes_to_str(base58.b58encode(contemporary_document.canonicalize()))
                if current_version_id == request_version_id:
                    logger.info("Found document for target version: %s", contemporary_document)
                    return contemporary_document, current_version_id

            elif target_version_id > current_version_id + 1:
                logger.debug("target_version_id: %s, current_version_id: %s", target_version_id, current_version_id)
                raise Exception(f"Late publishing {target_version_id} {current_version_id}") 
        
        logger.debug("Tracking: %s %s", contemporary_blockheight, target_time)
        if contemporary_blockheight == target_time:
            logger.info("Got to target: %s", contemporary_blockheight)
            return contemporary_document
        
        contemporary_blockheight += 1

        target_document, current_version_id = await self.traverse_blockchain_history(contemporary_document,
                                                            contemporary_blockheight,
                                                            current_version_id,
                                                            request_version_id,
                                                            target_time,
                                                            update_hash_history,
                                                            signals_metadata,
                                                            network)

        return target_document, current_version_id

    async def find_next_signals(self, beacons, contemporary_blockheight, network):
        signals = []
        esplora_client = self.networks[network]["esplora_client"]
        logger.debug("Scanning %d beacons from block height %s", len(beacons), contemporary_blockheight)
        for beacon in beacons:
            address = beacon.address()
            logger.debug("Checking beacon %s at address %s", beacon.id, address)
            txs = esplora_client.get_address_transactions(address)
            for tx_data in txs:
            # Only care about bitcoin transactions that have been accepted into the chain.

                # Skip transactions that haven't been confirmed yet or are from earlier blocks
                if 'status' not in tx_data or 'block_height' not in tx_data['status']:
                    continue
                if tx_data['status']['block_height'] < contemporary_blockheight:
                    continue

                if any(vin['prevout']['scriptpubkey_address'] == address for vin in tx_data['vin']):
                    tx_hex = esplora_client.get_transaction_hex(tx_data['txid'])
                    tx = Tx.parse_hex(tx_hex)
                    signal = {
                        "beaconId": beacon.id,
                        "beaconType": beacon.type,
                        "tx": tx,
                        "block_height": tx_data['status']['block_height'],
                        "block_time": tx_data['status']['block_time']
                    }
                    signals.append(signal)


        # Sort signals by block height
        signals.sort(key=lambda signal: signal['block_height'])
        
        # Only keep signals from the earliest block height found
        if signals:
            min_height = signals[0]['block_height']
            signals = [signal for signal in signals if signal['block_height'] == min_height]

        logger.debug("Found %d signals at earliest block height", len(signals))
        return signals
    

    def process_beacon_signals(self, signals, signals_metadata):
        updates = []

        for signal in signals:
            type = signal["beaconType"]
            signal_tx = signal["tx"]
            signal_id = signal_tx.id()
            signal_sidecar_data = signals_metadata.get(signal_id)
            did_update_payload = None
            if type == "SingletonBeacon":
                logger.debug("Signal ID: %s", signal_id)
                did_update_payload = self.process_singleton_beacon_signal(signal_tx, signal_sidecar_data)

            if did_update_payload:
                updates.append(did_update_payload)
        
        return updates

    def process_singleton_beacon_signal(self, tx: Tx, signal_sidecar_data):
        tx_out = tx.tx_outs[len(tx.tx_outs) - 1]
        did_update_payload = None
        logger.debug("TX OUT: %s", tx_out.script_pubkey.commands[1])
        if (tx_out.script_pubkey.commands[0] != 106 and len(tx_out.script_pubkey.commands[1]) != 32):
            logger.warning("Not a beacon signal")
            return did_update_payload
        
        hash_bytes = tx_out.script_pubkey.commands[1]
        logger.debug("Beacon signal hash: %s", hash_bytes.hex())

        if signal_sidecar_data:
            did_update_payload = signal_sidecar_data.get("updatePayload")

            if not did_update_payload:
                raise Exception("InvalidSidecarData")
            
            update_hash_bytes = sha256(jcs.canonicalize(did_update_payload))

            if update_hash_bytes != hash_bytes:
                raise Exception("InvalidSidecarData")
            
            return did_update_payload
        else:
            payload_cid = cid_sha256_wrap_digest(hash_bytes)
            # TODO: Fetch payload from IPFS
            raise Exception("Not implemented")
        

    def confirm_duplicate_update(self, update, update_hash_history):

        update_hash = sha256(jcs.canonicalize(update))
        # Note: version starts at 1, index starts at 0
        update_hash_index = update["targetVersionId"] - 2
        historical_update_hash = update_hash_history[update_hash_index]
        if (historical_update_hash != update_hash):
            raise Exception("Late Publishing Error")
        return    

        
    def apply_did_update(self, contemporary_document, update):
        # Retrieve the verification method used to secure the proof from the contemporary DID document
        capability_id = update["proof"]["capability"]
        document_to_update = contemporary_document.model_copy(deep=True)

        root_capability = self.dereference_root_capability(capability_id)
        
        proof_vm_id = update["proof"]["verificationMethod"]
        btcr2_identifier = document_to_update.id
        verification_method = None
        for vm in document_to_update.verification_method:
            vm_id = vm.id
            if vm_id[0] == "#":
                vm_id = f"{btcr2_identifier}{vm_id}"
            if vm_id == proof_vm_id:
                logger.debug("Verification Method found: %s", vm)
                verification_method = vm.serialize()
        if verification_method == None:
            raise Exception("Invalid Proof on Update Payload")
        multikey = SchnorrSecp256k1Multikey.from_verification_method(verification_method)

        # Instantiate a schnorr-secp256k1-2025 cryptosuite instance.
        cryptosuite = Bip340JcsCryptoSuite(multikey)
        di_proof = DataIntegrityProof(cryptosuite=cryptosuite)

        mediaType = "application/json"

        expected_proof_purpose = "capabilityInvocation"

        update_bytes = json.dumps(update)

        if self.logging:
            canonical_update = jcs.canonicalize(update)
            update_hash = sha256(canonical_update)

            with open(f"{self.block_folder}/canonical_document.txt", "w") as f:
                f.write(bytes_to_str(canonical_update))

            with open(f"{self.block_folder}/update_hash_hex.txt", "w") as f:
                f.write(update_hash.hex())


        verificationResult = di_proof.verify_proof(mediaType, update_bytes, expected_proof_purpose, None, None)
        logger.debug("Proof verification result: %s", verificationResult)

        if not verificationResult["verified"]:
            raise Exception("invalidUpdateProof")

        target_did_document = copy.deepcopy(document_to_update.serialize())

        update_patch = update["patch"]

        patch = jsonpatch.JsonPatch(update_patch)
        
        target_did_document = patch.apply(target_did_document)

        target_hash = bytes_to_str(base58.b58encode(sha256(jcs.canonicalize(target_did_document))))

        target_doc = Btcr2Document.model_validate(target_did_document)
        
        serialzied_doc = target_doc.serialize()
        
        compare_dictionaries(serialzied_doc, target_did_document)
        
        
        test_hash = bytes_to_str(base58.b58encode(target_doc.canonicalize()))

        logger.debug("Target hash check: %s %s", update["targetHash"], target_hash)
        if (target_hash != update["targetHash"]):
            raise Exception("LatePublishingError")
        
        if (target_hash != test_hash):
            raise Exception("LatePublishingError")

        return Btcr2Document.deserialize(target_did_document)
    
    

    def dereference_root_capability(self, capability_id):
    
        components = capability_id.split(":")
        assert(len(components) == 4)
        assert(components[0] == "urn")
        assert(components[1] == "zcap")
        assert(components[2] == "root")
        uri_encoded_id = components[3]
        btcr2Identifier = urllib.parse.unquote(uri_encoded_id)
        root_capability = {
            "@context": "https://w3id.org/zcap/v1",
            "id": capability_id,
            "controller": btcr2Identifier,
            "invocationTarget": btcr2Identifier
        }
        return root_capability

def compare_dictionaries(dict1, dict2):
    if len(dict1) != len(dict2):
        return False
    for key in dict1:
        if key not in dict2 or dict1[key] != dict2[key]:
            return False
    return True