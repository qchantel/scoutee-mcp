<p align="center"><img src="logo.png" alt="Scoutee" width="120" height="120"></p>

# Scoutee MCP and integration packages

Search public tenders across Europe and North America, then read and compare notices from your assistant.
For EU procurement, filter workspace searches by **CPV (Common Procurement Vocabulary)**, the common
public procurement standard across the EU.
Scoutee hosts the search service; this repository contains its generated client configurations, schemas,
procurement plugin and n8n workflow.

## One free email alert after registration

[Register for free](https://scoutee.org/en/signup), save your search on Scoutee and enable its daily
email alert. Your free account includes **one active search alert across your workspaces**, only when
new tenders match, with **up to 20 results per search**. The email previews three tenders; opening the
search on Scoutee keeps the free allowance of two searches per hour and one page of 20 results.
Paid plans support alerts for multiple searches. Manage subscriptions on Scoutee; MCP and the OAuth
REST tender tools search and read notices and cannot subscribe or schedule email for you.

## Your CPV codes, found for you

Sign in to Scoutee for free: our AI combines your company's activity with our knowledge base to find
relevant CPV codes automatically. Start with your company name or identifier, website, or activity
description in the [free AI CPV finder](https://scoutee.org/en/find-my-cpv). Review the suggestions, then
use them in workspace MCP or REST searches.

Use `search_tenders` with `cpv: ["90911200-8"]`, or `GET /api/tenders?cpv=90911200-8&country=France`.
Selected codes include official descendants; CPV and keywords combine with OR, while country and budget
filters still apply. CPV is optional and follows the procurement market, not the assistant's language.

The [official catalogue](https://scoutee.org/en/cpv) is free to browse and download. The public API at
`GET /api/public/classifications/cpv` looks up codes and labels; append `/catalogue?format=csv` for a full
CSV copy. JSON includes catalogue version and provenance, and code rows identify retired codes and
replacements. These catalogue endpoints need no credentials.

AI company discovery runs in Scoutee after sign-in. The anonymous MCP offers tender previews; CPV
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

Public preview provides `search_public_tenders` and `get_public_tender`. Workspace access provides
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
