# Platform team -- weekly status (week 45)

**Date:** 04.11.2026  |  **Author:** Priya Raghunathan (Priya R.)  |  **Org:** Nordhavn Labs

## TL;DR

- Migration to the new Kubernetes cluster is *mostly* done. Two services left.
- Staging is flaky on Mondays, cause still unknown.
- Soren has the on-call rota until Friday; ping him on Slack (`@soren.l`) first, phone second.

## Done this week

1. Søren Lindqvist moved the billing worker to the new cluster (he writes his name "Soren" in tickets, so search both).
2. Yuki Tanaka-Whitfield fixed the cert renewal bug; GitHub PR #2231.
3. Chidi Okonkwo (aka "Chi") rotated the Amazon Web Services keys.
4. Dashboard now lives at https://status.nordhavn-labs.example/overview, backed by the box at 203.0.113.45 (internal: 10.20.4.17).

## In progress

- [ ] Move the notification service. Owner: Raj (full name Rajesh Raghunathan, no relation to me)
- [ ] Decommission the old VM. Blocked on finance sign-off.
- [x] Update runbook

## Risks

> The person who sits next to the printer on the third floor and handles all the vendor invoices is leaving in March, and nobody else knows the approval flow.

Also: the shared staging login is still `deploy-shared` / `Mango-Lantern-42`. Please do NOT paste it into tickets. I will rotate it after the freeze, around Nov 20th.

## Contacts

| Who | Email | Phone |
|-----|-------|-------|
| Priya | priya.raghunathan@nordhavn-labs.example | +45 31 55 01 27 |
| Søren | s.lindqvist@nordhavn-labs.example | +45 29 40 77 12 |
| Yuki | yuki.tw@nordhavn-labs.example | +81 90 5550 1234 |

## Next week

Freeze starts 2026-11-16. Retro on Wednesday at 14:00 CET. Office is at Havnegade 41, 3rd floor, 1058 Copenhagen K, Denmark -- bring your badge.

Thanks all. Questions in the channel or reply here.

-- P.
