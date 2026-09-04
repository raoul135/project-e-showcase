import json
import os
import subprocess
import tempfile
import threading
import unittest
import uuid
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "tools" / "deploy_n8n_workflows.ps1"
POWERSHELL = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
API_KEY = "-".join(("mock", "test", "key", "not", "a", "real", "secret"))


def make_node(marker="source", credentials=None):
    value = {
        "parameters": {"marker": marker},
        "id": "node-start",
        "name": "Start",
        "type": "n8n-nodes-base.manualTrigger",
        "typeVersion": 1,
        "position": [0, 0],
    }
    if credentials is not None:
        value["credentials"] = credentials
    return value


def source_workflow(workflow_id="wf-one", name="Workflow One", marker="source", credentials=None):
    return {
        "id": workflow_id,
        "name": name,
        "nodes": [make_node(marker, credentials)],
        "connections": {},
        "settings": {
            "executionOrder": "v1",
            "binaryMode": "separate",
            "availableInMCP": False,
        },
        "active": True,
        "versionId": "version-old",
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z",
        "tags": [],
        "meta": {"ignored": True},
    }


def live_workflow(workflow_id="wf-one", name="Workflow One", marker="live", credentials=None, active=True):
    value = source_workflow(workflow_id, name, marker, credentials)
    value.update(
        {
            "active": active,
            "activeVersionId": "version-old" if active else None,
            "versionId": "version-old",
            "triggerCount": 1,
            "isArchived": False,
            "shared": [],
            "activeVersion": None,
        }
    )
    return value


