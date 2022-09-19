# Noise addition

## Goals and background

One of our goals is to make de-anonymization more difficult.
The more difficult it is for the data we hold be to abused,
the more comfortable we can be with holding it.

The overall approach here is an alternative to an older, failed, approach to privacy thinking.
In the past, people would think about specified pieces of information as enabling de-anonymization and all other data as being safe. We called the former "Personal Identifying Information" (PII) and felt that removing the PII from a data set meant that the remaining data about an individual could not be used for de-anonymization. Or at least not be usable for de-anonymization at a level that anyone had to seriously worry about.

Around 2005, this understanding changed among academics and cryptographers.
Work lead by Cynthia Dwork then at Microsoft Research and colleagues showed how mathematically naive that approach was, but also provided a mathematical framework, Differential Privacy, for solutions addressing the problem.

As is not atypical, the initial interest was among academics, while the old approach of just worrying about the PII grew within industry.
But as is also not atypical, the following years were filled with "we told you so" examples of where relying on removing identifiers failed to prevent de-anonymization of sensitive information. The more or less textbook case is the Netflix rating de-anonymization from 2008.
It is far from the only case, but it is perhaps the easiest to explain to general audiences.

More recently entities with the mathematical know-how and need to worry about de-anonymization began implementing systems that gave a much higher degree of de-anonymization resistance.
In 2016 Apple's keynote address at WWDC, Craig Federighi announced that iOS 10 would use Differential Privacy for some of its analytics. Among other things, that introduced the term to a broader community of software developers.

> Differential privacy is a research topic in the area of statistics and data analytics that uses hashing, sub-sampling and noise injection to enable this kind of crowdsourced learning while keeping the information of each individual user completely private

That is not really a great description, but that is how the term was introduced to a large number of people.

In addition to Apple, other entities adopting (so some degree or another) Differential Privacy techniques have been the US Census Bureau, Facebook, Google, surveys used for College Report Cards, and others.

It has been growing in use, both for data that organizations make public; but it is also used for internal controls of data. It is often used to enable data analysts to do their job while preventing those same analysts from acquiring enough information to de-anonymize records.

## It's all about balance

The techniques break away from an all-or-nothing approach to data collection, storage, and analysis. Instead of making a binary PII/not-PII decision, we recognize that everything is potentially identifying and so the idea is to balance privacy guarantees against utility of the data in a more fluid way.

We will find in what follows that technical difficulty of implementation, privacy protections, and data utility can all be managed without having to take an all-or-nothing approach. Absolutist approaches of "we can't tolerate any noise in the data" or "we can't hold onto anything that could ever be used to de-anonymize" both lead to not doing anything (noise always exists, and any data can potentially be used to de-anonymize.)

## De-anonymization resistence

For at least this document, I will talk about de-anonymization resistance and de-anonymization resistant. I will use DAR for both, as it should be clear which is meant in each usage.

There are broadly two ways to achieve DAR.

- Data minimization
- Noise addition

The less data we hold or make available (internally or externally) the harder it is to de-anonymize that data. For the data we do collect and hold, the noisier the data, the harder it is to de-anonymize. In the abstract data minimization is an instance of noise addition with extreme quantifies of noise.

Differential privacy is, very roughly speaking, a mathematical framework for assigning noise to stay within an (abstract) privacy budget, but leaving that math aside, we start out with a higher level view and do not need to frame this discussion specifically in Differential Privacy terms.

A great advantage to noise addition to those seeking to use and analyze the data is that it removes the "all or nothing" choice one might face in any decision about data collection. By substantially reducing the risk of de-anonymization, we may be willing to tolerate the collection, storage, or use of some data that we might otherwise have to reject entirely.

There are (roughly) three stages at which noise can be added.

1. Data collection
2. Data storage
3. Data analysis

## Consequences of noise

All data analysis involves some inferencing that results in
confidence intervals or error ranges or similar probabilistic interpretation the statistic in question.
I will refer to all such things as "confidence intervals" in what follows, even though for some analyses it may manifest in other forms.

All data analysis, whether we deliberately add noise or not, has these confidence intervals. We always must tolerate some uncertainty in any data analysis. In some naive presentations of data analysis the uncertainty is not explicitly expressed, but that is an omission from analysis.
There is always uncertainty. Deliberately adding noise makes the need for expressing confidence intervals more explicit, while in fact the confidence intervals should always be computed and should always be reported if not negligible.

If you can't tolerate any noise then you can't do any data analyses in the first place.

## At data collection

Noise can be added client-side. This offers the strongest guarantees for the user,
as it can add the highest degree of transparency to the user
and provides safety to the user against data interception, breach, or misuse of the data sent from the client. Of all three locations it does the most to keep us honest.

It is, however, the most difficult to implement and plan around. Hard-coding the noise parameters into the client would make adjustments and tuning practically impossible.
I have sketched a scheme elsewhere[^181] that would allow clients to have a hardcoded minimum amount of noise to add, but otherwise specific parameters for specific cases could be sent from the server.
But even with such a scheme, this still remains the most difficult.

[^181]: The document with that sketch needs to be cleaned up before being shared more publicly.

## At data storage

While we might receive data from clients that is not DAR, we can add the noise as we store the data. In this way, we would not be holding on to non-DAR data.

This would protect users from the consequences of data breach or misuse of the stored data.
Furthermore, it allows us to take a more holistic approach to the noise addition, as we can adjust the noise addition in light of the totality of the data.
## At usage time

The biggest advantage to adding noise at usage time is that we can tune the amount of noise precisely to the query or analysis being sought. Noise added prior to this point cannot be tuned to specific analyses and so it would be much harder to judge how much noise is both necessary to reach a desired level of DAR and how that noise will affect the confidence in the inferencing from the data analysis.

The tools available to us to add noise are most mature at this stage. This may change over time, but this practicality cannot be ignored.

## Noise at multiple stages

It is possible, even expected, that noise be added at multiple stages. If the noise addition at each stage is done within a differential privacy framework, then we know how all of the noise additions add up, both in terms of how much it widens the resulting confidence interval and how DAR the final report is.

A system that is designed to allow for all three mechanisms will give us the most flexible toolset for judging any individual case. In cases where the data sensitivity is high and the noise tolerance in analysis is also high, we could add most of the noise client side.
