from unittest import TestCase

from libbtcr2.did import EXTERNAL, KEY, decode_identifier, encode_identifier


class DIDTest(TestCase):
    good_encode_decode_tests = [
        {
            "did": "did:btcr2:k1qqptaz4ydc2q8qjgch9kl46y48ccdhjyqdzxxjmmaupwsv9sut5ssfsm0s3dn",
            "identifier_components": {
                "id_type": KEY,
                "version": 1,
                "network": "bitcoin",
                "genesis_bytes": bytes.fromhex(
                    "02be8aa46e14038248c5cb6fd744a9f186de440344634b7bef02e830b0e2e90826"
                ),
            },
        },
        {
            "did": "did:btcr2:k1qvpxlu8m9l4jw9czmthaf7zf6e96pfv2ak05utxmwhrv0zrtgrgdrwggpepd9",
            "identifier_components": {
                "id_type": KEY,
                "version": 1,
                "network": "testnet3",
                "genesis_bytes": bytes.fromhex(
                    "026ff0fb2feb271702daefd4f849d64ba0a58aed9f4e2cdb75c6c7886b40d0d1b9"
                ),
            },
        },
        {
            "did": "did:btcr2:k1qypvksjk8vfxpp0pl6jzwvc4sw7knmv8q4l2j5j2vgsjwfrfer2vqqqgrc3cx",
            "identifier_components": {
                "id_type": KEY,
                "version": 1,
                "network": "signet",
                "genesis_bytes": bytes.fromhex(
                    "02cb42563b126085e1fea427331583bd69ed87057ea9524a6221272469c8d4c000"
                ),
            },
        },
        {
            "did": "did:btcr2:k1psppl550jkrj9l2caef72m98k3z2ytvfkjv9uftv3htkn8n54979cwg5ht5py",
            "identifier_components": {
                "id_type": KEY,
                "version": 1,
                "network": 1,
                "genesis_bytes": bytes.fromhex(
                    "021fd28f958722fd58ee53e56ca7b444a22d89b4985e256c8dd7699e74a97c5c39"
                ),
            },
        },
        {
            "did": "did:btcr2:x1qzlqmvawa6ya5fx4qyf27a85p34z07z060h352qxgl65fr6d4ugmzm5tzxq",
            "identifier_components": {
                "id_type": EXTERNAL,
                "version": 1,
                "network": "bitcoin",
                "genesis_bytes": bytes.fromhex(
                    "be0db3aeee89da24d50112af74f40c6a27f84fd3ef1a280647f5448f4daf11b1"
                ),
            },
        },
        {
            "did": "did:btcr2:x1q2lqmvawa6ya5fx4qyf27a85p34z07z060h352qxgl65fr6d4ugmzxrg4q8",
            "identifier_components": {
                "id_type": EXTERNAL,
                "version": 1,
                "network": "regtest",
                "genesis_bytes": bytes.fromhex(
                    "be0db3aeee89da24d50112af74f40c6a27f84fd3ef1a280647f5448f4daf11b1"
                ),
            },
        },
        {
            "did": "did:btcr2:x1qjlqmvawa6ya5fx4qyf27a85p34z07z060h352qxgl65fr6d4ugmzgnd92w",
            "identifier_components": {
                "id_type": EXTERNAL,
                "version": 1,
                "network": "testnet4",
                "genesis_bytes": bytes.fromhex(
                    "be0db3aeee89da24d50112af74f40c6a27f84fd3ef1a280647f5448f4daf11b1"
                ),
            },
        },
        {
            "did": "did:btcr2:k1q5p4f9a0af7qtj83apkdd96zhlhk3ndhv3reu75lju503s82qkslvfgl7pq9r",
            "identifier_components": {
                "id_type": KEY,
                "network": "mutinynet",
                "genesis_bytes": bytes.fromhex(
                    "035497afea7c05c8f1e86cd69742bfef68cdb764479e7a9f9728f8c0ea05a1f625"
                ),
                "version": 1,
            },
        },
    ]

    def test_decode_identifier(self):

        for test in self.good_encode_decode_tests:
            id_type, version, network, genesis_bytes = decode_identifier(test["did"])

            self.assertEqual(id_type, test["identifier_components"]["id_type"])
            self.assertEqual(version, test["identifier_components"]["version"])
            self.assertEqual(network, test["identifier_components"]["network"])
            self.assertEqual(genesis_bytes, test["identifier_components"]["genesis_bytes"])

    def test_encode_identifier(self):

        for test in self.good_encode_decode_tests:
            id_type = test["identifier_components"]["id_type"]
            version = test["identifier_components"]["version"]
            network = test["identifier_components"]["network"]
            genesis_bytes = test["identifier_components"]["genesis_bytes"]

            identifier = encode_identifier(id_type, version, network, genesis_bytes)

            self.assertEqual(identifier, test["did"])
