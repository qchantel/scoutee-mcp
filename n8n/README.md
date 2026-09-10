# Scoutee → n8n

Import `scoutee-tender-watch.json`. The workflow is inactive and ends at an explicit destination setup
step. No customer data is sent anywhere until you replace that step with your chosen destination.

1. Create an **HTTP Header Auth** credential named as you prefer: header `X-API-Key`, value your Scoutee
   workspace key. Select it on **Fetch window**. Keys require a paid workspace. OAuth tokens also work
   in an Authorization header, but unattended refresh must be managed by your credential provider.
2. Configure countries/keywords on **Fetch window**. Start with a narrow window. The generated workflow
   freezes `seen_before`, pages through the same search and refuses a capped or inconsistent result set.
3. Replace **Configure destination** with destination nodes that upsert every notice by its canonical
   `id`, preserving nullable deadlines/estimates and each notice's currency. Only after every write is
   acknowledged, return the batch with `delivery_confirmed: true` and connect to **Commit checkpoint**.
   Partial success must fail the run; the next run may repeat already delivered IDs.
4. Test manually. Then replace the manual trigger with your schedule, set workflow concurrency to one,
   and activate it. n8n saves workflow static data on successful active executions; manual tests do not
   persist the cursor. Export a copy of the workflow whenever its filters change and start a fresh cursor.

The first active run covers the previous 24 hours. A five-minute overlap and two-minute ingestion delay
reduce late-arrival gaps. This is an at-least-once discovery feed, not a change/deletion feed: notices
merged or edited after discovery require a separate reconciliation if your destination needs that.
Server transactions that commit very late can exceed the overlap; adapt it to your ingestion SLA.

For EU procurement, you can add optional `cpv` query parameters on **Fetch window**, such as
`cpv=90911200-8`. Get codes for your business free in [Scoutee's AI CPV finder](https://scoutee.org/en/find-my-cpv):
after sign-in, AI combines your company details with Scoutee's knowledge base. Review the suggestions,
or browse the [official catalogue](https://scoutee.org/en/cpv), before adding them. A code matches its
official descendants and combines with keywords using OR; country, value and date filters still apply.
CPV is the common EU procurement standard; it does not replace US or Canadian classifications. Export
the changed workflow and start a fresh cursor when changing these filters, as for keywords.

An HTTP 429 stops the run before checkpointing. Honour the response's `Retry-After` before retrying;
401/403 require credential, membership or plan repair. The template spaces pages by 6.1 seconds and
makes no automatic immediate retries. Very large windows must be split rather than repeatedly retried.
The terminal checkpoint node refuses to run without explicit delivery acknowledgement.

The product repository’s Python adapter (`src/scoutee/integration_polling.py`) implements the same fixed-window contract for
other platforms. Its caller owns scheduling, the credential store, destination upserts and durable
checkpoint commits. No API key, token or customer destination belongs in the versioned catalogue.
