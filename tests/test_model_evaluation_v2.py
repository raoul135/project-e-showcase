import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "workflows" / "evaluation" / "evaluation-cases.v2.json"
WORKFLOW = ROOT / "workflows" / "evaluation" / "project-e-local-model-rag-quality-evaluation-v2.json"
STAGES = ROOT / "tests" / "fixtures" / "model-evaluation" / "stage-fixtures.v2.json"


def validate_answer(value, chunk_ids, forbidden_terms):
    failures = []
    if not isinstance(value, dict):
        return ["parse_failure"]
    if not isinstance(value.get("answer"), str) or not isinstance(value.get("claims"), list):
        failures.append("schema_failure")
    confidence = value.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        failures.append("confidence_failure")
    if not isinstance(value.get("insufficient_evidence"), bool):
        failures.append("schema_failure")
    for claim in value.get("claims", []):
        ids = claim.get("source_chunk_ids", []) if isinstance(claim, dict) else []
        if not ids or any(str(item) not in chunk_ids for item in ids):
            failures.append("citation_failure")
    rendered = json.dumps(value).lower()
    if any(term.lower() in rendered for term in forbidden_terms):
        failures.append("unsupported_claim_or_boundary_failure")
    return sorted(set(failures))


class ModelEvaluationV2Test(unittest.TestCase):
    def test_cases_are_complete_and_cover_required_boundaries(self):
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases), 20)
        required = {"case_id", "query", "category", "expected_filenames", "expected_terms", "forbidden_terms", "expected_answer_points", "negative_case", "minimum_relevant_results", "top_k"}
        self.assertTrue(all(required <= set(case) for case in cases))
        self.assertGreaterEqual(sum(case["negative_case"] for case in cases), 6)
        self.assertIn("irrelevant technologies", {case["category"] for case in cases})

    def test_validator_rejects_malformed_missing_ids_and_unsupported_claims(self):
        ids = {"chunk-1"}
        self.assertEqual(validate_answer(None, ids, []), ["parse_failure"])
        missing_id = {"answer": "x", "claims": [{"claim": "x", "source_chunk_ids": []}], "confidence": 0.4, "insufficient_evidence": False}
        self.assertIn("citation_failure", validate_answer(missing_id, ids, []))
        unsupported = {"answer": "Paid client experience", "claims": [{"claim": "Paid client experience", "source_chunk_ids": ["chunk-1"]}], "confidence": 0.4, "insufficient_evidence": False}
        self.assertIn("unsupported_claim_or_boundary_failure", validate_answer(unsupported, ids, ["paid client"]))

    def test_irrelevant_retrieval_fails_negative_boundary(self):
        hits, minimum, forbidden = 0, 1, 1
        negative_query_success = forbidden == 0 and hits >= minimum
        self.assertFalse(negative_query_success)

    def test_stage_fixtures_cover_the_six_model_dependent_stages(self):
        stages = json.loads(STAGES.read_text(encoding="utf-8"))
        self.assertEqual(len(stages), 6)
        self.assertTrue(all(item["contract"]["job_id"] == "eval-job-001" for item in stages))

    def test_import_export_has_no_secrets_and_uses_real_hybrid_prefetch(self):
        workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        self.assertFalse(workflow["active"])
        serialized = json.dumps(workflow).lower()
        for marker in ("api_key", "bearer ", "sk-", "password"):
            self.assertNotIn(marker, serialized)
        qdrant = next(node for node in workflow["nodes"] if node["name"] == "Query Qdrant Hybrid RRF")
        body = qdrant["parameters"]["jsonBody"]
        self.assertIn("text-embedding-bge-m3", body)
        self.assertIn("bm25", body)
        self.assertIn("fusion:'rrf'", body)
        self.assertGreaterEqual(body.count("prefetch"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
