#!/usr/bin/env python3
"""
Step 1: Clean, deduplicate, and categorize all Stevens context data.

Sources:
  1. Scraped web pages (from stevens_qa_finetuning.jsonl — extract unique contexts)
  2. Structured course catalog (CSV)
  3. Faculty profiles (per-school CSVs)
  4. University-wide data (UniData.json)

Output:
  output/clean_contexts.json — list of {id, category, source, text, metadata}

Run:
  python 01_clean_and_categorize.py
"""

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from config import (
    CLEAN_CONTEXTS_PATH,
    COURSE_CSV,
    FACULTY_SCHOOLS,
    MIN_CONTEXT_LENGTH,
    OUTPUT_DIR,
    PDF_ARTIFACT_PATTERN,
    RAW_JSONL,
    UNIDATA_JSON,
)

# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def ctx_id(text: str) -> str:
    """Deterministic short hash for a context string."""
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def clean_html_artifacts(text: str) -> str:
    """Remove common HTML/encoding artifacts from scraped text."""
    text = text.replace("\u00a0", " ")       # non-breaking space
    text = text.replace("\xa0", " ")
    text = re.sub(r"<[^>]+>", " ", text)     # stray HTML tags
    text = re.sub(r"\s{3,}", "  ", text)     # collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse excessive newlines
    return text.strip()


def extract_url_and_title(ctx: str):
    """Parse the 'URL: ... Title: ...' prefix from scraped contexts."""
    url, title, body = "", "", ctx

    url_match = re.match(r"^URL:\s*(\S+)", ctx)
    if url_match:
        url = url_match.group(1)
        body = ctx[url_match.end():].strip()

    title_match = re.match(r"^Title:\s*(.+?)(?:\s{2,}|\n)", body)
    if title_match:
        title = title_match.group(1).strip()
        body = body[title_match.end():].strip()

    return url, title, body


def categorize_url_context(url: str, title: str, body: str) -> str:
    """Rule-based category assignment for a URL-based context.

    Priority: URL path/netloc rules first (high confidence), then
    body-keyword rules (lower confidence, more ambiguous).
    """
    path = urlparse(url).path.lower() if url else ""
    netloc = urlparse(url).netloc.lower() if url else ""

    # ── High-confidence: URL structure ──
    if any(k in path for k in ["/program/", "/programs/", "/certificate/", "/graduate-programs/", "/undergraduate-programs/"]):
        return "program"
    if "/courses/" in path:
        return "course"
    if "/news/" in path or "/event" in path:
        return "news"
    if "gradadmission" in netloc or "undergradadmission" in netloc or "/admission" in path:
        return "admissions"
    if "ducklink" in netloc:
        return "campus_life"
    if "library" in netloc or "library" in path:
        return "library"
    if "fsc" in netloc:
        return "financial"
    if "support" in netloc:
        return "campus_life"
    if "/profile/" in path or "/faculty" in path:
        return "faculty"

    # ── Lower-confidence: body keywords ──
    combined = (title + " " + body[:2000]).lower()

    if any(k in combined for k in ["admission", "apply now", "application deadline"]):
        return "admissions"
    if any(k in combined for k in ["tuition", "scholarship", "financial aid", "cost of attendance"]):
        return "financial"
    if any(k in combined for k in ["faculty", "professor", "ph.d", "research interests"]):
        return "faculty"
    if any(k in combined for k in [
        "master's program", "bachelor's program", "degree program",
        "concentration", "curriculum requirements",
    ]):
        return "program"
    if any(k in combined for k in [
        "course", "credits", "prerequisite", "syllabus",
    ]):
        return "course"
    if any(k in combined for k in [
        "housing", "dining", "campus life", "student club",
        "organization", "career services", "counseling",
    ]):
        return "campus_life"

    return "general"


def has_pdf_artifacts(text: str) -> bool:
    """Check if text has (cid:XX) encoding artifacts from PDF extraction."""
    return bool(re.search(PDF_ARTIFACT_PATTERN, text))


