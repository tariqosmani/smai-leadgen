# Infrastructure - Smart AI Workspace

Cold-email sending infrastructure for `smart-ai-workspace`. Normally stood up by `/inbox-setup`.
This file was created by hand on 2026-09-10 to record the **interim setup** in use before a
formal `/inbox-setup` run, so `/deliverability-monitor` has something to check.

## Current setup (interim, pre-/inbox-setup)

- **Dedicated sending domains:** none. Cold email currently goes out on the **primary domain**
  `smartaiworkspace.tech`. The playbook advises against this for volume cold-sending
  (`.claude/skills/inbox-setup/references/deliverability.md` > Sizing rules: "Keep the primary
  domain out of cold sending, always"). Acceptable at demo scale; `/inbox-setup` is the fix for
  a real client.
- **Mailbox:** `info@smartaiworkspace.tech`, 1 mailbox.
- **Outbound path:** connected account is the founder's consumer Gmail account, with
  `info@smartaiworkspace.tech` added as a "Send mail as" alias. Gmail Settings > Accounts shows
  the alias configured as **"Mail is sent through: smtp.hostinger.com"** (port 465, SSL) - i.e.
  Gmail relays mail from this alias through Hostinger's SMTP, not straight out through Google.
  The `Received: ... by gmailapi.google.com with HTTPREST` line on sent copies only records API
  ingestion (the MCP / autonomous send); Gmail then hands the message to the Hostinger relay.
- **Domain DNS (Hostinger nameservers):**
  - MX: `5 mx1.hostinger.com`, `10 mx2.hostinger.com` (Hostinger Mail)
  - SPF: `v=spf1 include:_spf.mail.hostinger.com include:_spf.reach.hostinger.com ~all` - one
    record, authorizes the Hostinger send path
  - DKIM: Hostinger selectors `hostingermail-a/b/c._domainkey` (present), plus `resend._domainkey`
  - DMARC: `v=DMARC1; p=none; rua=mailto:dmarc@smartaiworkspace.tech`
- **Warmup:** none. No Instantly / Smartlead warmup was run on this mailbox.
- **Inbound:** delivered to Hostinger Mail; the connected Gmail account POP-fetches it, so replies
  land in the Gmail inbox `/lead-replies` reads.

## Auth status - CONFIRMED PASS (2026-09-10)

A self-test (`info@smartaiworkspace.tech` -> a personal Gmail, sent via the same MCP/API path the
automation uses) was delivered and its `Authentication-Results` header read:

```
dkim=pass  header.i=@smartaiworkspace.tech  header.s=hostingermail-a
spf=pass   smtp.mailfrom=info@smartaiworkspace.tech  (client-ip 23.83.212.37)
dmarc=pass (p=NONE)  header.from=smartaiworkspace.tech
```

The `Received:` chain: MCP `send_message` -> `gmailapi.google.com` (API ingestion) -> relayed to
`smtp.hostinger.com` (ESMTPSA, authenticated sender info@smartaiworkspace.tech) ->
`de-fra-smtpout2.hostinger.io` / MailChannels -> recipient `mx.google.com`. So API sends **do**
route through the Hostinger relay, and are signed by `d=smartaiworkspace.tech` + SPF-authorized +
DMARC-aligned.

Standing cautions (not auth failures): cold volume is going out on the **primary domain** with
**no warmup**. Fine at demo scale; a real client gets `/inbox-setup` (dedicated warmed domains).

## Deliverability checks

- 2026-09-10 (since 2026-09-03): sent 23 (23 first-touch / 0 follow-up), bounce 0.0% (0/23), complaints n/t, reply rate 0% (0/23, first check no trend, most sends <=2 days old), auth PASS - CONFIRMED by self-test Authentication-Results (spf=pass dkim=pass dmarc=pass, d=smartaiworkspace.tech, via smtp.hostinger.com relay), DMARC policy p=none, blocklist clean (Spamhaus DBL/ZEN, SURBL, SpamCop, Barracuda). verdict GREEN. Standing note (not a verdict driver): cold volume is on the primary domain with no warmup - run /inbox-setup for dedicated warmed domains before scaling for a paying client. Correction: an earlier draft of this line read RED on a misread of the `gmailapi.google.com` header (the alias's Hostinger SMTP relay was not accounted for), briefly YELLOW pending confirmation, now GREEN on the confirmed header.
