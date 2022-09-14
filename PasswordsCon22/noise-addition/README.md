# Noise addition

One of our goals is to make de-anonymization more difficult,
there are broadly two approaches:

- Data minimization
- Noise addition

The less data we hold or make available (internally or externally) the harder it is to de-anonymize that data. For the data we do collect and hold, the noisier the data, the harder it is to de-anonymize.

Differential privacy is, very roughly speaking, a mathematical framework assigning noise to stay within an (abstract) privacy budget, but leaving that math aside, we start out with a higher level view and do not need to frame this discussion specifically in Differential Privacy terms.

A great advantage to noise addition to those seeking to use and analyze the data is that it removes the "all or nothing" choice one might face in any decision about data collection. By substantially reducing the risk of de-anonymization, we may be willing to tolerate the collection, storage, or use of some data that we might otherwise have to reject entirely.


There are (roughly) three stages at which noise can be added.

1. Data collection
2. Data storage
3. Data analysis

## At data collection

Noise can be added client-side. This offers the strongest guarantees for the user,
as it can add the highest degree of transparency to the user
and provides safety to the user against data interception, breach, or misuse of the data sent from the client. Of all three locations it does the most to keep us honest.

It is, however, the most difficult to implement and plan around. Hard-coding the noise parameters into the client would make adjustments and tuning practically impossible.
I have sketched a scheme elsewhere[^181] that would allow clients to have a hardcoded minimum amount of noise to add, but otherwise specific parameters for specific cases could be sent from the server.
But even with such a scheme, this still remains the most difficult ...

[^181]: The document with that sketch needs to be cleaned up before being shared more publicly.
