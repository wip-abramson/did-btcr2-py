from buidl.ecc import S256Point
import math

from .bech32 import encode_bech32_identifier, decode_bech32_identifier
from.verificationMethod import get_verification_method
from pydid.did import DID
from .error import InvalidDidError

BITCOIN="bitcoin"
SIGNET="signet"
TESTNET3="testnet3"
TESTNET4="testnet4"
REGTEST="regtest"
MUTINYNET="mutinynet"

NETWORKS = [BITCOIN, SIGNET, REGTEST, TESTNET3, TESTNET4, MUTINYNET, None, None, None, None, None, None, 1, 2, 3, 4]

VERSIONS = [1]

EXTERNAL = "external"
KEY = "key"


id_type_to_hrp = {}

id_type_to_hrp[EXTERNAL] = "x"
id_type_to_hrp[KEY] = "k"

hrp_to_id_type = {v: k for k, v in id_type_to_hrp.items()}

network_map = {
    0x0: "bitcoin",
    0x1: "signet",
    0x2: "regtest",
    0x3: "testnet3",
    0x4: "testnet4",
    0x5: "mutinynet",
}



P2PKH = "p2pkh"
P2WPKH = "p2wpkh"
P2TR = "p2tr"

SINGLETON_BEACON_TYPE = "SingletonBeacon"

CONTEXT = ["https://www.w3.org/ns/did/v1", "https://did-btcr2/TBD/context"]

PLACEHOLDER_DID = "did:btcr2:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"




def encode_identifier(id_type, version, network, genesis_bytes):
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
        except:
            raise InvalidDidError("Genesis bytes is not a valid compressed secp256k1 public key")

    hrp = id_type_to_hrp[id_type]
    
    nibbles = []
    f_count = math.floor((version - 1) / 15)

    for i in range(f_count):
        nibbles.append(15)
        
    nibbles.append((version - 1) % 15)
    nibbles.append(network_num)

    if len(nibbles) % 2 == 1:
        nibbles.append(0)


    nibble_range = int(len(nibbles) / 2) - 1
    data_bytes = bytearray()

    if f_count == 0:
        concat = (nibbles[2 * 0] << 4) | nibbles[2 * 0 + 1]
        data_bytes.append((nibbles[2 * 0] << 4) | nibbles[2 * 0 + 1])
    else:
        for index in range(nibble_range):
            print(index)
            raise NotImplementedError()


    data_bytes += bytearray(genesis_bytes)

    identifier = "did:btcr2:"

    encoded_string = encode_bech32_identifier(hrp, data_bytes)

    identifier += encoded_string

    return DID(identifier)



def decode_identifier(identifier):
    components = identifier.split(":")
    if len(components) != 3:
        raise InvalidDidError()
    
    if components[0] != "did":
        raise InvalidDidError()

    if components[1] != "btcr2":
        raise Exception("methodNotSupported")
    
    encoded_string = components[2]

    hrp, data_bytes = decode_bech32_identifier(encoded_string)

    id_type = hrp_to_id_type.get(hrp)
    
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

    network = network_map.get(network_value)

    if not network:
        if 0xC <= network_value <= 0xF:
            network = network_value - 0xB
        else:
            raise InvalidDidError()

    if nibbles_consumed % 2 == 1:
        filler_nibble = current_byte & 0x0F
        if filler_nibble != 0:
            raise InvalidDidError()
        
    genesis_bytes = data_bytes[byte_index+1:]

    if id_type == KEY:
        try:
            S256Point.parse_sec(genesis_bytes)
        except:
            raise InvalidDidError()
    
    return id_type, version, network, genesis_bytes
        





