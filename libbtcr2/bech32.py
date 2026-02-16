from buidl.bech32 import (
    BECH32_ALPHABET,
    bech32m_create_checksum,
    bech32m_verify_checksum,
    convertbits,
    encode_bech32,
)

from .constants import BECH32_CHECKSUM_LEN
from .constants import HRP_TO_ID_TYPE as TYPE_FOR_PREFIX


def encode_bech32_identifier(hrp, value):
    data = convertbits(value, 8, 5)
    checksum = bech32m_create_checksum(hrp, data)
    encoded = encode_bech32(data + checksum)

    return hrp + "1" + encoded


def decode_bech32_identifier(value):
    hrp, raw_data = value.split("1")

    type = TYPE_FOR_PREFIX.get(hrp)
    if not type:
        raise ValueError(f"unknown human readable part: {hrp}")

    data = [BECH32_ALPHABET.index(c) for c in raw_data]

    if not bech32m_verify_checksum(hrp, data):
        raise ValueError(f"bad bech32 encoding: {value}")

    # Remove checksum
    data = data[0:-BECH32_CHECKSUM_LEN]

    genesis_bytes = bytes(convertbits(data, 5, 8, False))

    return [hrp, genesis_bytes]
