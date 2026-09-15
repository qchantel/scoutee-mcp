"""Guard real maintenance failures without contacting Scoutee during pull request checks."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

from scripts.check_contract import REMOTE_CONTRACTS, check


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.schemas = {
            "contracts/scoutee-integrations.json": {
                "product": {"cpv": {"anonymous": 20}}
            },
            "contracts/scoutee-openapi.json": {
                "paths": {"/tenders": {"security": ["OAuth"]}}
            },
        }
        hashes = {}
        for name, data in self.schemas.items():
            path = self.root / name
            path.parent.mkdir(exist_ok=True, parents=True)
            body = json.dumps(data).encode()
            path.write_bytes(body)
            hashes[name] = hashlib.sha256(body).hexdigest()
        (self.root / "CONTRACT-SOURCE.json").write_text(json.dumps({"files": hashes}))

    def fetch(self, url):
        return self.schemas[
            next(name for name, expected in REMOTE_CONTRACTS.items() if url == expected)
        ]

    def test_matching_bundle_and_deployed_contracts_pass(self):
        result = check(self.root, live=True, fetch=self.fetch)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(len(result["remote"]), 2)

    def test_hand_edit_fails_offline_without_making_requests(self):
        (self.root / "contracts/scoutee-integrations.json").write_text("{}")

        def forbidden_fetch(url):
            self.fail("A broken local bundle must fail before any network check")

        result = check(self.root, live=True, fetch=forbidden_fetch)
        self.assertEqual(result["status"], "drift")
        self.assertEqual(result["remote"], [])

    def test_missing_file_and_path_escape_fail(self):
        (self.root / "contracts/scoutee-openapi.json").unlink()
        path = self.root / "CONTRACT-SOURCE.json"
        manifest = json.loads(path.read_text())
        manifest["files"]["../outside"] = "0" * 64
        path.write_text(json.dumps(manifest))
        result = check(self.root)
        self.assertEqual(result["status"], "drift")
        self.assertTrue(
            any("invalid bundle path" in error for error in result["bundle_errors"])
        )
        self.assertTrue(
            any("missing generated file" in error for error in result["bundle_errors"])
        )

    def test_deployment_change_reports_paths_even_if_local_hashes_are_valid(self):
        self.schemas["contracts/scoutee-integrations.json"]["product"]["cpv"][
            "anonymous"
        ] = 10
        result = check(self.root, live=True, fetch=self.fetch)
        self.assertEqual(result["status"], "drift")
        self.assertEqual(
            result["remote"][0]["changed_paths"], ["/product/cpv/anonymous"]
        )

    def test_symlink_cannot_replace_a_generated_file(self):
        path = self.root / "contracts/scoutee-openapi.json"
        body = path.read_bytes()
        path.unlink()
        target = self.root / "elsewhere.json"
        target.write_bytes(body)
        path.symlink_to(target)
        result = check(self.root)
        self.assertEqual(result["status"], "drift")
        self.assertTrue(any("symlinks" in error for error in result["bundle_errors"]))

    def test_malformed_remote_response_is_unavailable(self):
        def malformed(url):
            raise ValueError("not JSON")

        result = check(self.root, live=True, fetch=malformed)
        self.assertEqual(result["status"], "unavailable")

    def test_unavailable_provider_is_not_reported_as_contract_drift(self):
        def unavailable(url):
            raise HTTPError(url, 503, "Unavailable", {}, None)

        result = check(self.root, live=True, fetch=unavailable)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(len(result["remote"]), 2)

    def test_failed_second_fetch_cannot_hide_confirmed_drift(self):
        def mixed(url):
            if url == REMOTE_CONTRACTS["contracts/scoutee-openapi.json"]:
                raise TimeoutError()
            return {"product": {"cpv": {"anonymous": 10}}}

        result = check(self.root, live=True, fetch=mixed)
        self.assertEqual(result["status"], "drift")
        self.assertEqual(result["remote"][1]["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
