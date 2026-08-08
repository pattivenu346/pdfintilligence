from app.services.extractor import is_paper_start, metadata_from_text

SAMPLE = '''ACME UNIVERSITY
B.Tech Degree Examination, May 2024
Semester 5
Subject: Operating Systems
CS305
Time: 3 Hours                 Maximum Marks: 70
'''

def test_detects_question_paper_header():
    assert is_paper_start(SAMPLE)

def test_extracts_resilient_metadata():
    meta = metadata_from_text(SAMPLE)
    assert meta["course_code"] == "CS305"
    assert meta["year"] == "2024"
    assert meta["semester"] == "5"
    assert meta["marks"] == "70"
