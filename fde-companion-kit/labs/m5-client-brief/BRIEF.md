# Client brief: Tidewell Parcel Co.

*A fictional client, for practice. Any resemblance to a real company is accidental.*

## Who they are

Tidewell Parcel Co. is a regional parcel carrier. It delivers for about 300 online shops, around 40,000 parcels a week. A support team of six handles **exceptions**: parcels that arrive late, damaged, at the wrong address, or not at all.

## The problem, in their words

> "We get 600 to 900 exception tickets a week, by email and through the shops' portal. Every one needs the same steps: work out what happened, look up the order and its tracking, decide what to offer, and write back. Easy ones take five minutes, hard ones take twenty, and the queue is always two days behind. Shops complain, and some have started looking at other carriers.
>
> We tried a chatbot last year. It was impressive in the demo and then it promised a refund to someone who'd made up their order number. We switched it off after a week."
> — Head of Customer Operations

## What they've asked for

A tool their support team uses on each ticket. For each one it should:

1. **Classify** it: late, damaged, lost, wrong address, or other.
2. **Look up** the order in their system and use the tracking history to check the story.
3. **Propose a resolution** under their policy (below), with the reason.
4. **Draft a reply** to the shop, in a calm, plain tone, that the agent can edit and send.

The support agent stays in charge. The tool proposes; a person decides.

## Their policy

| Situation | What they offer |
|---|---|
| Late by 1–2 days | Apology. No refund. |
| Late by 3+ days | Refund of the shipping fee. |
| Damaged, with a photo | Refund of the item value, up to the declared value. |
| Lost (no scan for 5+ days) | Open a trace. Refund the declared value once the trace closes. |
| Wrong address, our mistake | Redeliver free. |
| Order not found | Ask for the tracking number. Never offer money. |

**Hard rule:** any refund **over $100**, and any ticket that threatens legal action or mentions injury, goes to a team lead for approval. The tool must never tell a shop it will get money that a person hasn't approved.

## What they'll judge you on

The Head of Customer Operations cares about three things: does it save her team time, is it right, and can it ever promise money it shouldn't. Before anything is built, you'll agree with her on **one number** to be judged on, for example "the proposed resolution matches what a team lead would choose on at least 9 of 10 test tickets".
