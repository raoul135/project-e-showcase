import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StaticContractTest(unittest.TestCase):
    def test_python_sources_parse(self):
        paths = [
            ROOT / "dashboard" / "app.py",
            ROOT / "dashboard" / "db.py",
            ROOT / "services" / "job-reader" / "api_contract.py",
        ]
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_complete_seven_file_migration_chain_is_present(self):
        migrations = sorted((ROOT / "database" / "migrations").glob("*.sql"))
        self.assertEqual(
            [path.name[:2] for path in migrations],
            [f"{number:02d}" for number in range(1, 8)],
        )

    def test_workflow_json_files_parse(self):
        workflows = sorted((ROOT / "workflows").rglob("*.json"))
        self.assertEqual(len(workflows), 5)
        for path in workflows:
            with self.subTest(path=path.relative_to(ROOT)):
                json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