class MockN8n:
    def __init__(self, workflows, fail_put_id=None):
        self.workflows = deepcopy(workflows)
        self.fail_put_id = fail_put_id
        self.requests = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def send_json(self, status, body):
                data = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def authorized(self):
                return self.headers.get("X-N8N-API-KEY") == API_KEY

            def do_GET(self):
                owner.requests.append(("GET", self.path, None))
                if not self.authorized():
                    self.send_json(401, {"message": "unauthorized"})
                    return
                parsed = urlparse(self.path)
                if parsed.path == "/api/v1/workflows":
                    self.send_json(200, {"data": list(owner.workflows.values()), "nextCursor": None})
                    return
                prefix = "/api/v1/workflows/"
                workflow_id = parsed.path[len(prefix) :] if parsed.path.startswith(prefix) else ""
                workflow = owner.workflows.get(workflow_id)
                self.send_json(200, workflow) if workflow else self.send_json(404, {"message": "not found"})

            def do_PUT(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                owner.requests.append(("PUT", self.path, body))
                if not self.authorized():
                    self.send_json(401, {"message": "unauthorized"})
                    return
                workflow_id = self.path.rsplit("/", 1)[-1]
                if workflow_id == owner.fail_put_id:
                    self.send_json(400, {"message": f"mock update rejected {API_KEY}"})
                    return
                if workflow_id not in owner.workflows:
                    self.send_json(404, {"message": "not found"})
                    return
                current = owner.workflows[workflow_id]
                current.update(deepcopy(body))
                current["id"] = workflow_id
                current["versionId"] = f"version-{uuid.uuid4()}"
                if current.get("active"):
                    current["activeVersionId"] = current["versionId"]
                self.send_json(200, current)

            def do_POST(self):
                owner.requests.append(("POST", self.path, None))
                self.send_json(405, {"message": "POST forbidden"})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


class DeploymentScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / "deployment-state.json"
        self.state.write_text('{"schemaVersion":1,"workflows":[]}', encoding="utf-8")
        self.backups = self.root / "backups"

    def tearDown(self):
        self.temp.cleanup()

    def write_json(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def write_state_entry(self, workflow_id, live_version_id):
        self.state.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "workflows": [
                        {
                            "id": workflow_id,
                            "name": "Workflow One",
                            "liveVersionId": live_version_id,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def run_script(self, paths, mode, base_url, include_key=True, extra=None):
        quote = lambda value: "'" + str(value).replace("'", "''") + "'"
        path_array = "@(" + ",".join(quote(path) for path in paths) + ")"
        invocation = " ".join(
            [
                "&", quote(SCRIPT), "-WorkflowPath", path_array, mode,
                "-BaseUrl", quote(base_url),
                "-DeploymentStatePath", quote(self.state),
                "-BackupRoot", quote(self.backups),
                *(extra or []),
            ]
        )
        command = [
            str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-Command", invocation,
        ]
        env = os.environ.copy()
        if include_key:
            env["PROJECT_E_N8N_API_KEY"] = API_KEY
        else:
            env.pop("PROJECT_E_N8N_API_KEY", None)
        return subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            env=env,
            timeout=30,
        )

    def test_missing_api_key_fails_without_request(self):
        path = self.write_json("workflow.json", source_workflow())
        result = self.run_script([path], "-DryRun", "http://127.0.0.1:1", include_key=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PROJECT_E_N8N_API_KEY", result.stdout + result.stderr)

    def test_invalid_json_and_missing_id_fail_safely(self):
        invalid = self.root / "invalid.json"
        invalid.write_text("{invalid", encoding="utf-8")
        missing = source_workflow()
        missing.pop("id")
        missing_path = self.write_json("missing.json", missing)
        with MockN8n({"wf-one": live_workflow()}) as api:
            invalid_result = self.run_script([invalid], "-DryRun", api.base_url)
            missing_result = self.run_script([missing_path], "-DryRun", api.base_url)
            self.assertNotEqual(invalid_result.returncode, 0)
            self.assertIn("Invalid workflow JSON", invalid_result.stdout + invalid_result.stderr)
            self.assertNotEqual(missing_result.returncode, 0)
            self.assertIn("has no id", missing_result.stdout + missing_result.stderr)
            self.assertFalse(any(method == "PUT" for method, *_ in api.requests))

    def test_unknown_id_and_name_mismatch_fail(self):
        unknown = self.write_json("unknown.json", source_workflow("missing", "Missing"))
        mismatch = self.write_json("mismatch.json", source_workflow(name="Source Name"))
        with MockN8n({"wf-one": live_workflow(name="Live Name")}) as api:
            unknown_result = self.run_script([unknown], "-DryRun", api.base_url)
            mismatch_result = self.run_script([mismatch], "-DryRun", api.base_url)
            self.assertNotEqual(unknown_result.returncode, 0)
            self.assertIn("was not found", unknown_result.stdout + unknown_result.stderr)
            self.assertNotEqual(mismatch_result.returncode, 0)
            self.assertIn("name mismatch", (mismatch_result.stdout + mismatch_result.stderr).lower())

    def test_duplicate_selected_ids_fail(self):
        first = self.write_json("one.json", source_workflow())
        second = self.write_json("two.json", source_workflow())
        with MockN8n({"wf-one": live_workflow()}) as api:
            result = self.run_script([first, second], "-DryRun", api.base_url)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Duplicate selected workflow id", result.stdout + result.stderr)

    def test_safe_node_rename_preserves_credential_identity(self):
        credentials = {"postgres": {"id": "cred-one", "name": "Postgres"}}
        source = source_workflow(credentials=credentials)
        source["nodes"][0]["name"] = "Renamed Database Node"
        path = self.write_json("workflow.json", source)
        with MockN8n({"wf-one": live_workflow(credentials=credentials)}) as api:
            result = self.run_script([path], "-DryRun", api.base_url)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Credential references for Workflow One unchanged", result.stdout)
            self.assertFalse(any(method == "PUT" for method, *_ in api.requests))

    def test_same_node_different_credential_id_fails(self):
        source_creds = {"postgres": {"id": "cred-source", "name": "Postgres"}}
        live_creds = {"postgres": {"id": "cred-live", "name": "Postgres"}}
        path = self.write_json("workflow.json", source_workflow(credentials=source_creds))
        with MockN8n({"wf-one": live_workflow(credentials=live_creds)}) as api:
            result = self.run_script([path], "-DryRun", api.base_url)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Credential references", result.stdout + result.stderr)
            self.assertIn("node name 'Start'", result.stdout + result.stderr)

    def test_same_node_different_credential_type_fails(self):
        source_creds = {"postgres": {"id": "cred-one", "name": "Database"}}
        live_creds = {"mysql": {"id": "cred-one", "name": "Database"}}
        path = self.write_json("workflow.json", source_workflow(credentials=source_creds))
        with MockN8n({"wf-one": live_workflow(credentials=live_creds)}) as api:
            result = self.run_script([path], "-DryRun", api.base_url)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("credential type 'postgres'", result.stdout + result.stderr)
            self.assertIn("credential type 'mysql'", result.stdout + result.stderr)

    def test_credential_removal_and_addition_fail(self):
        credentials = {"postgres": {"id": "cred-one", "name": "Postgres"}}
        source_with = self.write_json(
            "source-with.json", source_workflow(credentials=credentials)
        )
        source_without = self.write_json("source-without.json", source_workflow())

        with MockN8n({"wf-one": live_workflow()}) as api:
            added = self.run_script([source_with], "-DryRun", api.base_url)
            self.assertNotEqual(added.returncode, 0)
            self.assertIn("Live references: <none>", added.stdout + added.stderr)

        with MockN8n({"wf-one": live_workflow(credentials=credentials)}) as api:
            removed = self.run_script([source_without], "-DryRun", api.base_url)
            self.assertNotEqual(removed.returncode, 0)
            self.assertIn("Source references: <none>", removed.stdout + removed.stderr)

    def test_historical_source_version_passes_when_live_matches_deployment_state(self):
        source = source_workflow(marker="changed")
        source["versionId"] = "historical-export-version"
        path = self.write_json("workflow.json", source)
        live = live_workflow(marker="live")
        live["versionId"] = "last-deployed-version"
        live["activeVersionId"] = "last-deployed-version"
        self.write_state_entry("wf-one", "last-deployed-version")

        with MockN8n({"wf-one": live}) as api:
            result = self.run_script([path], "-DryRun", api.base_url)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("No live version drift: Workflow One", result.stdout)
            self.assertNotIn("historical-export-version", result.stdout + result.stderr)

    def test_unexpected_live_version_drift_from_deployment_state_fails(self):
        path = self.write_json("workflow.json", source_workflow(marker="changed"))
        live = live_workflow(marker="live")
        live["versionId"] = "unexpected-live-version"
        live["activeVersionId"] = "unexpected-live-version"
        self.write_state_entry("wf-one", "last-deployed-version")

        with MockN8n({"wf-one": live}) as api:
            result = self.run_script([path], "-DryRun", api.base_url)
            self.assertNotEqual(result.returncode, 0)
            output = result.stdout + result.stderr
            self.assertIn("Live version drift detected", output)
            self.assertIn("last-deployed-version", output)
            self.assertIn("unexpected-live-version", output)
            self.assertFalse(any(method == "PUT" for method, *_ in api.requests))

    def test_first_managed_deployment_warns_but_ignores_historical_source_version(self):
        source = source_workflow(marker="changed")
        source["versionId"] = "historical-export-version"
        path = self.write_json("workflow.json", source)
        live = live_workflow(marker="live")
        live["versionId"] = "current-live-version"
        live["activeVersionId"] = "current-live-version"

        with MockN8n({"wf-one": live}) as api:
            result = self.run_script([path], "-DryRun", api.base_url)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = result.stdout + result.stderr
            self.assertIn("first managed deployment", output)
            self.assertIn("live-version drift cannot be established", output)
            self.assertNotIn("historical-export-version", output)
            self.assertFalse(any(method == "PUT" for method, *_ in api.requests))

    def test_dry_run_makes_no_put_and_no_artifacts(self):
        path = self.write_json("workflow.json", source_workflow(marker="changed"))
        original_state = self.state.read_text(encoding="utf-8")
        with MockN8n({"wf-one": live_workflow(marker="live")}) as api:
            result = self.run_script([path], "-DryRun", api.base_url)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(any(method in ("PUT", "POST") for method, *_ in api.requests))
            self.assertFalse(self.backups.exists())
            self.assertEqual(self.state.read_text(encoding="utf-8"), original_state)
            self.assertIn("NO LIVE CHANGES MADE", result.stdout)

    def test_apply_sanitizes_backs_up_verifies_and_updates_state(self):
        path = self.write_json("workflow.json", source_workflow(marker="changed"))
        with MockN8n({"wf-one": live_workflow(marker="live", active=True)}) as api:
            result = self.run_script([path], "-Apply", api.base_url)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            puts = [request for request in api.requests if request[0] == "PUT"]
            self.assertEqual(len(puts), 1)
            self.assertFalse(any(method == "POST" for method, *_ in api.requests))
            body = puts[0][2]
            self.assertEqual(set(body), {"name", "nodes", "connections", "settings"})
            self.assertEqual(
                body["settings"],
                {"executionOrder": "v1", "availableInMCP": False},
            )
            self.assertNotIn("binaryMode", body["settings"])
            for forbidden in ("id", "active", "versionId", "createdAt", "updatedAt", "tags", "meta"):
                self.assertNotIn(forbidden, body)
            self.assertEqual(len(list(self.backups.glob("*/*.json"))), 1)
            state = json.loads(self.state.read_text(encoding="utf-8-sig"))
            self.assertEqual(state["workflows"][0]["id"], "wf-one")
            self.assertTrue(state["workflows"][0]["active"])
            self.assertIn("SUCCESS", result.stdout)

    def test_api_error_stops_batch_and_reports_rollback(self):
        one = self.write_json("one.json", source_workflow("wf-one", "Workflow One", "changed"))
        two = self.write_json("two.json", source_workflow("wf-two", "Workflow Two", "changed"))
        workflows = {
            "wf-one": live_workflow("wf-one", "Workflow One", "live"),
            "wf-two": live_workflow("wf-two", "Workflow Two", "live"),
        }
        with MockN8n(workflows, fail_put_id="wf-two") as api:
            result = self.run_script([one, two], "-Apply", api.base_url)
            self.assertNotEqual(result.returncode, 0)
            puts = [request for request in api.requests if request[0] == "PUT"]
            self.assertEqual([request[1].rsplit("/", 1)[-1] for request in puts], ["wf-one", "wf-two"])
            self.assertIn("SAFE ROLLBACK ORDER", result.stdout + result.stderr)
            output = result.stdout + result.stderr
            self.assertIn("API response: mock update rejected <redacted>", output)
            self.assertNotIn(API_KEY, output)
            self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["workflows"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
