# Anonymizing Identifiers

The internal question that the following was an answer to was (roughly)

> How should we anonymize selected fields from production B5 database tables when importing into oue datalake

## Background and terminology

For those outside of 1Password, "B5" is is our backend for the 1Password service, and "datalake" is a database with broader internal access.

To better illustrate the kinds of things we may wish to analyze from the kinds of data in B5 are things such as

- "On average, what proportion of enrolled members of business accounts have connected to the service in the past 14 days?"
- "At the end of the free trial period, what is the average number of items users have created distinguishing between users who did or did not convert their trial accounts to paid?"

Those are examples of questions that can be answered by analyzing data which which is a by-product of providing the service.

## Identifiers

Roughly speaking, we hold two types of identifiers.
There are identifiers like the member email address, e.g., `hudson@bstreet.example` or the account domain, `baker21.1password.eu`.
Those identifiers contain information that correlates with non-B5 information about the customer.

There are other identifiers used by B5 which are deliberately designed to contain no information information about customers outside of our database.
These are randomly generated 128 bit numbers encoded using base-32 encoding.
So a user UUID would be something like `LIBGNOEGNHCJB5RZYLWXA37PRI`.

The UUIDs are designed to not be secret, but within the B5 database, it is possible to
go from a UUID to, say, an email address.
Indeed, this is required for providing the service.
For example, 1Password would not be able to present members of a team the email address of
the person they are sharing an vault with without some mechanism to get from UUIDs to human oriented identifiers.

Direct access to the B5 data base is tightly restricted and monitored.
The 1Password customer support Backoffice system has some access and many 1Password employees have access to that Backoffice system.

## The purpose of anonymizing identifiers

The datalake is designed to be used for research into the kinds of questions used above,
but we do not wish the data in datalake to be usable for working backwards to the identifiers in B5. There may be exceptional cases where working backwards that way is necessary,
the system we design should treat such things as exceptional.
Thus the goal here is to enable research into the kinds of questions listed above, while creating technical barriers to working backwards.

For the types of analyses we need, the anonymized identifiers in data lake should be

- Deterministically created from the B5 identifiers. That is the transformation process should be a function in that f(x) = y should always produce the same y each time it is given a particular x.
- One-to-one. That is distinct identifiers in B5 must map to distinct anonymized identifiers in datalake.
- Not be reversible. Given an anonymized identifier in datalake it should be impossible (without special permission or access) to determine the identifier in B5.

## (Salted) hashes are not enough

First let me point out that the "obvious" approach does not work.
The obvious approach would be hash the field. It is true that a cryptographic hash is impossible[^999] to reverse, but that holds only when nothing is known about the input.
These can easily be reversed if one has good guesses about the input.
For example, suppose we are talking about email addresses.
An attacker with the list of email addresses of B5 users could perform the same hash on each email address and have their own table that maps back and forth between the email addresses and hash.

[^999]: Where "impossible" is suitably defined.

A widely reported case of such de-anonymization this way is the [NYC cab drivers case](https://arstechnica.com/tech-policy/2014/06/poorly-anonymized-logs-reveal-nyc-cab-drivers-detailed-whereabouts/).
This is a common error, in part because many people overlook a crucial requirement in the definition of pre-image resistance.
A cryptographically secure hash function is pre-image resistance,
but that does make the hash irreversible if set of pre-images can be narrowed down.

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

