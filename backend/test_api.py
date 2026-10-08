import json
import unittest
from app import app
import database

class FlaskApiTests(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()
        # Initialize DB
        database.init_db()

    def test_1_analyze_nlp(self):
        print("\n--- Test 1: Analyze New Scam Job (Via Model) ---")
        response = self.client.post('/analyze', 
                                    data=json.dumps({
                                        "company_name": "TestCorp",
                                        "job_title": "Data Entry",
                                        "description": "Please pay fee upfront and registration fee for interview."
                                    }),
                                    content_type='application/json')
        data = json.loads(response.data)
        print("Response:", json.dumps(data, indent=2))
        self.assertEqual(data["label"], "Fake")
        self.assertEqual(data["source"], "model")

    def test_2_report_scam(self):
        print("\n--- Test 2: Report Scam ---")
        response = self.client.post('/report', 
                                    data=json.dumps({
                                        "company_name": "ReportedInc",
                                        "job_title": "Manager",
                                        "description": "Seems fine but it's a scam reported by user."
                                    }),
                                    content_type='application/json')
        data = json.loads(response.data)
        print("Response:", json.dumps(data, indent=2))
        self.assertIn("message", data)

    def test_3_analyze_memory(self):
        print("\n--- Test 3: Analyze Reported Scam (Via Memory) ---")
        response = self.client.post('/analyze', 
                                    data=json.dumps({
                                        "company_name": "ReportedInc",
                                        "job_title": "Manager",
                                        "description": "Any text here doesn't matter since it should hit memory."
                                    }),
                                    content_type='application/json')
        data = json.loads(response.data)
        print("Response:", json.dumps(data, indent=2))
        self.assertEqual(data["label"], "Fake")
        self.assertEqual(data["source"], "memory")
        self.assertIn("report_count", data)

if __name__ == "__main__":
    unittest.main(verbosity=2)
