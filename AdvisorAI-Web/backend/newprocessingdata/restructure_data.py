#!/usr/bin/env python3
"""
Restructure raw faculty CSV + course CSV data into optimized documents
for vector DB embedding and retrieval.

Outputs (all in this directory):
  - structured_faculty_profiles.json
  - faculty_course_mapping.json
  - enriched_courses.json
  - faculty_research.json

Run from the backend/ directory:
    python newprocessingdata/restructure_data.py
"""

import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DATA_DIR = BACKEND_DIR / "Data"

FACULTY_CSVS = [
    ("School of Business", DATA_DIR / "Business_school" / "faculty_directory1.csv"),
    ("College of Arts and Letters (HASS)", DATA_DIR / "HASS_school" / "faculty_directory1.csv"),
    ("Schaefer School of Engineering & Science", DATA_DIR / "Schafer_school" / "faculty_directory1.csv"),
]

COURSE_CSV = DATA_DIR / "stevens_courses_full_details.csv"

VALID_COURSE_PREFIXES = {
    "AAI", "ACC", "BIA", "BIO", "BIOE", "BME", "BT", "CAL", "CE", "CH",
    "CHE", "CLK", "CM", "COMM", "COOP", "CPE", "CS", "DE", "DS", "ECON",
    "EE", "ELC", "EM", "EMT", "EN", "ENGR", "ES", "FA", "FE", "FIN",
    "GEN", "HAR", "HASS", "HHS", "HLI", "HMU", "HONR", "HPL", "HQSS",
    "HSSC", "HST", "HTH", "HUM", "IDE", "IPD", "ISE", "LCH", "LFR",
    "LSP", "LTL", "MA", "ME", "MGT", "MIS", "MT", "NANO", "NE", "OE",
    "PAE", "PEP", "PIN", "PME", "PRV", "QF", "SEF", "SES", "SM", "SOC",
    "SSES", "SSW", "SYS", "TE", "TG", "TM", "E",
}

# Pattern that matches course codes like "FE 621", "FE-621", "FE621",
# "HASS 103", "ACC-351", "E 355", "CS 115", "CAL 105"
COURSE_CODE_RE = re.compile(
    r'\b(' + '|'.join(sorted(VALID_COURSE_PREFIXES, key=len, reverse=True)) +
    r')[\s\-]?(\d{3})\b',
    re.IGNORECASE,
)


def normalize_course_code(prefix: str, number: str) -> str:
    """Normalize to 'FE 621' format (uppercase prefix, space, 3-digit number)."""
    return f"{prefix.upper()} {number}"


def parse_courses_text(text: str) -> list[dict]:
    """
    Parse a free-text Courses field into a list of {code, name} dicts.
    Handles formats like:
      - 'MIS110 Creative Problem Solving BT416 Business Process Management'
      - 'FE-621 - Computational Methods in Finance'
      - 'ACC-351: Federal Taxation of Individuals'
      - 'CAL 105 (freshman colloquium): Knowledge, Nature, Culture'
    """
    if not text or not text.strip():
        return []

    # Skip entries that are numbered lists without codes (e.g., Daneshmand's format)
    if re.match(r'^\s*1\.\s', text) and not COURSE_CODE_RE.search(text):
        return []

    # Skip entries that start with freeform text (e.g., "Courses Taught at Stevens •")
    cleaned = text.strip()
    if cleaned.startswith("Courses Taught"):
        cleaned = re.sub(r'^Courses Taught[^•]*•?\s*', '', cleaned)

    matches = list(COURSE_CODE_RE.finditer(cleaned))
    if not matches:
        return []

    results = []
    for i, match in enumerate(matches):
        prefix, number = match.group(1), match.group(2)
        code = normalize_course_code(prefix, number)

        # Extract name: text between end of this code and start of next code
        name_start = match.end()
        name_end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        raw_name = cleaned[name_start:name_end].strip()

        # Clean separators and trim
        raw_name = re.sub(r'^[\s:\-–—]+', '', raw_name).strip()
        raw_name = re.sub(r'[\s,;]+$', '', raw_name).strip()

        # Remove trailing bullet markers, semester info, year info
        raw_name = re.sub(r',?\s*(?:Fall|Spring|Summer)\s+\d{4}.*$', '', raw_name).strip()
        raw_name = re.sub(r'\s*•\s*$', '', raw_name).strip()

        if not raw_name:
            raw_name = ""

        results.append({"code": code, "name": raw_name})

    return results


def parse_education(text: str) -> list[str]:
    """Parse education string into a list of individual degrees."""
    if not text or not text.strip():
        return []
    parts = re.split(r'\s+(?=(?:PhD|MS|MA|MBA|BS|BA|BE|BBA|JD|Other|MFA|MEng)\s*\()', text.strip())
    return [p.strip() for p in parts if p.strip()]


