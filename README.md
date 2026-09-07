<p align="center">
  <img src="logo.png" alt="Scoutee" width="120" height="120">
</p>

<h1 align="center">Scoutee MCP server</h1>

<p align="center">
  Search public tenders across Europe and North America from any MCP client.
</p>

<p align="center">
  <a href="https://scoutee.org">scoutee.org</a> ·
  <a href="https://scoutee.org/en/api-docs">API reference</a> ·
  <a href="https://scoutee.org/pricing">Pricing</a>
</p>

---

## What Scoutee is

Scoutee is a public procurement monitoring service. Every day it collects the tenders published by
official journals and buyer platforms across Europe (TED and the national portals of 30 countries)
and North America (SAM.gov, CanadaBuys, SEAO), deduplicates them into one row per notice, and stores
them in a single searchable database — **200,000+ notices, 87 sources, 32 countries**.

This repository is the **documentation** for Scoutee's hosted MCP server. It contains no product
code: the server is hosted by Scoutee and you connect to it over HTTPS.

| | |
|---|---|
| **Endpoint** | `https://scoutee.org/api/mcp` |
| **Transport** | Streamable HTTP (stateless, JSON responses). No SSE, no stdio package. |
| **Auth** | `X-API-Key: sct_...` header (`Authorization: Bearer sct_...` is also accepted) |
| **Tools** | `search_tenders`, `get_tender` — both read-only |
| **Quota** | 10,000 searches per hour per key |
| **Docs** | https://scoutee.org/en/api-docs |

## Getting an API key

