# Requires Python 3.7 or later.
import hmac
from hmac import HMAC
import base64

# This sample/demo code for anonymizing identifiers is excessively factored
# and very verbose, particular when it comes to communicated expected types.
# This is deliberate to help better communicate what is going on.
#
# This demo/sample code uses a hardcoded key. Do not do the same in action.
# The keys should be fetched from a secure storage mechanism, such as
# 1Password's Secrets Automation.

class Anonymizer:
    def __init__(self, hash_key):
        """Initialize a new Anonymizer with a key."""

        # This is to compute keying and hasher creation just once
        self.instance_hmac: HMAC = hmac.new(hash_key, digestmod='sha256')

    def from_str(self, src: str) -> str:
        """returns an anonymized form of the imput src."""

        # We do NOT want to update the initialized hasher
        # each time this is called, so we make copy.
        try:
             local_hmac: HMAC = self.instance_hmac.copy()
        except AttributeError:
            raise Exception("Anonymizer must be initialied before using")

        local_hmac.update(src.encode('utf-8'))
        anon_bytes: bytes = local_hmac.digest()
        anon_truncated_bytes: bytes = truncate(anon_bytes)
        anon_str: str = encode_to_string(anon_truncated_bytes)

        return(anon_str)
    

# This demo deals a list of source data, and a list output.
# In real usage Iterators may make more sense, but this demo.
def anonymize_field(b5_field_name: str) -> list[str]:
    """Returns a list of anonymized IDs for the B5 field."""

    # get (or create) the secret hashing key
    hash_key: bytes = get_hash_key_from_vault(field=b5_field_name)

    # Create and initialize our keyed anonyimzer
    anonymizer = Anonymizer(hash_key)

    anonymized_ids: list[str] = []
    for src in get_b5_field("email"):
        anon_id = anonymizer.from_str(src)
        anonymized_ids.append(anon_id)

    return anonymized_ids

def get_b5_field(field_name: str) -> list[str]:
    """This would be able to read from the relevant B5 tables."""

    # This sample code returns a list, but a more generic iterator may make
    # sense when actually reading from a database.

    # In this example code, the only field we know about is email
    if field_name not in ["email"]:
        # Given the potential for malicious input, we should not write out
        # a potentially malicious field name.
        raise ValueError("We can't fetch the field requested")

    # our sample data is just a single short list
    return [
        'amelia@erhardt.fm',
        'James.Hoffa@floor.lakemi.us',
        'db_cooper@rocky_mtn.high.co.us',
    ]

# The hash_key is a high entropy secret that we will
# pull from something like Secrets Automation.
# I will use a password in this example,
# but if we do use a password for this master secret,
# it should be generated as a gibberish/random password of at
# least 23 characters in length.
def get_hash_key_from_vault(field: str) -> bytes:
    """Retrieves the secret hash key for field from a well protected place.

    This could just randomly generate a string with at least 128 bits of
    entropy if we do not need results to be repeatable on separate runs.
    """

    # this is just a demo, and the only field we know about is "email"
    if field not in ["email"]:
        # This is security sensitive code. The input field string
        # may be malicious. Best not to log or display it without performing
        # additional checks.
        raise ValueError("unknown field")

    # for this demo code, we just return something hard coded.
    # Do NOT use a hard coded key in action.
    # The secret needs to be better protected and managed.
    return b'XCGkaWfQQ9TQyfDLVKebYdH'

def truncate(data: bytes, byte_length=15) -> bytes:
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


def main():
    for anon in anonymize_field("email"):
        print(anon)

if __name__ == "__main__":
    main()
