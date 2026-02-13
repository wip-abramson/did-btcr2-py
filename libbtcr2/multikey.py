from multiformats import varint, multibase
from buidl.ecc import S256Point

SECP256K1_PUBLIC_KEY_PREFIX = varint.encode(0xe7)


def get_public_key_multibase(key_bytes):
    multikey_bytes = SECP256K1_PUBLIC_KEY_PREFIX + key_bytes
    multikey_value = multibase.encode(multikey_bytes, "base58btc")
    return multikey_value