def is_duplicate_archive(url: str, seen_base_urls: dict) -> bool:
    """Detect duplicate catalog archive pages (keep most recent year only)."""
    match = re.search(r"/catalog/archive/(\d{4}-\d{4})/", url)
    if not match:
        return False
    year = match.group(1)
    base = re.sub(r"/catalog/archive/\d{4}-\d{4}/", "/catalog/archive/YEAR/", url)
    if base in seen_base_urls:
        if year > seen_base_urls[base]:
            seen_base_urls[base] = year
            return False  # this one is newer, keep it (old one was already added but we'll dedup later)
        return True  # older duplicate
    seen_base_urls[base] = year
    return False


# ═══════════════════════════════════════════════════════════════════════
# Source 1: Scraped web pages from existing JSONL
# ═══════════════════════════════════════════════════════════════════════


def load_scraped_contexts() -> list[dict]:
    """Extract unique URL-based contexts from the JSONL, clean and categorize."""
    print(f"Loading scraped contexts from {RAW_JSONL}...")

    seen_texts = set()
    seen_base_urls = {}
    contexts = []
    skipped = Counter()

    with open(RAW_JSONL, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line.strip())
            raw_ctx = row["context"]

            if raw_ctx in seen_texts:
                continue
            seen_texts.add(raw_ctx)

            # Skip non-URL contexts (PDF extractions with artifacts)
            if not raw_ctx.startswith("URL:"):
                if has_pdf_artifacts(raw_ctx):
                    skipped["pdf_artifact"] += 1
                    continue
                # Non-URL but clean — still might be useful, but low quality
                if len(raw_ctx) < MIN_CONTEXT_LENGTH:
                    skipped["too_short_nonurl"] += 1
                    continue
                # Keep clean non-URL contexts with a general category
                body = clean_html_artifacts(raw_ctx)
                contexts.append({
                    "id": ctx_id(body),
                    "category": "general",
                    "source": "scraped_nonurl",
                    "text": body,
                    "metadata": {},
                })
                continue

            url, title, body = extract_url_and_title(raw_ctx)
            body = clean_html_artifacts(body)

            if len(body) < MIN_CONTEXT_LENGTH:
                skipped["too_short"] += 1
                continue

            if has_pdf_artifacts(body):
                skipped["pdf_artifact_url"] += 1
                continue

            if is_duplicate_archive(url, seen_base_urls):
                skipped["duplicate_archive"] += 1
                continue

            category = categorize_url_context(url, title, body)

            contexts.append({
                "id": ctx_id(body),
                "category": category,
                "source": "scraped_url",
                "text": body,
                "metadata": {"url": url, "title": title},
            })

    print(f"  Extracted {len(contexts)} unique contexts")
    print(f"  Skipped: {dict(skipped)}")
    return contexts


# ═══════════════════════════════════════════════════════════════════════
# Source 2: Structured course catalog
# ═══════════════════════════════════════════════════════════════════════


