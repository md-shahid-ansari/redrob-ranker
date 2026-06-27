import re
from pathlib import Path

JD_PATH = Path("data/job_description.docx")

def read_docx(filepath):
    """Extract text from a .docx file."""
    try:
        from docx import Document
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        raise ImportError("python-docx is required to read .docx files. Install with: pip install python-docx")

def load_jd_text():
    if not JD_PATH.exists():
        raise FileNotFoundError(f"JD not found at {JD_PATH}")
    return read_docx(JD_PATH)

def parse_jd(jd_text=None):
    if jd_text is None:
        jd_text = load_jd_text()

    from src.config import JD_REQUIRED_SKILLS, JD_NICE_TO_HAVE, PREFERRED_LOCATIONS

    required = set(JD_REQUIRED_SKILLS)
    nice = set(JD_NICE_TO_HAVE)
    locations = set(PREFERRED_LOCATIONS)

    # YoE range
    yoe_match = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*years?", jd_text, re.IGNORECASE)
    yoe_min, yoe_max = (int(yoe_match.group(1)), int(yoe_match.group(2))) if yoe_match else (5, 9)

    # Notice period
    notice_match = re.search(r"notice\s*period\s*[<]*\s*(\d+)\s*days?", jd_text, re.IGNORECASE)
    notice_days = int(notice_match.group(1)) if notice_match else 30

    # Locations
    loc_matches = re.findall(r"(?:Pune|Noida|Hyderabad|Mumbai|Delhi NCR|Gurugram)", jd_text, re.IGNORECASE)
    for loc in loc_matches:
        locations.add(loc.lower())

    return {
        "required_skills": required,
        "nice_to_have": nice,
        "preferred_locations": locations,
        "yoe_range": (yoe_min, yoe_max),
        "notice_period_days": notice_days,
    }

if __name__ == "__main__":
    print(parse_jd())