from pydid.doc.builder import ServiceBuilder, DIDDocumentBuilder
from pydid.did import DID
from pydid.doc.builder import DIDDocumentBuilder, RelationshipBuilder, VerificationMethodBuilder
from pydid.doc import DIDDocument
from pydid.verification_method import Multikey

from buidl.ecc import S256Point

from ..service import SingletonBeaconService
from ..did import PLACEHOLDER_DID, KEY
from typing import Iterator, List, Optional, Type, Union
from .doc import IntermediateBtcr2DIDDocument, Btcr2Document
from ..did import encode_identifier
from ..multikey import get_public_key_multibase

class Btcr2ServiceBuilder(ServiceBuilder):

    def add_singleton_beacon(self, beacon_address: str, ident: Optional[str] = None):
        ident = ident or next(self._id_generator)

        service_endpoint = f"bitcoin:{beacon_address}"
        service = SingletonBeaconService.make(
            id=self._did.ref(ident),
            service_endpoint=service_endpoint    
        )

        self.services.append(service)
        return service        
    


    

class Btcr2DIDDocumentBuilder(DIDDocumentBuilder):

    def __init__(
        self,
        id: Union[str, DID],
        context: List[str] = None,
        *,
        also_known_as: List[str] = None,
        controller: Union[List[str], List[DID]] = None,
    ):
        super().__init__(id=id, context=context, also_known_as=also_known_as, controller=controller)
        self.context = context or self.__default_context()
        self.service = Btcr2ServiceBuilder(self.id)

    @staticmethod
    def __default_context() -> List[str]:
        return ["https://www.w3.org/TR/did-1.1", "https://did-btcr2/TBD/context"]
    
    @classmethod
    def from_secp256k1_key(cls, initial_key: S256Point, network="bitcoin", version=1):
        key_bytes = initial_key.sec()
        did_btcr2 = encode_identifier(KEY, version, network, key_bytes)

        builder = cls(
            id=did_btcr2,
        )

        vm_id = "initialKey"

        public_key_multibase = get_public_key_multibase(key_bytes)

        verificationMethod = builder.verification_method.add(Multikey, vm_id, controller=did_btcr2, public_key_multibase=public_key_multibase)

        # vm = get_verification_method(btcr2_identifier, initial_key, vm_id)

        # did_document["verificationMethod"] = [vm]

        builder.authentication.reference(verificationMethod.id)
        builder.assertion_method.reference(verificationMethod.id)
        builder.capability_delegation.reference(verificationMethod.id)
        builder.capability_invocation.reference(verificationMethod.id)

        if network == "bitcoin":
            network = "mainnet"
        if network == "testnet3" or network == "testnet4":
            network = "testnet"
        if network == "mutinynet":
            network = "signet"
        elif isinstance(network, int):
            # TODO: what should network be when custom?
            network = "signet"

        p2pkh_address = initial_key.p2pkh_script().address(network)
        builder.service.add_singleton_beacon(p2pkh_address, "initialP2PKH")

        p2wpkh_address = initial_key.p2wpkh_address(network=network)
        builder.service.add_singleton_beacon(p2wpkh_address, "initialP2WPKH")

        p2tr_address = initial_key.p2tr_address(network=network)
        builder.service.add_singleton_beacon(p2tr_address, "initialP2TR")

        return builder
    
    def build(self) -> Btcr2Document:
        return Btcr2Document.model_construct(
            id=self.id,
            context=self.context,
            also_known_as=self.also_known_as,
            controller=self.controller,
            verification_method=self.verification_method.methods or None,
            authentication=self.authentication.methods or None,
            assertion_method=self.assertion_method.methods or None,
            key_agreement=self.key_agreement.methods or None,
            capability_invocation=self.capability_invocation.methods or None,
            capability_delegation=self.capability_delegation.methods or None,
            service=self.service.services or None,
            **self.extra,
        )

class IntermediateBtcr2DIDDocumentBuilder(Btcr2DIDDocumentBuilder):
    def __init__(
        self,
        context: List[str] = None,
        *,
        also_known_as: List[str] = None,
        controller: Union[List[str], List[DID]] = None,
    ):
        super().__init__(id=PLACEHOLDER_DID, context=context, also_known_as=also_known_as, controller=controller)

    def build(self) -> IntermediateBtcr2DIDDocument:
        return IntermediateBtcr2DIDDocument.model_construct(
            context=self.context,
            also_known_as=self.also_known_as,
            controller=self.controller,
            verification_method=self.verification_method.methods or None,
            authentication=self.authentication.methods or None,
            assertion_method=self.assertion_method.methods or None,
            key_agreement=self.key_agreement.methods or None,
            capability_invocation=self.capability_invocation.methods or None,
            capability_delegation=self.capability_delegation.methods or None,
            service=self.service.services or None,
            **self.extra,
        )
    
    @classmethod
    def from_doc(cls, doc: DIDDocument) -> "IntermediateBtcr2DIDDocumentBuilder":
        builder = cls(
            context=doc.context,
            also_known_as=doc.also_known_as,
            controller=doc.controller,
        )
        
        vm = doc.verification_method.model_copy(deep=True)
        vm.id = PLACEHOLDER_DID
        builder.verification_method = VerificationMethodBuilder(
            PLACEHOLDER_DID, methods=doc.verification_method
        )
        builder.authentication = RelationshipBuilder(
            PLACEHOLDER_DID, "auth", methods=doc.authentication
        )
        builder.assertion_method = RelationshipBuilder(
            PLACEHOLDER_DID, "assert", methods=doc.assertion_method
        )
        builder.key_agreement = RelationshipBuilder(
            PLACEHOLDER_DID, "key-agreement", methods=doc.key_agreement
        )
        builder.capability_invocation = RelationshipBuilder(
            PLACEHOLDER_DID, "capability-invocation", methods=doc.capability_invocation
        )
        builder.capability_delegation = RelationshipBuilder(
            PLACEHOLDER_DID, "capability-delegation", methods=doc.capability_delegation
        )
        builder.service = Btcr2ServiceBuilder(PLACEHOLDER_DID, services=doc.service)
        return builder
    