def read_faculty_csvs() -> list[dict]:
    """Read all faculty CSVs and return normalized faculty records."""
    all_faculty = []

    for school_name, csv_path in FACULTY_CSVS:
        if not csv_path.exists():
            print(f"WARNING: {csv_path} not found, skipping")
            continue

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("Name", "").strip()
                if not name:
                    continue

                courses_raw = row.get("Courses", "").strip()
                parsed_courses = parse_courses_text(courses_raw)

                faculty = {
                    "name": name,
                    "school": school_name,
                    "title": row.get("Title", "").strip() or None,
                    "profile_url": row.get("Profile URL", "").strip() or None,
                    "address": row.get("Address", "").strip() or None,
                    "phone": row.get("Phone", "").strip() or None,
                    "email": row.get("Email", "").strip() or None,
                    "website": row.get("Website", "").strip() or None,
                    "education": parse_education(row.get("Education", "")),
                    "research_summary": row.get("Research", "").strip() or None,
                    "general_info": row.get("General Information", "").strip() or None,
                    "experience": row.get("Experience", "").strip() or None,
                    "courses_raw": courses_raw or None,
                    "courses_parsed": parsed_courses,
                    "course_codes": [c["code"] for c in parsed_courses],
                    "honors_awards": row.get("Honors and Awards", "").strip() or None,
                    "grants_funds": row.get("Grants, Contracts and Funds", "").strip() or None,
                    "professional_societies": row.get("Professional Societies", "").strip() or None,
                    "appointments": row.get("Appointments", "").strip() or None,
                }
                all_faculty.append(faculty)

    return all_faculty


def classify_course_level(course_number_str: str | None) -> str:
    """Classify a course as undergraduate or graduate based on its number.
    Stevens convention: < 500 = undergraduate, >= 500 = graduate."""
    if not course_number_str:
        return "unknown"
    try:
        num = float(course_number_str)
        return "undergraduate" if num < 500 else "graduate"
    except (ValueError, TypeError):
        return "unknown"


