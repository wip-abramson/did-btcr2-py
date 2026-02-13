from .builder import Btcr2DIDDocumentBuilder
from pydid.verification_method import VerificationMethod
import jsonpatch
from pydid.doc import DIDDocument
import jcs
import base58
import json
from buidl.helper import sha256, bytes_to_str
import copy
from di_bip340.cryptosuite import Bip340JcsCryptoSuite
from di_bip340.data_integrity_proof import DataIntegrityProof
from di_bip340.multikey import SchnorrSecp256k1Multikey
import urllib
import logging

logger = logging.getLogger(__name__)

class Btcr2DIDDocumentUpdater():

    def __init__(self, document_builder: Btcr2DIDDocumentBuilder, version):
        self.builder = document_builder
        self.current_version = version
        self.current_document = self.builder.build().model_copy(deep=True)
        self.update_patch = []

    def add_verification_method(self, verificationMethod: VerificationMethod):
        VerificationMethod.model_validate(verificationMethod)
        vm_path = f"/verificationMethod/{len(self.builder.verification_method.methods)}"

        vm_json = verificationMethod.serialize()
        patch = self.get_patch('add', vm_path, vm_json)
        self.builder.verification_method.methods.append(verificationMethod) 

        self.update_patch.append(patch)

    def add_service(self, service):
        service_path = f"/service/{len(self.builder.service.services)}"

        service_json = service.serialize()
        logger.debug("Document before add_service: %s", json.dumps(self.current_document.serialize(), indent=2))
        self.builder.service.services.append(service)
        logger.debug("Document after add_service: %s", json.dumps(self.current_document.serialize(), indent=2))

        patch = self.get_patch('add', service_path, service_json)

        self.update_patch.append(patch)

    def get_patch(self, op, path, value):
        patch = {'op': op, 'path': path, 'value': value}
        return patch


    def validate_update(self):
        logger.debug("JSON Patch: %s", json.dumps(self.update_patch))
        json_patch = jsonpatch.JsonPatch(self.update_patch)
        # print("Before Patch \n")
        next_document = self.current_document.model_copy(deep=True).serialize()

        logger.debug("Before patch: %s", json.dumps(next_document, indent=2))
        next_document = json_patch.apply(next_document)
        # print("After patch\n")
        logger.debug("After patch: %s", json.dumps(next_document, indent=2))

        # print(json.dumps(next_document, indent=2))
        next_hash = sha256(jcs.canonicalize(next_document))
        check_document = self.builder.build().serialize()
        # print(json.dumps(check_document, indent=2))
        check_hash = sha256(jcs.canonicalize(check_document))
        if check_hash != next_hash:
            raise Exception("InvalidUpdate")

    def construct_update_payload(self):
        self.validate_update()
        source_hash = self.current_document.canonicalize()
        target_hash = self.builder.build().canonicalize()
        target_version_id = self.current_version + 1
        update_payload = {
            '@context': [
                'https://w3id.org/security/v2',
                'https://w3id.org/zcap/v1',
                'https://w3id.org/json-ld-patch/v1'
                # TODO did:btcr2 zcap context
            ],
            'patch': self.update_patch,
            # TODO: this might not go here?
            'sourceHash': bytes_to_str(base58.b58encode(source_hash)),
            'targetHash': bytes_to_str(base58.b58encode(target_hash)),
            'targetVersionId': target_version_id
        }

        logger.debug("Update payload: %s", update_payload)
        self.update_payload = update_payload

        return update_payload
    
    def finalize_update_payload(self, vm_id, signing_key):
        did_update_invocation = copy.deepcopy(self.update_payload)

        multikey = SchnorrSecp256k1Multikey(id=vm_id, controller=self.current_document.id, private_key=signing_key)
        cryptosuite = Bip340JcsCryptoSuite(multikey)
        di_proof = DataIntegrityProof(cryptosuite)

        root_capability_id = f"urn:zcap:root:{urllib.parse.quote(self.current_document.id)}"

        options = {
                "type": "DataIntegrityProof",
                "cryptosuite": "bip340-jcs-2025",
                "verificationMethod": multikey.full_id(),
                "proofPurpose": "capabilityInvocation",
                "capability": root_capability_id,
                "capabilityAction": "Write"
        }

        logger.debug("Update payload for signing: %s", json.dumps(self.update_payload, indent=2))

        secured_did_update_payload = di_proof.add_proof(did_update_invocation, options)
        mediaType = "application/json"

        expected_proof_purpose = "capabilityInvocation"

        update_bytes = json.dumps(secured_did_update_payload)

        verificationResult = di_proof.verify_proof(mediaType, update_bytes, expected_proof_purpose, None, None)

        if not verificationResult:
            raise Exception("invalidUpdateProof")
        
        self.current_document = self.builder.build().model_copy(deep=True)

        return secured_did_update_payload
    

# class Btcr2UpdatePayload():

#     def __init__(self, current_document, version, patch):
#         json_patch = jsonpatch.JsonPatch(patch)
#         target_document = json_patch.apply(current_document)
#         source_hash = sha256(jcs.canonicalize(current_document.serialize()))
#         target_hash = sha256(jcs.canonicalize(self.builder.build().serialize()))
#         target_version_id = self.current_version + 1
#         update_payload = {
#             '@context': [
#                 'https://w3id.org/security/v2',
#                 'https://w3id.org/zcap/v1',
#                 'https://w3id.org/json-ld-patch/v1'
#                 # TODO did:btcr2 zcap context
#             ],
#             'patch': self.update_patch,
#             # TODO: this might not go here?
#             'sourceHash': base58.b58encode(source_hash),
#             'targetHash': base58.b58encode(target_hash),
#             'targetVersionId': target_version_id
#         }


    
