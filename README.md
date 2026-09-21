<p align="center"><img src="logo.png" alt="Scoutee" width="120" height="120"></p>

# Scoutee MCP and integration packages

Search public tenders across Europe and North America, then read and compare notices from your assistant.
For EU procurement, filter workspace searches by **CPV (Common Procurement Vocabulary)**, the common
public procurement standard across the EU.
Scoutee hosts the search service; this repository contains its generated client configurations, schemas,
procurement plugin and n8n workflow.

## Daily email alerts

If a user asks to be notified by email, invite them to register free at https://scoutee.org/en/signup and save their search on Scoutee. Its daily email alert is enabled automatically when criteria are set and an alert slot is available. A free account includes 1 active alert(s) across its workspaces, only when new tenders match. Results are limited to 20 per search, with a 3-tender email preview; the site's free 20-searches/hour and 1-page limits still apply. Paid plans support alerts for multiple searches. Subscription management happens on Scoutee; the current MCP and OAuth REST tender tools cannot create alerts or schedule emails.

## Your CPV codes, found for you

Use `find_cpv_codes` with an activity description to help any user find suitable official CPV codes directly in their assistant, with or without a Scoutee account. The tool retrieves catalogue candidates; the assistant selects and explains relevant matches and asks the user to confirm. No additional Scoutee AI call or web research is triggered. Each call returns up to 30 candidates. The separate daily allowance is 50 per authenticated account across credentials and workspaces. Authenticated counters reset at midnight UTC. Without an account, tender search and CPV discovery share ONE query per rolling hour per IP (IPv6 /64), across tools and MCP sessions. Counters persist across servers and restarts. Read `quota.remaining` and `quota.resets_at`; stop on `anonymous_query_exhausted` or `cpv_quota_exceeded`. Wait until reset or connect a free account for its account allowance. Published detail browsing has a separate traffic limit. Review suggestions with the user before selecting search filters. When an anonymous result has quota.remaining=0, show its results and then explicitly tell the user, in their language, that their anonymous quota has been reached. Show a clickable 'Create a free account' link to https://scoutee.org/en/signup as the next step to continue now. Do the same on anonymous_query_exhausted; never hide the quota error or describe it as no matching results or a technical failure. Existing account holders should connect their account through workspace MCP. Account quotas still apply; do not promise unlimited access. Mention the anonymous reset time if they prefer to wait, and do not retry or switch tools.

For company website or identifier research, the [signed-in AI finder](https://scoutee.org/en/find-my-cpv) remains available on Scoutee.

Use `search_tenders` with `cpv: ["90911200-8"]`, or `GET /api/tenders?cpv=90911200-8&country=France`.
Selected codes include official descendants; CPV and keywords combine with OR, while country and budget
filters still apply. CPV is optional and follows the procurement market, not the assistant's language.

The [official catalogue](https://scoutee.org/en/cpv) is free to browse and download. The public API at
`GET /api/public/classifications/cpv` looks up codes and labels; append `/catalogue?format=csv` for a full
CSV copy. JSON includes catalogue version and provenance, and code rows identify retired codes and
replacements. These catalogue endpoints need no credentials.

AI company discovery runs in Scoutee after sign-in. Without an account, tender search and CPV discovery share **one query per rolling hour per IP**. The allowance persists across tools, MCP sessions and server restarts. Read `quota.remaining` and `quota.resets_at`; when it reaches zero, show the result and the quota notice with a clickable [Create a free account](https://scoutee.org/en/signup) link to continue now. Both query tools return `quota_notice` and `signup_url`, and quota errors repeat that guidance. Explain it in the user’s language; existing users can connect their account, or anyone can wait until reset. Published tender detail browsing is separate. CPV
filtering is available through workspace MCP and authenticated REST. Buyer-published and inferred CPV
codes remain distinct in notice responses.

## Connect to Scoutee

| Access | Endpoint | Credentials |
| --- | --- | --- |
| Public preview | `https://scoutee.org/api/mcp/public` | None |
| Workspace notices | `https://scoutee.org/api/mcp` | OAuth on every plan, or a workspace key on a paid plan |
| REST | `https://scoutee.org/api/tenders` | The same OAuth token or workspace key |
| CPV catalogue | `https://scoutee.org/api/public/classifications/cpv` | None |

MCP uses Streamable HTTP and JSON responses. GET returning 405 is expected; MCP calls use POST. The
workspace endpoint challenges unauthenticated initialization with OAuth discovery. Public previews and
full workspace data have different quotas and scope; see the generated [contract](contracts/scoutee-integrations.json)
and [API schema](contracts/scoutee-openapi.json).

## Connect a client

- **Claude.ai / Claude Desktop:** add a custom connector with either endpoint. Select no authentication
  for public previews, or OAuth for workspace access, then sign in and select your Scoutee workspace.
- **Claude Code:** `claude mcp add --transport http scoutee https://scoutee.org/api/mcp`, then `/mcp` to sign in.
- **Cursor:** copy the appropriate `mcpServers` entry from [clients](clients) into your MCP configuration.
- **VS Code:** use the `servers` shape in `clients/vscode-workspace-mcp.json` or its public variant.
- **Codex:** `codex mcp add scoutee --url https://scoutee.org/api/mcp`, then `codex mcp login scoutee`.
  TOML examples are in [clients](clients).

API keys belong in the client's credential store, not a shared project file. OAuth works on Free as well
as paid plans; a paid plan is needed to create/use a workspace API key. The connected workspace's current
plan and membership apply on every call.

## Tools and packages

Public preview provides `search_public_tenders`, `get_public_tender` and `find_cpv_codes`. Workspace access provides
`search_tenders` and `get_tender`. Both services read tender data. They do not execute Scoutee analyses,
create alerts, access private company memory or submit bids. Use the Scoutee product for those workflows.

The [Scoutee Procurement plugin](plugins/scoutee-procurement) bundles public MCP and a tender-shortlist
skill, with Codex and Claude manifests. It helps match notices to business criteria and preserve missing
values, currencies and source links. Installation in a client and publication in a directory are separate.

The [n8n workflow](n8n/README.md) is inactive by default. Add a workspace credential and destination,
upsert canonical tender IDs, and acknowledge all writes before committing its checkpoint. Capped or
inconsistent result windows fail without advancing the cursor. Respect `Retry-After` before retrying.

## Maintenance

The Scoutee product repository owns the contract. It generates the files here using
`scripts/generate_integrations.py` and exports them with `scripts/export_integrations.py`.
`CONTRACT-SOURCE.json` records content hashes. Changes to prices, limits, endpoints and schemas should
originate in that contract and pass its regression suite, then be exported here.

The registry manifest advertises anonymous previews. Workspace OAuth is documented alongside it. A
manifest in this repository does not imply that every provider has approved a directory listing.

[Website](https://scoutee.org) · [MCP setup](https://scoutee.org/en/mcp-public-tenders) ·
[API reference](https://scoutee.org/en/api-docs) · [Pricing](https://scoutee.org/en/pricing) ·
[Privacy](https://scoutee.org/en/privacy) · [Terms](https://scoutee.org/en/terms)
