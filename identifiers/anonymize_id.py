import sys
if sys.version_info < (3, 6):
    raise RuntimeError("Requires Python 3.6 or later")
import hmac # requires 3.4
from hmac import HMAC
import base64
import secrets # requires 3.6
from typing import Iterable, Optional # requires 3.5

# This sample/demo code for anonymizing identifiers is excessively factored
# and very verbose, particular when it comes to communicated expected types.
# This is deliberate to help better communicate what is going on.
#
# This demo/sample code uses a hardcoded key. Do not do the same in action.
# The keys should be fetched from a secure storage mechanism, such as
# 1Password's Secrets Automation.

def print_demo() -> None:
    """Illustrates some usages."""
    
    print('Demo 1: anonymize_field("email") iteration')
    for anon in anonymize_field("email", use_demo=True):
        print(anon)

    print('\nDemo 2: Use Anonymizer')
    # You really shouldn't be holding on this secret this scope,
    # so it is better to use the mechanism from Demo 1.
    hash_key = get_hash_key_from_vault("email", use_demo=True)
    email_anonymizer = Anonymizer(hash_key)
    for addr in get_b5_field("email", use_demo=True):
        print(email_anonymizer.from_str(addr))

    print('\nDemo 3: w/ throwaway key via anonymize field')
    for anon in anonymize_field("email", throwaway=True, use_demo=True):
        print(anon)

    print('\nDemo 4: Use Anonymizer with throw away field')
    email_anonymizer = Anonymizer()
    for addr in get_b5_field("email", use_demo=True):
        print(email_anonymizer.from_str(addr))

class Anonymizer:
    def __init__(self, hash_key: bytes | None = None) -> None:
        """Initialize a new Anonymizer with a key or generate key if None."""

        if hash_key == None:
            hash_key = secrets.token_bytes()
        
        if not isinstance(hash_key, bytes):
            raise ValueError("hash key isn't bytes")
        if len(hash_key) < 16:
            raise ValueError("hash key is too short")

        # This is to compute keying and hasher creation just once
        self.instance_hmac: HMAC = hmac.new(hash_key, digestmod='sha256')

    def from_str(self, src: str) -> str:
        """returns an anonymized form of the input src."""

        # We do NOT want to update the initialized hasher
        # each time this is called, so we make copy.
        try:
            local_hmac: HMAC = self.instance_hmac.copy()
        except AttributeError:
            raise Exception("Anonymizer must be initialized before using")

        local_hmac.update(src.encode('utf-8'))
        anon_bytes: bytes = local_hmac.digest()
        anon_truncated_bytes: bytes = truncate(anon_bytes)
        anon_str: str = encode_to_string(anon_truncated_bytes)

        return(anon_str)

class _DemoData:
    known_fields = ['email']
    keys_from_vault: dict[str, bytes] = {"email": b'XCGkaWfQQ9TQyfDLVKebYdH'}
    data_from_field: dict[str, list[str]] = { "email": [
        'amelia@erhardt.fm',
        'James.Hoffa@floor.lakemi.us',
        'db_cooper@rocky_mtn.high.co.us',
    ]}

# This demo deals a list of source data, and a list output.
# In real usage Iterators may make more sense, but this demo.
def anonymize_field(b5_field_name: str, throwaway: bool = False, use_demo: bool = False) -> Iterable[str]:
    """Returns a list of anonymized IDs for field using a key that it fetches.
    
    Parameters
    ----------
    b5_field_name: The name of the identifer field in the source DB
    
    throwaway: If we don't need the same key for previous or subsequenct runs, and never need to reverse
    """

    if not isinstance(b5_field_name, str):
        raise TypeError("field name should be a string")

    # get (or create) the secret hashing key
    hash_key: Optional[bytes] = None
    if not throwaway:
        hash_key = get_hash_key_from_vault(b5_field_name, use_demo)

    # Create and initialize our keyed anonyimzer
    anonymizer = Anonymizer(hash_key)

    anonymized_ids: list[str] = []
    for src in get_b5_field("email", use_demo=use_demo):
        anon_id = anonymizer.from_str(src)
        anonymized_ids.append(anon_id)

    return anonymized_ids

def _true_get_field(field_name: str) -> Iterable[str]:
    raise NotImplementedError

def get_b5_field(field_name: str, use_demo: bool = False) -> Iterable[str]:
    """This would be able to read from the relevant B5 tables."""

    if not use_demo:
        return _true_get_field(field_name)

    # We will use our sample data in _DemoData

    if field_name not in _DemoData.known_fields:
        # Given the potential for malicious input, we should not write out
        # a potentially malicious field name.
        raise ValueError("We can't fetch the field requested")

    return _DemoData.data_from_field[field_name]

# The hash_key is a high entropy secret that we will
# pull from something like Secrets Automation.
# I will use a password in this example,
# but if we do use a password for this master secret,
# it should be generated as a gibberish/random password of at
# least 23 characters in length.

def _true_get_hash_key(field: str) -> bytes:
    raise NotImplementedError()


def get_hash_key_from_vault(field: str, use_demo: bool = False) -> bytes:
    """Retrieves the secret hash key for field from a well protected place.
    """

    if not use_demo:
        return _true_get_hash_key(field)
    
    # Everything else here is using demo data
    # this is just a demo, and the only field we know about is "email"
    if field not in _DemoData.known_fields:
        # This is security sensitive code. The input field string
        # may be malicious. Best not to log or display it without performing
        # additional checks.
        raise ValueError("unknown field")

    return _DemoData.keys_from_vault[field]


def truncate(data: bytes, byte_length: int = 15) -> bytes:
    """returns truncated data to min(byte_length, digest_size."""

    # 15 is a good default. It is collision safe for any plausible
    # number of things we are hashing, and it will produce cleaner results
    # with both base64 and base32 stringifications.

    length = min(byte_length, len(data))

    if length < 12:
        raise ValueError("byte_length must be at least 12")
    return data[:length]

def encode_to_string(data: bytes) -> str:
    """Encodes bytes to a string that is compact and indexable in DB."""
    return base64.b64encode(data).decode(encoding="ascii")

if __name__ == "__main__":
    print_demo()
