# Maintaining the connector bundle

The Scoutee product repository owns generated files, including README.md and the contracts.
After its normal release, run `scripts/generate_integrations.py --check` there, then
`scripts/export_integrations.py --target /path/to/scoutee-mcp`. Review and merge the exported diff;
do not repair drift by editing plan rules or hashes in this repository.

`python3 scripts/check_contract.py` verifies the generated bundle against `CONTRACT-SOURCE.json`.
`python3 scripts/check_contract.py --live` also compares both exported schemas with the public
canonical schemas served by Scoutee. It makes two GET requests, uses no credentials or MCP tools,
and consumes no search or CPV allowance. Confirmed drift exits with 1; unavailable remote checks
exit with 2 and retain any independently confirmed differences. Output identifies JSON paths.

The Connector contract workflow runs offline checks for pull requests and also checks deployed
freshness after main pushes, daily, or on manual dispatch. This detects product changes that land
without a corresponding export. A red remote check requires investigation, not a new provider
submission. Reviewed ChatGPT and Claude snapshots and actual installation acceptance remain
separate records in the [Scoutee backoffice](https://backoffice.scoutee.org/connectors).

Run the checker regressions with `python3 -m unittest discover -s tests -v`.
