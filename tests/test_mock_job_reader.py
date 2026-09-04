import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "services" / "job-reader" / "api_contract.py"


def load_module():
    spec = importlib.util.spec_from_file_location("showcase_api_contract", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


try:
    CONTRACT = load_module()
except ModuleNotFoundError:
    CONTRACT = None


@unittest.skipIf(CONTRACT is None, "FastAPI/Pydantic showcase dependencies unavailable")
class MockJobReaderTest(unittest.TestCase):
    def test_accepts_only_fictional_reserved_host(self):
        url = "https://jobs.example.invalid/jobs/demo-001"
        self.assertEqual(CONTRACT.validate_demo_url(url), url)

    def test_rejects_nonfictional_or_credentialed_urls(self):
        rejected = [
            "https://example.com/jobs/demo-001",
            "https://" + "demo:demo" + "@jobs.example.invalid/jobs/demo-001",
            "http://jobs.example.invalid/jobs/demo-001",
            "https://jobs.example.invalid/not-a-job/demo-001",
        ]
        for value in rejected:
            with self.subTest(value=value), self.assertRaises(ValueError):
                CONTRACT.validate_demo_url(value)

    def test_provider_returns_deterministic_fictional_data(self):
        result = CONTRACT.MockJobProvider().read(
            "https://jobs.example.invalid/jobs/demo-001"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["job"]["job_id"], "DEMO-001")
        self.assertEqual(result["source"], "fictional-showcase-provider")


if __name__ == "__main__":
    unittest.main(verbosity=2)