def read_courses_csv() -> list[dict]:
    """Read the courses CSV and return normalized course records."""
    courses = []
    if not COURSE_CSV.exists():
        print(f"WARNING: {COURSE_CSV} not found")
        return courses

    with open(COURSE_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("Course Code", "").strip()
            if not code:
                continue
            course_number = row.get("Course Number", "").strip() or None
            courses.append({
                "course_code": code,
                "course_title": row.get("Course Title", "").strip(),
                "course_url": row.get("Course URL", "").strip() or None,
                "course_number": course_number,
                "course_level": classify_course_level(course_number),
                "course_description": row.get("Course Description", "").strip() or None,
                "credits": row.get("Credits", "").strip() or None,
                "prerequisite": row.get("Course Prerequisite", "").strip() or None,
                "branch": row.get("Course Branch", "").strip() or None,
                "offered_semester": row.get("Offered Semester", "").strip() or None,
            })

    return courses


def build_faculty_course_mapping(
    faculty_list: list[dict],
    course_lookup: dict[str, dict],
) -> list[dict]:
    """
    Build the critical faculty-course mapping table.
    Returns one record per (professor, course) pair.
    """
    mapping = []
    for fac in faculty_list:
        for parsed in fac["courses_parsed"]:
            code = parsed["code"]
            course_name_from_faculty = parsed["name"]

            # Try to find this course in the courses CSV
            course_info = course_lookup.get(code, {})
            course_name = (
                course_info.get("course_title")
                or course_name_from_faculty
                or code
            )

            mapping.append({
                "professor_name": fac["name"],
                "professor_email": fac["email"],
                "professor_phone": fac["phone"],
                "professor_profile_url": fac["profile_url"],
                "school": fac["school"],
                "course_code": code,
                "course_name": course_name,
                "course_level": course_info.get("course_level", classify_course_level(
                    course_info.get("course_number")
                )),
                "course_url": course_info.get("course_url"),
                "credits": course_info.get("credits"),
                "prerequisite": course_info.get("prerequisite"),
            })

    return mapping


def build_course_to_professors(mapping: list[dict]) -> dict[str, list[str]]:
    """Invert the mapping: course_code -> list of professor names."""
    c2p = defaultdict(list)
    for entry in mapping:
        c2p[entry["course_code"]].append(entry["professor_name"])
    return dict(c2p)


def build_enriched_courses(
    courses: list[dict],
    course_to_professors: dict[str, list[str]],
) -> list[dict]:
    """Enrich course records with professor info."""
    enriched = []
    for course in courses:
        code = course["course_code"]
        professors = course_to_professors.get(code, [])

        enriched_course = dict(course)
        enriched_course["professors"] = professors
        enriched_course["professor_count"] = len(professors)
        enriched.append(enriched_course)

    return enriched


def build_structured_profiles(faculty_list: list[dict]) -> list[dict]:
    """Build clean structured profiles (trim huge text fields for embedding)."""
    profiles = []
    for fac in faculty_list:
        bio = fac.get("general_info") or ""
        if len(bio) > 600:
            bio = bio[:600].rsplit(" ", 1)[0] + "..."

        profile = {
            "doc_type": "faculty_profile",
            "name": fac["name"],
            "school": fac["school"],
            "title": fac["title"],
            "email": fac["email"],
            "phone": fac["phone"],
            "profile_url": fac["profile_url"],
            "address": fac["address"],
            "education": fac["education"],
            "courses_taught": fac["course_codes"],
            "bio": bio if bio else None,
            "experience": _trim(fac.get("experience"), 400),
            "appointments": fac.get("appointments"),
        }
        profiles.append(profile)

    return profiles


def build_faculty_research(faculty_list: list[dict]) -> list[dict]:
    """Build focused research documents per professor."""
    research_docs = []
    for fac in faculty_list:
        research = fac.get("research_summary")
        if not research:
            continue

        doc = {
            "doc_type": "faculty_research",
            "name": fac["name"],
            "school": fac["school"],
            "email": fac["email"],
            "profile_url": fac["profile_url"],
            "research_summary": _trim(research, 800),
            "honors_awards": _trim(fac.get("honors_awards"), 500),
            "grants_funds": _trim(fac.get("grants_funds"), 500),
            "courses_taught": fac["course_codes"],
        }
        research_docs.append(doc)

    return research_docs


def _trim(text: str | None, max_len: int) -> str | None:
    if not text:
        return None
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def write_json(data, filename: str):
    out_path = SCRIPT_DIR / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {out_path.name}: {len(data)} records")


def print_stats(
    faculty_list, mapping, enriched_courses, profiles, research_docs
):
    print("\n=== STATISTICS ===")
    print(f"Total faculty parsed:            {len(faculty_list)}")
    faculty_with_courses = sum(1 for f in faculty_list if f["course_codes"])
    print(f"Faculty with courses:            {faculty_with_courses}")
    total_pairs = len(mapping)
    print(f"Faculty-course pairs:            {total_pairs}")

    courses_with_prof = sum(
        1 for c in enriched_courses if c["professors"]
    )
    print(f"Courses with professor assigned: {courses_with_prof}/{len(enriched_courses)}")
    print(f"Faculty profiles:                {len(profiles)}")
    print(f"Faculty research docs:           {len(research_docs)}")

    # Show sample mappings
    print("\n=== SAMPLE FACULTY-COURSE MAPPINGS ===")
    for entry in mapping[:10]:
        print(f"  {entry['professor_name']:30s} -> {entry['course_code']:10s} {entry['course_name'][:50]}")

    # Show courses that now have professors
    print("\n=== SAMPLE ENRICHED COURSES ===")
    shown = 0
    for c in enriched_courses:
        if c["professors"] and shown < 8:
            print(f"  {c['course_code']:10s} {c['course_title'][:40]:40s} -> {', '.join(c['professors'])}")
            shown += 1


def main():
    print("=" * 60)
    print("STEP 4.1 — Restructure Data for Optimized Retrieval")
    print("=" * 60)

    # 1. Read raw data
    print("\n[1/5] Reading faculty CSVs...")
    faculty_list = read_faculty_csvs()
    print(f"  Loaded {len(faculty_list)} faculty records from {len(FACULTY_CSVS)} schools")

    print("\n[2/5] Reading courses CSV...")
    courses = read_courses_csv()
    print(f"  Loaded {len(courses)} course records")
    course_lookup = {c["course_code"]: c for c in courses}

    # 2. Build mapping
    print("\n[3/5] Building faculty-course mapping...")
    mapping = build_faculty_course_mapping(faculty_list, course_lookup)
    course_to_professors = build_course_to_professors(mapping)
    print(f"  Built {len(mapping)} faculty-course pairs")
    print(f"  Unique courses with professors: {len(course_to_professors)}")

    # 3. Build outputs
    print("\n[4/5] Building output documents...")
    profiles = build_structured_profiles(faculty_list)
    research_docs = build_faculty_research(faculty_list)
    enriched_courses = build_enriched_courses(courses, course_to_professors)

    # 4. Write outputs
    print("\n[5/5] Writing JSON files...")
    write_json(profiles, "structured_faculty_profiles.json")
    write_json(mapping, "faculty_course_mapping.json")
    write_json(enriched_courses, "enriched_courses.json")
    write_json(research_docs, "faculty_research.json")

    # Stats
    print_stats(faculty_list, mapping, enriched_courses, profiles, research_docs)

    print("\n" + "=" * 60)
    print("Done! All files written to:", SCRIPT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
