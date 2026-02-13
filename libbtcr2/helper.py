import jcs
from buidl.helper import sha256


def canonicalize_and_hash(document):
    return sha256(jcs.canonicalize(document))