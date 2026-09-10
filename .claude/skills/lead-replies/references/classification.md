# Inbound reply classification

Cues for `/lead-replies` Step 2. Claude classifies with judgment, these are the signals, not a keyword
matcher. One reply gets exactly one class. When two could fit, use the priority order at the bottom.

## The seven classes

### interested
- Asks a question about the work, the approach, price-later, timeline, or the portfolio.
- "Send more info", "share a deck", "what would this look like for us".
- Proposes a time, asks how to book, "let's set up a call", "grab 20 minutes".
- A plain "yes" / "sure" / "I'm open to a chat".
- Forwards themselves in from another address to keep the thread going.

Gist: what they want to know or do next.

### not-now
- Explicit future revisit: "circle back in Q1", "not this quarter", "after our migration", "ask me in
  the spring", "budget resets in July".
- There IS interest, only the timing is off. No future date and no interest means `not-interested`.

Gist: the revisit window in their words. Parse it to a date for `next_action_date`: a named quarter =
its first day, "next month" = today +30d, anything vague = today +90d.

### not-interested
- "Not a fit", "we handle this in-house", "we already have a vendor", "no thanks", "not interested".
- A hard no with no door left open and no demand to stop all contact.

Gist: the reason if given, else "polite no".

### unsubscribe
- "Unsubscribe", "remove me", "take me off your list", "opt out", "do not contact me", "stop emailing
  me".
- A demand to stop ALL contact (CAN-SPAM style), not just a no to this offer.
- "This is spam" / "I'll report this as spam": treat as unsubscribe.

Gist: "unsubscribe".
This is the only class that writes `clients/<client>/suppress.md`.

### auto-reply
- Subject or body: "Out of Office", "OOO", "Automatic reply", "auto-response", "away until <date>",
  "on leave", "parental leave".
- Autoresponder / ticket acknowledgement: "we received your message", "ticket #NNN opened".
- "<Name> no longer works here" / "has left the company" WITH NO replacement contact. (WITH a named
  replacement it is `referral`.)

Gist: "OOO until <date>" or "left company, no contact".
If the body names a return date further out than +7, use it for the retry; otherwise retry today +7.

### referral
- "You want <name>", "<name> handles this", "I've cc'd <name>", "reach out to <email>", "talk to our
  ops lead".
- The current contact redirects you to a specific, named other person.

Gist: "referred to <name> <email or title>".
Routes as `Replied` (a human takes it). Do not auto-create a lead for the new person, put them in the
gist and Next Action so Tariq adds them.

### bounce
- Sender is `mailer-daemon@`, `postmaster@`, or `Mail Delivery Subsystem`.
- Body: "Delivery has failed", "Address not found", "550", "mailbox full", "user unknown", "recipient
  rejected", "does not exist".
- A soft bounce ("temporarily deferred", "over quota, retrying") that has not become a hard failure:
  leave it, do not route, it may still deliver.

Gist: the failure reason, short: "550 mailbox not found", "domain does not exist".

## "Wants to book" (drives Step 4, the booking sub-flow)
Inside `interested`, the booking draft is prepared ONLY when the reply:
- proposes a specific time or day ("Thursday afternoon?", "does the 14th work"), OR
- asks how to schedule ("how do we set this up", "send me a link", "what does your calendar look
  like").

A plain "yes let's talk" with no time and no scheduling ask: route `interested`, no draft. The Next
Action tells Tariq to propose times himself.

## Priority when two classes fit
`unsubscribe` > `bounce` > `referral` > `auto-reply` > `not-interested` > `not-now` > `interested`

- "Remove me" plus "not a fit" is `unsubscribe`.
- A mailer-daemon wrapper around any content is `bounce`.
- An OOO that also says "but talk to Sam <sam@co.com>" is `referral`, because Sam is actionable.
