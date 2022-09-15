# Anonymizing Identifiers

The internal question that the following was an answer to was (roughly)

> How should we anonymize selected fields from production B5 database tables when importing into our datalake

## Background and terminology

For those outside of 1Password, "B5" is is our backend for the 1Password service, and "datalake" is a database with broader internal access.

To better illustrate the kinds of things we may wish to analyze from the kinds of data in B5 are things such as

1. "At the end of the free trial period, what is the average number of items users have created distinguishing between users who did or did not convert their trial accounts to paid?"
2. "On average, what proportion of enrolled members of business accounts have connected to the service in the past 14 days?"

Those are examples of questions that can be answered by analyzing data which which is a by-product of providing the service. Answering example question (1) does not require making use of any identifiers beyond the ability to JOIN tables indicating number of items and the status of the account as paid or trial.
But that ability to join (or have things in the same record within a database table) is most naturally served by using an anonymized user identifier.

The second example question requires some way to identify which users are in the same account as other users. That is we need to be able to make tallies within accounts. The most natural (and technically plausible) way to do this is to make use of anonymized account identifiers.
Again, we will also need to JOIN based on anonymized user identifiers.

## Identifiers

Roughly speaking, B5 holds two types of identifiers.
There are identifiers like the member email address, e.g., `hudson@bstreet21.example` or the account domain, `baker21.1password.eu`.
Those identifiers contain information that correlates with non-B5 information about the customer.

There are other identifiers used by B5 which are deliberately designed to contain no information information about customers outside of our database.
These are randomly generated 128 bit numbers encoded using base-32 encoding.
So a user UUID would be something like `LIBGNOEGNHCJB5RZYLWXA37PRI`.

The UUIDs are designed to not be secret. That is knowledge of a UUID is never used to authenticate any process.
Within the B5 database it is possible to
go from a UUID to, say, an email address.
Indeed, this is required for providing the service.
For example, 1Password would not be able to present members of a team the email address of
the person they are sharing an vault with without some mechanism to get from UUIDs to human oriented identifiers.

Direct access to the B5 data base is tightly restricted and monitored.
Limited indirect access exists for things like our billing systems, internal customer support systems, and the export to the data lake.

## The purpose of anonymizing identifiers

The datalake is designed to be used for research into the kinds of questions used above,
but we do not wish the data in datalake to be usable for working backwards to the identifiers in B5. There may be exceptional cases where working backwards that way is necessary,
the system we design should treat such things as exceptional.
Thus the goal here is to enable research into the kinds of questions listed above, while creating technical barriers to working backwards.

For the types of analyses we need, the anonymized identifiers in data lake should be

- Deterministically created from the B5 identifiers. That is the transformation process should be a function in that f(x) = y should always produce the same y each time it is given a particular x.
- One-to-one. That is distinct identifiers in B5 must map to distinct anonymized identifiers in datalake.

Those could be achieved by exporting the identifiers directly to the data lake,
but we also which to make it difficult to work backwards from what is in the data lake to information available in B5.
For example, billing information may include postal code.
If an authorized user of the data in the data lake also had access to, say, billing information, they would be able to connect data in the data lake to postal codes.

The system proposed here does not preclude analyses based on postal codes, but it would require that use of postal codes be explicitly approved.
Properly anonymizing IDs mean that those responsible for overseeing what data is used and how will have the visibility and control necessary to do their jobs.
Without anonymizing identifiers, we would have far fewer controls on how data is connected.

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

If nothing other than the process that performs the export from B5 to the data lake then is ever going to use the hash key, then a new hash key could be generated by that process each time the data lake is regenerated, and the secret hash key would not need to be persisted.
The generation process could create a key for generation and then throw that key away.

There are two reasons why we may wish to keep a tightly guarded copy of the hash keys.
If export from B5 is incremental instead of re-generated afresh,
we need the newly anonymized identifiers to remain consistent with previously anonymized identifiers that will remain in the data lake.

The second reason is that the users of data lake may reject the design if we do not provide some mechanism reverse identifier anonymization in case of some unanticipated need.
And so while throwing away the key provides the strongest guarantees,
I will sketch a hash key management proposal.

### A key per identifier field

There should be a separate key for each identifier.
This way, if a need emerges to be able to tie records in the data lake to, say, actual account IDs, the key for anonymizing account UUIDs can be made available for that specific purpose without exposing the key for other fields.

This does not prevent all potential leakages. For example, being able to de-anonymize member UUIDs in combination with access to our internal customer support and management systems would allow someone to use that system to go from member UUID to member email address.
However, the proposed mechanism raises some barriers against misuse of the information, and it best communicates what is allowed and what isn't.

### Key rotation

If someone has temporary access to a hash key and the list of identifiers from B5, they can create a mapping of IDs with their anonymized counter parts. They can store such a table on their own devices for later use.

We therefore should rotate the hash keys with a cadence that takes into account the cost of entirely regenerating all of the tables in the data lake which include an anonymized identifier.

### Don't hand out keys

When a request to make use of one of these hash keys is approved, the holders of the keys should perform the query or analysis that requested. Thus the key itself is not shared, and we reduce the threat of creation mapping tables between anonymized and B5 identifiers.

If it turns out that some set of keys or analyses are frequently approved, then the approach should be to design the data lake exports to accommodate those approved usages.
