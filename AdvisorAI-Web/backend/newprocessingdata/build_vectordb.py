#!/usr/bin/env python3
"""
Build ChromaDB vector collections from the structured JSON files
produced by restructure_data.py.

Key improvements over the old create_chroma_collections.py:
  - Rich, filterable metadata on every document (professor name,
    course code, doc_type, school, etc.)
  - Embedding text is crafted per doc_type so the vector captures
    the right semantics (not a 3000-char blob)
  - Separate doc_types allow metadata-filtered retrieval

Run from the backend/ directory:
    python newprocessingdata/build_vectordb.py
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

INPUT_DIR = SCRIPT_DIR                       # structured JSONs live here
OUTPUT_DIR = BACKEND_DIR / os.getenv("VECTORDB_DIR", "./VectorDB_v2").lstrip("./")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


# ── helpers ───────────────────────────────────────────────────────────

def _safe(val: Any) -> str:
    """Coerce a value to a non-empty string for ChromaDB metadata."""
    if val is None:
        return ""
    if isinstance(val, list):
        return ", ".join(str(v) for v in val) if val else ""
    return str(val).strip()


def _normalize_code(code: str) -> str:
    """'FE 621' -> 'FE621' (no space, for substring matching)."""
    return code.replace(" ", "").replace("-", "").upper()


# ── document builders ────────────────────────────────────────────────

def build_faculty_profile_docs(profiles: list[dict]) -> list[Document]:
    """
    One document per professor.
    Embedding text is a concise profile paragraph (not a raw blob).
    """
    docs = []
    for p in profiles:
        name = p["name"]
        school = p.get("school", "")
        courses = p.get("courses_taught", [])

        # Build embedding text: concise, query-matchable
        parts = [f"Professor {name}"]
        if school:
            parts.append(f"School: {school}")
        if p.get("title"):
            parts.append(f"Title: {p['title']}")
        if p.get("email"):
            parts.append(f"Email: {p['email']}")
        if p.get("phone"):
            parts.append(f"Phone: {p['phone']}")
        if p.get("address"):
            parts.append(f"Office: {p['address']}")
        if p.get("education"):
            parts.append("Education: " + "; ".join(p["education"]))
        if courses:
            parts.append("Courses taught: " + ", ".join(courses))
        if p.get("bio"):
            parts.append(p["bio"])
        if p.get("experience"):
            parts.append(f"Experience: {p['experience']}")

        text = "\n".join(parts)

        metadata = {
            "doc_type": "faculty_profile",
            "professor_name": name,
            "professor_name_lower": name.lower(),
            "school": _safe(school),
            "email": _safe(p.get("email")),
            "phone": _safe(p.get("phone")),
            "profile_url": _safe(p.get("profile_url")),
            "courses_taught": _safe(courses),
            "course_count": len(courses),
        }

        docs.append(Document(page_content=text, metadata=metadata))

    return docs


def build_faculty_course_mapping_docs(mappings: list[dict]) -> list[Document]:
    """
    One document per (professor, course) pair.
    This is the critical doc_type that answers "Who teaches X?" and
    "What courses does professor Y teach?"
    """
    docs = []
    for m in mappings:
        name = m["professor_name"]
        code = m["course_code"]
        course_name = m.get("course_name", "")

        course_level = m.get("course_level", "unknown")

        text = (
            f"Professor {name} teaches {code} {course_name}. "
            f"Contact: {m.get('professor_email', 'N/A')}. "
            f"School: {m.get('school', 'N/A')}. "
            f"Level: {course_level}."
        )
        if m.get("credits"):
            text += f" Credits: {m['credits']}."
        if m.get("prerequisite"):
            text += f" Prerequisite: {m['prerequisite']}."

        metadata = {
            "doc_type": "faculty_course_mapping",
            "professor_name": name,
            "professor_name_lower": name.lower(),
            "course_code": code,
            "course_code_normalized": _normalize_code(code),
            "course_name": _safe(course_name),
            "course_level": course_level,
            "school": _safe(m.get("school")),
            "email": _safe(m.get("professor_email")),
            "credits": _safe(m.get("credits")),
        }

        docs.append(Document(page_content=text, metadata=metadata))

    return docs


def build_course_docs(courses: list[dict]) -> list[Document]:
    """
    One document per course, enriched with professor info.
    """
    docs = []
    for c in courses:
        code = c["course_code"]
        title = c.get("course_title", "")
        professors = c.get("professors", [])
        course_level = c.get("course_level", "unknown")

        parts = [f"Course {code}: {title} ({course_level} level)"]
        if professors:
            parts.append(f"Taught by: {', '.join(professors)}")
        else:
            parts.append("Professor: Not yet assigned in our records")
        if c.get("credits"):
            parts.append(f"Credits: {c['credits']}")
        if c.get("prerequisite"):
            parts.append(f"Prerequisites: {c['prerequisite']}")
        if c.get("offered_semester"):
            parts.append(f"Offered: {c['offered_semester']}")
        if c.get("course_description"):
            desc = c["course_description"]
            if len(desc) > 600:
                desc = desc[:600].rsplit(" ", 1)[0] + "..."
            parts.append(f"Description: {desc}")

        text = "\n".join(parts)

        metadata = {
            "doc_type": "course",
            "course_code": code,
            "course_code_normalized": _normalize_code(code),
            "course_title": _safe(title),
            "course_level": course_level,
            "credits": _safe(c.get("credits")),
            "professors": _safe(professors),
            "professor_count": len(professors),
            "has_professor": len(professors) > 0,
            "prerequisite": _safe(c.get("prerequisite")),
            "offered_semester": _safe(c.get("offered_semester")),
            "course_url": _safe(c.get("course_url")),
        }

        docs.append(Document(page_content=text, metadata=metadata))

    return docs


def build_research_docs(research_list: list[dict]) -> list[Document]:
    """
    One document per professor's research profile.
    """
    docs = []
    for r in research_list:
        name = r["name"]

        parts = [f"Professor {name} - Research"]
        if r.get("school"):
            parts.append(f"School: {r['school']}")
        if r.get("research_summary"):
            parts.append(f"Research areas: {r['research_summary']}")
        if r.get("honors_awards"):
            parts.append(f"Honors & Awards: {r['honors_awards']}")
        if r.get("grants_funds"):
            parts.append(f"Grants & Funding: {r['grants_funds']}")
        if r.get("courses_taught"):
            parts.append(f"Courses: {', '.join(r['courses_taught'])}")

        text = "\n".join(parts)

        metadata = {
            "doc_type": "faculty_research",
            "professor_name": name,
            "professor_name_lower": name.lower(),
            "school": _safe(r.get("school")),
            "email": _safe(r.get("email")),
            "profile_url": _safe(r.get("profile_url")),
            "courses_taught": _safe(r.get("courses_taught")),
        }

        docs.append(Document(page_content=text, metadata=metadata))

    return docs


# ── collection builder ────────────────────────────────────────────────

def build_collection(
    collection_name: str,
    documents: list[Document],
    embedding_model: HuggingFaceEmbeddings,
    output_dir: Path,
) -> int:
    """Create (or replace) a single Chroma collection. Returns doc count."""
    collection_path = output_dir / collection_name

    if collection_path.exists():
        print(f"  Removing existing {collection_name}...")
        shutil.rmtree(collection_path)

    print(f"  Embedding {len(documents)} documents for '{collection_name}'...")
    Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        collection_name=collection_name,
        persist_directory=str(collection_path),
    )

    return len(documents)


# ── main ──────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("STEP 4.2 — Build ChromaDB with Rich Metadata")
    print("=" * 60)

    # Load structured data
    print("\n[1/4] Loading structured JSON files...")

    with open(INPUT_DIR / "structured_faculty_profiles.json") as f:
        profiles = json.load(f)
    with open(INPUT_DIR / "faculty_course_mapping.json") as f:
        mappings = json.load(f)
    with open(INPUT_DIR / "enriched_courses.json") as f:
        courses = json.load(f)
    with open(INPUT_DIR / "faculty_research.json") as f:
        research = json.load(f)

    print(f"  Profiles:  {len(profiles)}")
    print(f"  Mappings:  {len(mappings)}")
    print(f"  Courses:   {len(courses)}")
    print(f"  Research:  {len(research)}")

    # Build documents
    print("\n[2/4] Building documents with rich metadata...")
    profile_docs = build_faculty_profile_docs(profiles)
    mapping_docs = build_faculty_course_mapping_docs(mappings)
    course_docs = build_course_docs(courses)
    research_docs = build_research_docs(research)

    all_docs = profile_docs + mapping_docs + course_docs + research_docs
    print(f"  Total documents: {len(all_docs)}")
    print(f"    faculty_profile:         {len(profile_docs)}")
    print(f"    faculty_course_mapping:  {len(mapping_docs)}")
    print(f"    course:                  {len(course_docs)}")
    print(f"    faculty_research:        {len(research_docs)}")

    # Print sample documents
    print("\n  Sample embedding texts:")
    for doc in mapping_docs[:2]:
        print(f"    [{doc.metadata['doc_type']}] {doc.page_content[:120]}...")
    for doc in course_docs[:2]:
        lines = doc.page_content.split("\n")
        print(f"    [{doc.metadata['doc_type']}] {lines[0]}")
        if len(lines) > 1:
            print(f"      {lines[1]}")

    # Initialize embedding model
    print(f"\n[3/4] Loading embedding model: {EMBEDDING_MODEL}")
    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # Build collections
    print(f"\n[4/4] Building ChromaDB collections in {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    collections = {
        "AllFacultyProfiles": profile_docs,
        "FacultyCourseMapping": mapping_docs,
        "AllCourseData": course_docs,
        "AllFacultyResearch": research_docs,
    }

    total = 0
    for name, docs in collections.items():
        count = build_collection(name, docs, embedding_model, OUTPUT_DIR)
        total += count

    # Summary
    print("\n" + "=" * 60)
    print(f"SUCCESS — {total} documents across {len(collections)} collections")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    for name, docs in collections.items():
        print(f"  {name:30s}  {len(docs):5d} docs")

    # Show metadata sample
    print("\n=== SAMPLE METADATA (faculty_course_mapping) ===")
    for doc in mapping_docs[:3]:
        print(f"  {doc.metadata}")

    print("\n=== SAMPLE METADATA (course) ===")
    for doc in course_docs[:3]:
        m = doc.metadata
        print(f"  code={m['course_code']} profs={m['professors'][:50]} has_prof={m['has_professor']}")

    print("\n" + "=" * 60)
    print("Done! Update VECTORDB_DIR in .env to point to VectorDB_v2")
    print("=" * 60)


if __name__ == "__main__":
    main()
