from buidl.bech32 import bc32encode, BECH32_ALPHABET, encode_bech32, convertbits, bech32m_create_checksum, bech32m_verify_checksum
from buidl.helper import int_to_big_endian

from .constants import ID_TYPE_TO_HRP as PREFIX, HRP_TO_ID_TYPE as TYPE_FOR_PREFIX, BECH32_CHECKSUM_LEN


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
