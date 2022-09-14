# Requires Python 3.7 or later.
import hmac
import base64

# The hash_key is a high entropy secret that we will
# pull from something like Secrets Automation.
# I will use a password in this example,
# but if we do use a password for this master secret,
# it should be generated as a gibberish/random password of at
# least 23 characters in length.


def get_hash_key_from_vault() -> bytes:
    """Retrieves the secret hash key from a well protected place.

    This could just randomly generate a string with at least 128 bits of
    entropy if we do not need results to be repeatable on separate runs.
    """

    # for this demo code, we just return something hard coded.
    # Do not use this in action. In action secret needs to be better protected
    return b'XCGkaWfQQ9TQyfDLVKebYdH'


# src is our field from b5 that we want to anonymize
# We would be reading these from B5.
field_from_b5: list[str] = [
    'amelia@erhardt.fm',
    'James.Hoffa@floor.lakemi.us',
    'db_cooper@rocky_mtn.high.co.us',
]


def truncate(data: bytes, byte_length=15) -> bytes:
    """returns truncated data to min(byte_length, digest_size."""

    # 15 is a good default. It is collision safe for any plausible
    # number of things we are hashing, and it will produce cleaner results
    # with both base64 and base32 stringifications.
    length = min(byte_length, len(data))
    return data[:length]


def encode_to_string(data: bytes) -> str:
    """Encodes bytes to a string that is compact and indexable in DB."""
    return base64.b64encode(data).decode(encoding="ascii")


hash_key: bytes = get_hash_key_from_vault()

# There is an optimization that can be done which
# pre-computes and allocates some constant stuff outside of the loop.
# If this loop needs optimizing, let me (Jeffrey Goldberg)
# know.
for src in field_from_b5:
    hashed_src_bytes = hmac.digest(
        key=hash_key,
        msg=src.encode('utf-8'),
        digest='sha256'
    )

    truncated_hash = truncate(hashed_src_bytes)
    hashed_src = encode_to_string(truncated_hash)

    print(hashed_src)
