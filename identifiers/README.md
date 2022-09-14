# Anonymizing Identifiers

The internal question that the following was an answer to was (roughly)

> How should we anonymize selected fields from production B5 database tables when importing into datalake

For those outside of 1Password, "B5" is is our backend for the 1Password service, and "datalake" is a database with broader internal access.

Some of the details depend on what the anonymized field is to be used for. In the best case (from a security and privacy POV), we simply wouldn't export the field in the first place. But let's consider the case where we have a field in B5 that we would like to JOIN (or INDEX) on datalake. Thus however we transform the B5 data field, we need to be able to transform it the same way into each table in datalake. The transformation must be deterministic.

## (Salted) hashes are not enough

First let me point out that the "obvious" approach does not work. The obvious approach would be hash the field. It is true that a cryptographic hash is impossible[^999] to reverse, but that holds only when nothing is known about the input. These can easily be reversed if one has good guesses about the input. For example, suppose we are talking about email addresses. An attacker with the list of email addresses of B5 users could perform the same hash on each email address and have their own table that maps back and forth between the email addresses and hash. Indeed, this kind of thing happens all the time

[^999]: Where "impossible" is suitably defined.

## A keyed hash

Exactly how to implement this will depend on the cryptographic tools available to the export process. I will first describe it in terms of HMAC. All examples of HMAC assume HMAC-SHA256.

We use a keyed hash construction. There will be a secret that is required to hash the data. Let's call it `hash_key`. Let's call the raw field from B5, `src` and what gets stored in datalake `hashed_src`. 

The attached Python has lots of comments, and lots of fiddly things for converting strings to bytes and back again.

This pseudo-code leaves out many parameters and details.
```
secret_hash_key <- get_hash_key_from_vault()
for src in b5_table {
    hashed_src_bytes <- HMAC(key = secret_hash_key, msg = src)
    truncated_hash <- truncate(hashed_src_bytes)
    hashed_src <- encode_to_string(truncated_hash)
    write_out(hashed_src)
}
```

### Parameters and details

- SHA256 for HMAC's hash.

    It doesn't really matter what we use here, but using SHA256 means that we don't need to explain or defend why it doesn't matter.

- Truncation is of the number of bytes before being converted to a string. Using 15 bytes may make other things easier.

    Truncation is not for security purposes. It is only needed if it is useful for performance reasons in data lake.

    Do not truncate the string representation. Truncation is of the bytes returned by HMAC
    
    The length to truncate to must be at least [^12] 12 bytes and must be not be longer than the number of bytes that the HMAC returns. When using SHA256, HMAC returns 32 bytes.

    The truncation length can be tuned for the kind of string encoding to come later. If base64 is to be used, it is useful to start with a multiple of 3 bytes. If base32 is to be used, it is useful to start with a multiple of 5 bytes. If hex is used, then it doesn't matter.

- encode_to_string. The strings are not meant for human consumption or use. They are meant for our SQL engine. Base64 seems right to me, but database experts may have other opinions.

[^12]: We could get away with fewer than 12 bytes if that becomes important, but then I would need to do a bunch of ugly calculations to start working out concrete collision risks of doing so.

## Secret secrecy

In principle nobody should ever know or see or have access to the secret hash key. Anyone with access will have the ability to de-anonymize. We can change it at will as long as we know that the newly generated tables won't work with tables
generated under a previous key.

If we are generating all the tables fresh with each run instead of incrementally appending, then the hash_key can be generated randomly for each run, and not preserved anywhere.

