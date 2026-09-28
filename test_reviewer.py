import unittest

from reviewer import ReviewReport, extract_job_keywords, extract_resume_sections, extract_resume_text, report_to_markdown, review_resume


class ResumeReviewerTests(unittest.TestCase):
    def test_extracts_plain_text_resume(self):
        self.assertEqual(extract_resume_text("resume.txt", b"  Python  and SQL  "), "Python and SQL")

    def test_rejects_unsupported_resume_format(self):
        with self.assertRaisesRegex(ValueError, "PDF, DOCX, or TXT"):
            extract_resume_text("resume.rtf", b"resume")

    def test_extracts_common_resume_sections(self):
        sections = extract_resume_sections("SUMMARY\nAnalyst with Python experience.\n\nEXPERIENCE\nBuilt reports.\nSKILLS\nPython, SQL")

        self.assertEqual(sections["Summary"], "Analyst with Python experience.")
        self.assertEqual(sections["Experience"], "Built reports.")
        self.assertEqual(sections["Skills"], "Python, SQL")

    def test_local_review_maps_keywords_and_validates_schema(self):
        resume = "Experience\nBuilt a Python data analysis dashboard and reduced report time by 20%.\nEducation\nBSc"
        job = "Required: Python and SQL. Tableau is preferred."
        report, mode = review_resume(resume, job, "Data Analyst")

        self.assertIsInstance(report, ReviewReport)
        self.assertEqual(mode, "Local keyword review")
        self.assertEqual([item.keyword for item in report.keyword_matches], ["python", "sql", "tableau"])
        self.assertEqual(report.keyword_matches[0].status, "Found")
        self.assertEqual(report.keyword_matches[1].status, "Not found")
        self.assertEqual(report.requirement_mapping[0].priority, "Must-have")
        self.assertEqual(report.requirement_mapping[0].status, "Evidence found")
        self.assertEqual(report.requirement_mapping[1].status, "Not found")
        self.assertEqual(report.requirement_mapping[2].priority, "Preferred")
        self.assertIn("Requirement-to-evidence map", report_to_markdown(report, "Data Analyst"))
        self.assertIn("Advisory feedback only", report_to_markdown(report, "Data Analyst"))

    def test_job_keyword_parser_ignores_unknown_terms(self):
        self.assertEqual(extract_job_keywords("Python and quantum gardening experience"), ["python"])

    def test_requires_both_inputs(self):
        with self.assertRaisesRegex(ValueError, "required"):
            review_resume("resume", "")


if __name__ == "__main__":
    unittest.main()