1. Create an account at [scoutee.org](https://scoutee.org).
2. Subscribe to the **Standard** plan ([pricing](https://scoutee.org/pricing)) — the API and the MCP
   server require a paid workspace.
3. Open your workspace page, section **API**, and create a key. It looks like `sct_...`.
4. Keys can be revoked at any time from the same page.

## Setup

### Claude Code

```bash
claude mcp add --transport http scoutee https://scoutee.org/api/mcp \
  --header "X-API-Key: sct_your_key_here"
```

### Claude Desktop, Cursor, VS Code, Windsurf

Add this block to the MCP config file of your client (`claude_desktop_config.json`,
`.cursor/mcp.json`, `.vscode/mcp.json`, `~/.codeium/windsurf/mcp_config.json`). It is also in
[`mcp-config.json`](mcp-config.json) in this repo.

```json
{
  "mcpServers": {
    "scoutee": {
      "type": "http",
      "url": "https://scoutee.org/api/mcp",
      "headers": {
        "X-API-Key": "sct_your_key_here"
      }
    }
  }
}
```

VS Code's `mcp.json` uses `servers` instead of `mcpServers`, and supports an input prompt for the key:

```json
{
  "inputs": [
    { "id": "scoutee-key", "type": "promptString", "description": "Scoutee API key", "password": true }
  ],
  "servers": {
    "scoutee": {
      "type": "http",
      "url": "https://scoutee.org/api/mcp",
      "headers": { "X-API-Key": "${input:scoutee-key}" }
    }
  }
}
```

### Python

```python
import asyncio, os
import httpx
from mcp.client import Client
from mcp.client.streamable_http import streamable_http_client

async def main():
    headers = {"X-API-Key": os.environ["SCOUTEE_API_KEY"]}
    async with httpx.AsyncClient(headers=headers, timeout=60) as http:
        async with Client(
            streamable_http_client("https://scoutee.org/api/mcp", http_client=http)
        ) as client:
            result = await client.call_tool(
                "search_tenders",
                {"q": "road maintenance", "country": ["France", "Belgium"], "page_size": 5},
            )
            print(result)

asyncio.run(main())
```

### curl (raw JSON-RPC, useful to check a key)

```bash
curl -s https://scoutee.org/api/mcp \
  -H "X-API-Key: $SCOUTEE_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Tools

### `search_tenders` — Search public tenders

Search Scoutee's index of public procurement notices. Returns a page of notices, the total number of
matches, a per-country breakdown of the same match set (`by_country`, useful to suggest where else to
look) and what the caller's hourly quota has left. Open notices only and newest first unless asked
otherwise; notices published on several portals appear once, the other portals listed in `also_on`.
**Each search consumes one quota unit.** Read-only.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | `string` (≤200) | — | Free text over title, buyer and description. Every word must match the *start* of a word in the notice (`nettoy` finds `nettoyage`); a substring inside a word does not match. Accent- and case-insensitive. |
| `keyword` | `string[]` | — | Keywords matched as whole words (plural tolerated) in title, buyer or description, plus the cached translations of each keyword on the portals of that language — the way to search across countries without translating anything yourself. Several keywords widen the search (a notice matching any of them is returned). |
| `country` | `string[]` | — | Countries of the publishing portal, by their English name as Scoutee stores it (`France`, `Belgium`, `Germany`; `Europe` for TED). Several countries add up. Omit to search everywhere — the `by_country` map of any result lists the exact values in use. |
| `source_id` | `integer` | — | Restrict to a single portal, by its Scoutee source identifier. |
| `min_value` | `number` | — | Minimum estimated value, in the currency of the notice. Notices without a published value are excluded when this is set. |
| `max_value` | `number` | — | Maximum estimated value. |
| `sort` | `"newest" \| "oldest" \| "deadline"` | `newest` | `newest` (publication descending), `oldest` (publication ascending) or `deadline` (soonest submission deadline first). |
| `include_closed` | `boolean` | `false` | Include notices whose consultation is already closed. |
| `seen_after` | `string` (ISO 8601 date-time) | — | Keep only notices first collected by Scoutee after this instant. The way to poll for what is new since a previous run. |
| `page` | `integer` ≥1 | `1` | 1-based page number. |
| `page_size` | `integer` 1–200 | `20` | Notices per page (capped by the plan). Kept modest by default because a notice is a large object; raise it when you need to sweep a whole result set. |

Example result:

```json
{
  "items": [
    {
      "id": 398005,
      "source_id": 12,
      "source_name": "BOAMP",
      "source_country": "France",
      "external_id": "26-118742",
      "title": "Entretien des espaces verts de la commune",
      "buyer": "Ville de Rennes",
      "description": "Marché de services d'entretien des espaces verts ...",
      "url": "https://www.boamp.fr/pages/avis/?q=idweb:26-118742",
      "location": "Rennes, Ille-et-Vilaine",
      "procedure": "Procédure adaptée",
      "cpv_codes": ["77310000", "77311000"],
      "estimated_value": 450000.0,
      "currency": "EUR",
      "published_at": "2026-09-02T08:00:00Z",
      "deadline_at": "2026-10-15T12:00:00Z",
      "first_seen_at": "2026-09-02T09:12:44Z",
      "last_seen_at": "2026-09-07T04:10:03Z",
      "closed_at": null,
      "favorite": false,
      "also_on": [{ "source_id": 1, "source_name": "TED", "url": "https://ted.europa.eu/..." }],
      "documents_url": "https://www.boamp.fr/dce/..."
    }
  ],
  "total": 137,
  "page": 1,
  "page_size": 20,
  "pages": 7,
  "by_country": { "France": 98, "Belgium": 21, "Europe": 18 },
  "quota_plan": "standard",
  "quota_limit": 10000,
  "quota_remaining": 9987
}
```

### `get_tender` — Read one public tender

One notice in full, by its Scoutee identifier (the `id` of a search result). Same shape as a search
result item. **Consumes no quota.** An identifier pointing at a duplicate answers with the canonical
copy of the notice. Read-only.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `tender_id` | `integer` | yes | Scoutee identifier of the notice. |

Returns a single tender object, identical in shape to one entry of `items` above.

## Example prompts

- "Find open tenders about road maintenance in France and Belgium with a deadline after next month."
- "List the newest IT consulting RFPs above 500,000 EUR in Germany."
- "Show me the details of tender 398005 and summarise the buyer's requirements."
- "What has been published in the Netherlands since yesterday about cloud hosting?"

## Quotas and errors

- **10,000 searches per hour per key.** Every `search_tenders` result carries `quota_plan`,
  `quota_limit` and `quota_remaining`; `get_tender` does not consume quota.
- Exceeding the quota returns a tool error with the same message the REST API would return (HTTP 429).
- A missing, unknown or revoked key returns a tool error asking for `X-API-Key`.
- Notices are returned in the language they were published in; nothing is translated. `url` always
  points at the notice on its source portal, which is where a bid is actually filed.

## Registry

This server is published to the official MCP Registry as `org.scoutee/scoutee`. The manifest is
[`server.json`](server.json).

## Links

- Website — https://scoutee.org
- Developer reference (REST + MCP) — https://scoutee.org/en/api-docs (French:
  https://scoutee.org/fr/documentation-api)
- Pricing — https://scoutee.org/pricing
- Contact — contact@scoutee.org

## License

The contents of this documentation repository are MIT licensed (see [LICENSE](LICENSE)). The Scoutee
service itself is a commercial product operated by AUTEUR (France) and is not open source.
