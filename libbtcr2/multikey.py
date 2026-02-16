from multiformats import varint, multibase
from buidl.ecc import S256Point

from .constants import SECP256K1_PUBLIC_KEY_CODEC

SECP256K1_PUBLIC_KEY_PREFIX = varint.encode(SECP256K1_PUBLIC_KEY_CODEC)


def get_public_key_multibase(key_bytes):
    multikey_bytes = SECP256K1_PUBLIC_KEY_PREFIX + key_bytes
    multikey_value = multibase.encode(multikey_bytes, "base58btc")
    return multikey_value
