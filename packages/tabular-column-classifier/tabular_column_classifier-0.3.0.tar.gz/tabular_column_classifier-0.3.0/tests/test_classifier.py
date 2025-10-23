import os
import sys
import unittest

import pandas as pd

# Ensure the package is importable when running tests from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from column_classifier import ColumnClassifier


class TestColumnClassifier(unittest.TestCase):
    def test_basic_classification(self):
        classifier = ColumnClassifier(sample_size=3)
        cities = pd.Series(["New York", "Paris", "Tokyo"])
        result = classifier.classify_column(cities, column_name="cities")
        self.assertIn("classification", result)
        self.assertIn("probabilities", result)
        self.assertIn("sources", result)
        self.assertEqual(result["classification"], "LOCATION")
        self.assertGreaterEqual(result["probabilities"].get("LOCATION", 0.0), 0.5)
        self.assertIn("spacy", result["sources"])
        self.assertIn("probabilities", result["sources"]["spacy"])

    def test_table_and_multi_table_output(self):
        classifier = ColumnClassifier(sample_size=3)
        df1 = pd.DataFrame({"name": ["Alice", "Bob"], "age": [34, 29]})
        df2 = pd.DataFrame({"city": ["London", "Oslo"], "founded": [43, 1048]})

        table_result = classifier.classify_table(df1, table_name="people")
        self.assertEqual(table_result["table"], "people")
        self.assertIn("name", table_result["columns"])
        self.assertIn("classification", table_result["columns"]["name"])
        self.assertIn("sources", table_result["columns"]["name"])

        results = classifier.classify_multiple_tables([df1, df2])

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["table"], "table_1")
        self.assertEqual(results[1]["table"], "table_2")
        self.assertIn("name", results[0]["columns"])
        self.assertIn("city", results[1]["columns"])
        self.assertIn("classification", results[0]["columns"]["name"])

    def test_llm_retry_and_parse(self):
        class FakeMessage:
            def __init__(self, content: str):
                self.content = content

        class FakeResponse:
            def __init__(self, content: str):
                self.message = FakeMessage(content)

        class FakeClient:
            def __init__(self):
                self.calls = 0

            def chat(self, model, messages):
                self.calls += 1
                if self.calls == 1:
                    return {
                        "message": {
                            "content": "I cannot provide the answer in the requested format."
                        }
                    }
                return FakeResponse(
                    '{"classification": "PERSON", "probabilities": {"PERSON": 0.9}}'
                )

        classifier = ColumnClassifier(sample_size=3)
        classifier.llm_client = FakeClient()
        classifier.llm_model = "fake"
        classifier.llm_system_prompt = None
        classifier.llm_max_retries = 1
        classifier.llm_retry_delay = 0.0

        sample = pd.Series(["Alice", "Bob", "Charlie"])
        llm_result = classifier._maybe_call_llm(
            "people", sample, {"PERSON": 0.6, "STRING": 0.4}
        )

        self.assertIsNotNone(llm_result)
        self.assertEqual(llm_result["classification"], "PERSON")
        self.assertGreaterEqual(llm_result["probabilities"].get("PERSON", 0.0), 0.9)
        self.assertEqual(llm_result["source"], "llm")
        self.assertEqual(llm_result["attempt"], 2)

    def test_llm_total_fallback_uses_baseline(self):
        class FailingClient:
            def chat(self, model, messages):
                return {"message": {"content": "I cannot comply with that request."}}

        classifier = ColumnClassifier(sample_size=3)
        classifier.llm_client = FailingClient()
        classifier.llm_model = "fake"
        classifier.llm_system_prompt = None
        classifier.llm_max_retries = 0
        classifier.llm_retry_delay = 0.0

        sample = pd.Series(["42", "7", "13"])
        fallback = classifier._maybe_call_llm(
            "numbers", sample, {"NUMBER": 0.8, "STRING": 0.2}
        )

        self.assertEqual(fallback["classification"], "NUMBER")
        self.assertEqual(fallback["probabilities"]["NUMBER"], 1.0)
        self.assertEqual(fallback["source"], "fallback")


if __name__ == "__main__":
    unittest.main()
