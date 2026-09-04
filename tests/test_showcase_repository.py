import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRESENTATIVE = ROOT / "workflows" / "representative"
DEMO = ROOT / "workflows" / "demo" / "fictional-end-to-end-demo.json"
FORBIDDEN_TOP_LEVEL = {
    "id",
    "versionId",
    "meta",
    "tags",
    "pinData",
    "staticData",
    "shared",
    "createdAt",
    "updatedAt",
}
LIVE_HOST_MARKERS = {
    "host.docker.internal",
    "ai-qdrant",
    "127.0.0.1:5678",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def walk(value):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


class ShowcaseRepositoryTest(unittest.TestCase):
    def test_exactly_three_representative_workflows_are_present(self):
        self.assertEqual(
            {path.name for path in REPRESENTATIVE.glob("*.json")},
            {
                "deterministic-opportunity-scoring.json",
                "hybrid-evidence-retrieval.json",
                "proposal-auditor.json",
            },
        )

    def test_representative_workflows_are_sanitized(self):
        for path in REPRESENTATIVE.glob("*.json"):
            with self.subTest(path=path.name):
                workflow = load_json(path)
                self.assertFalse(FORBIDDEN_TOP_LEVEL.intersection(workflow))
                self.assertFalse(workflow["active"])
                text = json.dumps(workflow)
                self.assertNotIn('"credentials"', text)
                for marker in LIVE_HOST_MARKERS:
                    self.assertNotIn(marker, text)
                for node in workflow["nodes"]:
                    if node.get("type") == "n8n-nodes-base.executeWorkflow":
                        self.assertTrue(node.get("disabled"))
                        self.assertEqual(
                            node["parameters"]["workflowId"]["value"],
                            "CONFIGURE_DOWNSTREAM_WORKFLOW_ID",
                        )

    def test_demo_is_credential_free_fictional_and_self_contained(self):
        workflow = load_json(DEMO)
        self.assertFalse(FORBIDDEN_TOP_LEVEL.intersection(workflow))
        self.assertFalse(workflow["active"])
        text = json.dumps(workflow).lower()
        self.assertNotIn('"credentials"', text)
        self.assertNotIn("upwork.com", text)
        self.assertNotIn("gmail", text)
        self.assertNotIn("postgres", text)
        self.assertNotIn("qdrant", text)
        self.assertNotIn("openai", text)
        node_names = {node["name"] for node in workflow["nodes"]}
        self.assertEqual(len(node_names), len(workflow["nodes"]))
        for source, branches in workflow["connections"].items():
            self.assertIn(source, node_names)
            for branch in branches["main"]:
                for edge in branch:
                    self.assertIn(edge["node"], node_names)

    def test_embedded_javascript_parses(self):
        node = os.environ.get("NODE_BINARY") or shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        paths = list(REPRESENTATIVE.glob("*.json")) + [DEMO]
        for path in paths:
            workflow = load_json(path)
            for workflow_node in workflow["nodes"]:
                code = workflow_node.get("parameters", {}).get("jsCode")
                if not code:
                    continue
                with self.subTest(workflow=path.name, node=workflow_node["name"]):
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".js", encoding="utf-8", delete=False
                    ) as handle:
                        handle.write("async function __n8n_node__() {\n")
                        handle.write(code)
                        handle.write("\n}\n")
                        temporary = Path(handle.name)
                    try:
                        result = subprocess.run(
                            [node, "--check", str(temporary)],
                            capture_output=True,
                            text=True,
                        )
                        self.assertEqual(
                            result.returncode, 0, result.stdout + result.stderr
                        )
                    finally:
                        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