def load_structured_courses() -> list[dict]:
    """Create clean contexts from the structured course CSV."""
    print(f"Loading structured courses from {COURSE_CSV}...")

    contexts = []
    with open(COURSE_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row.get("Course Code", "").strip()
            title = row.get("Course Title", "").strip()
            desc = row.get("Course Description", "").strip()
            credits = row.get("Credits", "").strip()
            prereqs = row.get("Course Prerequisite", "").strip()
            branch = row.get("Course Branch", "").strip()
            semester = row.get("Offered Semester", "").strip()

            if not code or not desc or len(desc) < 30:
                continue

            parts = [f"Course: {code} — {title}"]
            if branch:
                parts.append(f"Department: {branch}")
            parts.append(f"Credits: {credits}" if credits else "Credits: N/A")
            parts.append(f"Description: {desc}")
            if prereqs and prereqs.lower() not in ("n/a", "not available on this page structure", ""):
                parts.append(f"Prerequisites: {prereqs}")
            if semester:
                parts.append(f"Offered: {semester}")

            text = "\n".join(parts)
            contexts.append({
                "id": f"course_{code.replace(' ', '_')}",
                "category": "course",
                "source": "structured_csv",
                "text": text,
                "metadata": {
                    "course_code": code,
                    "course_title": title,
                    "credits": credits,
                    "url": row.get("Course URL", ""),
                },
            })

    print(f"  Loaded {len(contexts)} courses")
    return contexts


# ═══════════════════════════════════════════════════════════════════════
# Source 3: Faculty profiles
# ═══════════════════════════════════════════════════════════════════════


def load_faculty_profiles() -> list[dict]:
    """Create clean contexts from per-school faculty CSVs."""
    print("Loading faculty profiles...")

    KEY_FIELDS = [
        "Education", "Research", "General Information", "Courses",
        "Experience", "Honors and Awards", "Professional Societies",
        "Institutional Service",
    ]

    contexts = []
    for school, csv_path in FACULTY_SCHOOLS.items():
        if not csv_path.exists():
            print(f"  Warning: {csv_path} not found, skipping")
            continue

        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row.get("Name", "").strip()
                if not name:
                    continue

                parts = [f"Professor: {name}"]
                parts.append(f"School: {school}")

                if row.get("Address"):
                    parts.append(f"Office: {row['Address'].strip()}")
                if row.get("Phone"):
                    parts.append(f"Phone: {row['Phone'].strip()}")
                if row.get("Email"):
                    parts.append(f"Email: {row['Email'].strip()}")
                if row.get("Profile URL"):
                    parts.append(f"Profile: {row['Profile URL'].strip()}")

                for field in KEY_FIELDS:
                    val = row.get(field, "").strip()
                    if val and len(val) > 5:
                        parts.append(f"{field}: {val[:1500]}")

                text = "\n".join(parts)
                if len(text) < MIN_CONTEXT_LENGTH:
                    continue

                contexts.append({
                    "id": f"faculty_{name.replace(' ', '_').lower()}",
                    "category": "faculty",
                    "source": "structured_csv",
                    "text": text,
                    "metadata": {
                        "name": name,
                        "school": school,
                        "email": row.get("Email", ""),
                        "url": row.get("Profile URL", ""),
                    },
                })

        print(f"  {school}: loaded {sum(1 for c in contexts if c['metadata'].get('school') == school)} faculty")

    print(f"  Total faculty: {len(contexts)}")
    return contexts


# ═══════════════════════════════════════════════════════════════════════
# Source 4: University-wide data
# ═══════════════════════════════════════════════════════════════════════


def load_university_data() -> list[dict]:
    """Create topical context chunks from the UniData.json (College Scorecard)."""
    print(f"Loading university data from {UNIDATA_JSON}...")

    with open(UNIDATA_JSON, encoding="utf-8") as f:
        raw = json.load(f)

    def val(key):
        v = raw.get(key, {})
        if isinstance(v, dict):
            return v.get("0", "")
        return v

    # Group the 25K+ fields into meaningful topical chunks
    chunks = []

    # Location & basics
    chunks.append({
        "topic": "Location & General Info",
        "text": (
            f"Stevens Institute of Technology\n"
            f"Address: {val('latest/school/address')}\n"
            f"City: {val('latest/school/city')}, State: {val('latest/school/state')}\n"
            f"ZIP: {val('latest/school/zip')}\n"
            f"Website: {val('latest/school/school_url')}\n"
            f"Main campus: {'Yes' if val('latest/school/main_campus') else 'No'}\n"
            f"Ownership: {'Private' if str(val('latest/school/ownership')) == '2' else 'Public'}\n"
            f"Accreditor: {val('latest/school/accreditor')}"
        ),
        "category": "general",
    })

    # Admissions stats
    sat_avg = val("latest/admissions/sat_scores/average/overall")
    act_avg = val("latest/admissions/act_scores/midpoint/cumulative")
    adm_rate = val("latest/admissions/admission_rate/overall")
    if sat_avg or adm_rate:
        adm_text = "Stevens Institute of Technology — Admissions Statistics\n"
        if adm_rate:
            adm_text += f"Admission Rate: {float(adm_rate)*100:.1f}%\n"
        if sat_avg:
            adm_text += f"Average SAT Score: {sat_avg}\n"
        if act_avg:
            adm_text += f"Average ACT Score: {act_avg}\n"
        chunks.append({"topic": "Admissions Stats", "text": adm_text, "category": "admissions"})

    # Cost & financial
    tuition_in = val("latest/cost/tuition/in_state")
    tuition_out = val("latest/cost/tuition/out_of_state")
    if tuition_in or tuition_out:
        cost_text = "Stevens Institute of Technology — Cost & Tuition\n"
        if tuition_in:
            cost_text += f"Tuition (in-state): ${int(float(tuition_in)):,}\n"
        if tuition_out:
            cost_text += f"Tuition (out-of-state): ${int(float(tuition_out)):,}\n"
        avg_cost = val("latest/cost/avg_net_price/overall")
        if avg_cost:
            cost_text += f"Average Net Price: ${int(float(avg_cost)):,}\n"
        chunks.append({"topic": "Cost & Tuition", "text": cost_text, "category": "financial"})

    # Student body
    size = val("latest/student/size")
    if size:
        student_text = f"Stevens Institute of Technology — Student Body\n"
        student_text += f"Total enrollment: {int(float(size)):,}\n"
        ug = val("latest/student/enrollment/undergrad_12_month")
        grad = val("latest/student/enrollment/grad_12_month")
        if ug:
            student_text += f"Undergraduate enrollment (12-month): {int(float(ug)):,}\n"
        if grad:
            student_text += f"Graduate enrollment (12-month): {int(float(grad)):,}\n"
        chunks.append({"topic": "Student Body", "text": student_text, "category": "general"})

    # Outcomes / earnings
    earn = val("latest/earnings/10_yrs_after_entry/median")
    if earn:
        outcome_text = (
            f"Stevens Institute of Technology — Outcomes\n"
            f"Median earnings 10 years after entry: ${int(float(earn)):,}\n"
        )
        completion = val("latest/completion/rate_suppressed/overall")
        if completion:
            outcome_text += f"Completion rate: {float(completion)*100:.1f}%\n"
        chunks.append({"topic": "Outcomes", "text": outcome_text, "category": "general"})

    contexts = []
    for chunk in chunks:
        if len(chunk["text"]) < 50:
            continue
        contexts.append({
            "id": f"unidata_{chunk['topic'].lower().replace(' ', '_')}",
            "category": chunk["category"],
            "source": "college_scorecard",
            "text": chunk["text"],
            "metadata": {"topic": chunk["topic"]},
        })

    print(f"  Created {len(contexts)} university data chunks")
    return contexts


# ═══════════════════════════════════════════════════════════════════════
# Deduplication
# ═══════════════════════════════════════════════════════════════════════


def deduplicate(contexts: list[dict]) -> list[dict]:
    """Remove near-duplicate contexts, preferring structured sources."""
    print("Deduplicating contexts...")

    SOURCE_PRIORITY = {"structured_csv": 0, "college_scorecard": 1, "scraped_url": 2, "scraped_nonurl": 3}
    contexts.sort(key=lambda c: SOURCE_PRIORITY.get(c["source"], 9))

    seen_ids = set()
    unique = []
    for ctx in contexts:
        if ctx["id"] in seen_ids:
            continue
        seen_ids.add(ctx["id"])
        unique.append(ctx)

    removed = len(contexts) - len(unique)
    print(f"  Removed {removed} exact duplicates, {len(unique)} remaining")
    return unique


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════


def main():
    all_contexts = []

    # Load from all sources
    all_contexts.extend(load_scraped_contexts())
    all_contexts.extend(load_structured_courses())
    all_contexts.extend(load_faculty_profiles())
    all_contexts.extend(load_university_data())

    # Deduplicate
    all_contexts = deduplicate(all_contexts)

    # Summary stats
    cat_counts = Counter(c["category"] for c in all_contexts)
    source_counts = Counter(c["source"] for c in all_contexts)

    print("\n" + "=" * 60)
    print("FINAL CLEAN CONTEXT SUMMARY")
    print("=" * 60)
    print(f"Total contexts: {len(all_contexts)}")
    print(f"\nBy category:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s}: {count:>6,}")
    print(f"\nBy source:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"  {src:20s}: {count:>6,}")

    text_lengths = [len(c["text"]) for c in all_contexts]
    print(f"\nText length stats:")
    print(f"  Min: {min(text_lengths):,}")
    print(f"  Max: {max(text_lengths):,}")
    print(f"  Mean: {sum(text_lengths) // len(text_lengths):,}")

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CLEAN_CONTEXTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_contexts, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {CLEAN_CONTEXTS_PATH}")
    print(f"File size: {CLEAN_CONTEXTS_PATH.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
