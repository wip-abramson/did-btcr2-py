from unittest import TestCase, IsolatedAsyncioTestCase
from buidl.ecc import S256Point, PrivateKey, N
from libbtcr2.did_manager import DIDManager
from random import randint

class DIDManagerTest(IsolatedAsyncioTestCase):

    sk = PrivateKey.parse("KyZpNDKnfs94vbrwhJneDi77V6jF64PWPF8x5cdJb8ifgg2DUc9d")
    pubkey = sk.point
    did_network = "bitcoin"
    btc_network = "mainnet"

    expected_identifier = "did:btcr2:k1qqpnp4206rw5yznwt7xnvf847dyzet34pauatur4806mamuu9kg670qvqx7vy"

    async def test_deterministic_did(self):

        print(randint(0, N))
        did_manager = DIDManager(did_network=self.did_network, btc_network=self.btc_network)
        identifier, did_doc = await did_manager.create_deterministic(self.sk, self.did_network)
        self.assertEqual(identifier, self.expected_identifier)

        self.assertEqual(did_doc.id, identifier)
        self.assertEqual(did_doc.controller, None)
        self.assertEqual(len(did_doc.verification_method), 1)
        self.assertEqual(did_doc.verification_method[0].type, "Multikey")

        self.assertEqual(did_doc.verification_method[0].id, did_doc.id + "#initialKey")        
        self.assertEqual(did_doc.verification_method[0].id, did_doc.capability_delegation[0])
        self.assertEqual(did_doc.verification_method[0].id, did_doc.capability_invocation[0])
        self.assertEqual(did_doc.verification_method[0].id, did_doc.authentication[0])
        self.assertEqual(did_doc.verification_method[0].id, did_doc.assertion_method[0])