import logging
import math

from buidl.ecc import S256Point
from pydid.did import DID

from .bech32 import decode_bech32_identifier, encode_bech32_identifier
from .constants import (
    DID_METHOD,
    DID_METHOD_PREFIX,
    DID_SCHEME,
    EXTERNAL,
    HRP_TO_ID_TYPE,
    ID_TYPE_TO_HRP,
    KEY,
    NETWORK_MAP,
    NETWORKS,
)
from .error import InvalidDidError

logger = logging.getLogger(__name__)


def encode_identifier(id_type, version, network, genesis_bytes):
    logger.debug("Encoding identifier: type=%s, version=%s, network=%s", id_type, version, network)
    if id_type not in [EXTERNAL, KEY]:
        raise InvalidDidError()

    if version != 1:
        raise InvalidDidError()

    network_num = None
    if network is not None and network not in NETWORKS:
        raise InvalidDidError(f"Network not recognised {network}")
    else:
        network_num = NETWORKS.index(network)

    if id_type == KEY:
        try:
            S256Point.parse_sec(genesis_bytes)
        except Exception:
            raise InvalidDidError(
                "Genesis bytes is not a valid compressed" + " secp256k1 public key"
            ) from None

    hrp = ID_TYPE_TO_HRP[id_type]

    nibbles = []
    f_count = math.floor((version - 1) / 15)

    for _i in range(f_count):
        nibbles.append(15)

    nibbles.append((version - 1) % 15)
    nibbles.append(network_num)

    if len(nibbles) % 2 == 1:
        nibbles.append(0)

    nibble_range = int(len(nibbles) / 2) - 1
    data_bytes = bytearray()

    if f_count == 0:
        data_bytes.append((nibbles[2 * 0] << 4) | nibbles[2 * 0 + 1])
    else:
        for index in range(nibble_range):
            logger.debug("index: %s", index)
            raise NotImplementedError()

    data_bytes += bytearray(genesis_bytes)

    identifier = DID_METHOD_PREFIX

    encoded_string = encode_bech32_identifier(hrp, data_bytes)

    identifier += encoded_string

    logger.debug("Encoded identifier: %s", identifier)
    return DID(identifier)


def decode_identifier(identifier):
    logger.debug("Decoding identifier: %s", identifier)
    components = identifier.split(":")
    if len(components) != 3:
        raise InvalidDidError()

    if components[0] != DID_SCHEME:
        raise InvalidDidError()

    if components[1] != DID_METHOD:
        raise Exception("methodNotSupported")

    encoded_string = components[2]

    hrp, data_bytes = decode_bech32_identifier(encoded_string)

    id_type = HRP_TO_ID_TYPE.get(hrp)

    if id_type is None:
        raise InvalidDidError()

    version = 1

    byte_index = 0

    nibbles_consumed = 0

    current_byte = data_bytes[byte_index]

    version_nibble = current_byte >> 4

    while version_nibble == 0xF:
        version += 15
        # TODO
        if nibbles_consumed % 2 == 0:
            version_nibble = current_byte & 0x0F
        else:
            byte_index += 1
            current_byte = data_bytes[byte_index]
            version_nibble = current_byte >> 4
        nibbles_consumed += 1

    version += version_nibble
    nibbles_consumed += 1

    if nibbles_consumed % 2 == 0:
        byte_index += 1
        current_byte = data_bytes[byte_index]
        network_nibble = current_byte >> 4
    else:
        network_nibble = current_byte & 0x0F

    nibbles_consumed += 1
    network_value = network_nibble

    network = NETWORK_MAP.get(network_value)

    if not network:
        if 0xC <= network_value <= 0xF:
            network = network_value - 0xB
        else:
            raise InvalidDidError()

    if nibbles_consumed % 2 == 1:
        filler_nibble = current_byte & 0x0F
        if filler_nibble != 0:
            raise InvalidDidError()

    genesis_bytes = data_bytes[byte_index + 1 :]

    if id_type == KEY:
        try:
            S256Point.parse_sec(genesis_bytes)
        except Exception:
            raise InvalidDidError() from None

    logger.debug("Decoded: type=%s, version=%s, network=%s", id_type, version, network)
    return id_type, version, network, genesis_bytes
