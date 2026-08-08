import re
from dataclasses import dataclass
import fitz

UNKNOWN = "Unknown"

@dataclass
class ExtractedPaper:
    start: int
    end: int
    text: str
    metadata: dict

PATTERNS = {
    "course_code": r"\b(?:[A-Z]{2,5}\s?\d{3,4}|[A-Z]{2,5}-\d{3,4})\b",
    "year": r"\b(20\d{2})\b",
    "semester": r"\b(?:semester|sem\.?)[\s:-]*(\d+|[IVX]+)\b",
    "marks": r"(?:max(?:imum)?\s*marks?|marks)\s*[:\-]?\s*(\d+)",
    "duration": r"(?:time|duration)\s*[:\-]?\s*([\d.]+\s*(?:hours?|hrs?|minutes?|mins?))",
    "regulation": r"(?:regulation|reg\.)\s*[:\-]?\s*([A-Z0-9-]+)",
}

def _match(pattern, text, group=0):
    found = re.search(pattern, text, re.I)
    return found.group(group).strip() if found else UNKNOWN

def is_paper_start(text: str) -> bool:
    header = text[:2200].lower()
    signals = sum(term in header for term in ("question paper", "maximum marks", "time:", "university", "semester", "examination"))
    return signals >= 2 and bool(re.search(PATTERNS["year"], header))

def metadata_from_text(text: str) -> dict:
    clean = " ".join(text.split())
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    subject = UNKNOWN
    for line in lines[:20]:
        if re.search(r"(?:subject|course|paper)\s*(?:title|name)?\s*[:\-]", line, re.I):
            subject = re.split(r"[:\-]", line, maxsplit=1)[-1].strip(); break
    if subject == UNKNOWN:
        subject = next((x for x in lines[:12] if 5 < len(x) < 120 and not re.search(r"university|examination|semester|marks|time", x, re.I)), UNKNOWN)
    return {
        "subject": subject, "course_code": _match(PATTERNS["course_code"], clean),
        "year": _match(PATTERNS["year"], clean), "semester": _match(PATTERNS["semester"], clean, 1),
        "marks": _match(PATTERNS["marks"], clean, 1), "duration": _match(PATTERNS["duration"], clean, 1),
        "regulation": _match(PATTERNS["regulation"], clean, 1),
        "department": _match(r"\b(CSE|ECE|EEE|MECH|CIVIL|MBA|IT)\b", clean),
        "month": _match(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b", clean),
        "exam_type": "University Examination" if "examination" in clean.lower() else UNKNOWN,
        "university": next((x for x in lines[:8] if "university" in x.lower()), UNKNOWN),
    }

def extract_papers(pdf_path: str) -> list[ExtractedPaper]:
    doc = fitz.open(pdf_path)
    page_texts = [p.get_text("text") for p in doc]
    starts = [i for i, text in enumerate(page_texts) if is_paper_start(text)] or [0]
    result = []
    for index, start in enumerate(starts):
        end = (starts[index + 1] - 1) if index + 1 < len(starts) else len(doc) - 1
        text = "\n".join(page_texts[start:end + 1])
        result.append(ExtractedPaper(start, end, text, metadata_from_text(text)))
    return result

def write_split(source_path: str, destination: str, start: int, end: int):
    source, output = fitz.open(source_path), fitz.open()
    output.insert_pdf(source, from_page=start, to_page=end)
    output.save(destination); output.close(); source.close()
