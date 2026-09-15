"""Verify the generated bundle; optionally compare schemas with the deployed canonical service.

No credentials, tool calls, quota consumption or writes. Exit 1 means confirmed drift;
exit 2 means a remote check could not be completed. Regenerate in the product repository.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REMOTE_CONTRACTS = {
    "contracts/scoutee-integrations.json": "https://scoutee.org/.well-known/scoutee-integrations.json",
    "contracts/scoutee-openapi.json": "https://scoutee.org/.well-known/scoutee-openapi.json",
}
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def bundle_errors(root: Path) -> list[str]:
    manifest = json.loads((root / "CONTRACT-SOURCE.json").read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        return ["CONTRACT-SOURCE.json: missing file hashes"]
    errors = [
        f"{name}: missing from manifest"
        for name in REMOTE_CONTRACTS
        if name not in files
    ]
    for name, expected in files.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or str(relative) != name:
            errors.append(f"{name}: invalid bundle path")
            continue
        path = root / relative
        if any(
            part.is_symlink() for part in (path, *path.parents) if root in part.parents
        ):
            errors.append(f"{name}: symlinks are not generated artifacts")
        elif not isinstance(expected, str) or not re.fullmatch(
            r"[0-9a-f]{64}", expected
        ):
            errors.append(f"{name}: invalid SHA-256")
        elif not path.is_file():
            errors.append(f"{name}: missing generated file")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"{name}: generated content differs from its source hash")
    return errors


def changed_paths(local: object, deployed: object, path: str = "") -> list[str]:
    """Report JSON locations, never response bodies or account data. Ignore object key order."""
    if isinstance(local, dict) and isinstance(deployed, dict):
        changes = []
        for key in sorted(local.keys() | deployed.keys()):
            child = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in local or key not in deployed:
                changes.append(child)
            else:
                changes.extend(changed_paths(local[key], deployed[key], child))
            if len(changes) >= 20:
                break
        return changes[:20]
    return [] if local == deployed else [path or "/"]


def fetch_contract(url: str) -> object:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "User-Agent": "ScouteeContractChecker/1.0 (+https://github.com/qchantel/scoutee-mcp)",
        },
    )
    with urlopen(request, timeout=20) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("response exceeds the contract size limit")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise TypeError("response is not a JSON contract object")
    return data


def check(root: Path, *, live: bool = False, fetch=fetch_contract) -> dict:
    try:
        errors = bundle_errors(root)
    except (OSError, ValueError, TypeError) as exc:
        errors = [f"Cannot validate the local bundle: {type(exc).__name__}"]
    report = {
        "status": "drift" if errors else "passed",
        "bundle_errors": errors,
        "remote": [],
    }
    if not live or errors:
        return report
    for name, url in REMOTE_CONTRACTS.items():
        item = {"file": name, "url": url}
        try:
            local = json.loads((root / name).read_text(encoding="utf-8"))
            differences = changed_paths(local, fetch(url))
            item.update(
                status="drift" if differences else "passed", changed_paths=differences
            )
        except (OSError, ValueError, TypeError, URLError) as exc:
            item.update(status="unavailable", error=type(exc).__name__)
            if isinstance(exc, HTTPError):
                item["http_status"] = exc.code
                exc.close()
        report["remote"].append(item)
    statuses = {item["status"] for item in report["remote"]}
    if "drift" in statuses:
        report["status"] = "drift"
    elif "unavailable" in statuses:
        report["status"] = "unavailable"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Read the two public canonical schemas"
    )
    args = parser.parse_args()
    report = check(ROOT, live=args.live)
    print(json.dumps(report, indent=2))
    return {"passed": 0, "drift": 1, "unavailable": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
