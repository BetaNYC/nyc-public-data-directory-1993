#!/usr/bin/env python3
"""Parse the 1993 NYC Public Data Directory (OCR text layer) into structured records.

Input: source/1993-NYC-Public-Data-Directory.pdf (embedded OCR text layer)
Output: data/public-data-directory-1993.json + data/public-data-directory-1993-applications.csv

Usage: uv run --with pypdf scripts/parse_directory.py   (from the repo root)
"""
import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PDF = REPO / "source" / "1993-NYC-Public-Data-Directory.pdf"
DATA_DIR = REPO / "data"

# --- fuzzy label regexes (OCR swaps I -> Z/X, M -> K/H) ---
L_APP_NAME = re.compile(r"^APPL[IZX]CAT[IZX]ON\s+NA[MK]E\s*:?\s*(.*)$", re.I)
L_YEAR = re.compile(r"^YEAR\s+ACT[IZX]?VATED?\s*:?\s*(.*)$|^YEAR ACT:\s*(.*)$", re.I)
L_DESC = re.compile(r"^APPL[IZX]CAT[IZX]ON\s+DESCR[IZX]PT[IZX]ON\s*:?\s*(.*)$", re.I)
L_CONTENTS = re.compile(r"^DATABASE\s+CONTENTS\s*:?\s*I?\s*(.*)$", re.I)
L_STATUS = re.compile(r"^STATUS\s*:\s*(.*)$", re.I)
L_CONF = re.compile(r"^CONF[IZX]DENT[IZX]AL(?:[IZX]TY)?\s*(?:REQU[IZX]REMENTS|PROV[IZX]S[IZX]ONS)\s*:?\s*(.*)$", re.I)
L_METHOD = re.compile(r"^METHOD\s+OF\s+ACCESS\s*:?\s*(.*)$", re.I)
L_BUREAU = re.compile(r"^User\s+Bureau\s*:?\s*(.*)$", re.I)

APP_HEADER = re.compile(r"AGENCY\s*:\s*'?\s*(.+?)\s+Pa[gq]e\s+(\d+)\s+of\s+(\d+)", re.I)
BOX_LINE = re.compile(r"^[1IJl|]?[-~_=\s]{10,}[1IJl|]?$")
PAGE_NUM = re.compile(r"^\s*(\d{1,3}|[ivxlc]+)\s*$", re.I)
PHONE = re.compile(r"\d{3}[-.\s]\d{3}[-.\s]\d{4}")
PHONE_ARTIFACT = re.compile(r"^[I1l|\"'\s]*(PHONE|FAX)\s*:?\s*$", re.I)


def load_pages():
    from pypdf import PdfReader
    reader = PdfReader(PDF)
    return [(i, p.extract_text() or "") for i, p in enumerate(reader.pages)]


def classify(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if any(l == "AGENCY" for l in lines[:3]) and "PUBLIC LIAISON" in text:
        return "profile", None
    if re.search(r"AGENCY\s*:", text[:400]):
        return "applications", None
    return "other", None


def parse_profile(pdf_page, text):
    lines = [l.rstrip() for l in text.splitlines()]
    lines = [l for l in lines if l.strip()]
    # agency name = first line(s) after 'AGENCY' until an address-looking line
    try:
        i = next(k for k, l in enumerate(lines) if l.strip() == "AGENCY")
    except StopIteration:
        i = -1
    name_lines, addr_lines = [], []
    in_addr = False
    j = i + 1
    while j < len(lines) and lines[j].strip() != "PUBLIC LIAISON":
        s = lines[j].strip()
        if PHONE_ARTIFACT.match(s) or PHONE.fullmatch(s):
            j += 1
            continue
        if re.search(r"\d", s) or re.search(r"(?i)\b(street|plaza|broadway|avenue|blvd|centre)\b", s):
            in_addr = True
        (addr_lines if in_addr else name_lines).append(s)
        j += 1
    # liaison block
    liaison_name = liaison_title = None
    k = j + 1
    liaison_lines = []
    while k < len(lines) and lines[k].strip() != "MISSION STATEMENT":
        s = lines[k].strip()
        if not PHONE_ARTIFACT.match(s) and not PHONE.fullmatch(s):
            liaison_lines.append(s)
        k += 1
    if liaison_lines:
        liaison_name = liaison_lines[0]
        if len(liaison_lines) > 1:
            liaison_title = " ".join(liaison_lines[1:])
    # mission = everything after MISSION STATEMENT minus artifacts and page number
    mission_lines = []
    for l in lines[k + 1:]:
        s = l.strip()
        if PHONE_ARTIFACT.match(s) or PHONE.fullmatch(s) or PAGE_NUM.match(s):
            continue
        mission_lines.append(s)
    phones = PHONE.findall(text)
    return {
        "agency_name": " ".join(name_lines).strip() or None,
        "address": ", ".join(addr_lines).strip() or None,
        "public_liaison": liaison_name,
        "liaison_title": liaison_title,
        "phone_numbers": phones,
        "mission_statement": " ".join(mission_lines).strip() or None,
        "pdf_page": pdf_page + 1,  # 1-indexed
        "applications": [],
    }


def clean_app_page(text):
    """Strip box borders, the AGENCY:...Page header, and trailing page numbers."""
    out = []
    for l in text.splitlines():
        s = l.strip()
        # strip box-border runs glued onto the line
        s = re.sub(r"^[1IJl|]?\s*[-~_=]{5,}\s*[1IJl|]?", "", s).strip()
        if not s:
            continue
        if BOX_LINE.match(s):
            continue
        if re.match(r"^[1IJl|]?\s*AGENCY\s*:", s):
            continue
        if re.fullmatch(r"Pa[gq]e\s+\d+\s+of\s+\d+\s*[1IJl|]?", s, re.I):
            continue
        if PAGE_NUM.match(s):
            continue
        out.append(s)
    return out


FIELD_ORDER = [
    ("user_bureau", L_BUREAU),
    ("application_name", L_APP_NAME),
    ("year_activated", L_YEAR),
    ("application_description", L_DESC),
    ("database_contents", L_CONTENTS),
    ("status", L_STATUS),
    ("confidentiality", L_CONF),
    ("method_of_access", L_METHOD),
]


def parse_applications(lines_with_pages):
    """lines_with_pages: list of (pdf_page, line). Returns list of records."""
    records = []
    cur = None
    cur_field = None
    pending_bureau = None
    pending_bureau_page = None

    def flush():
        nonlocal cur, cur_field
        if cur and cur.get("application_name"):
            for k, v in list(cur.items()):
                if isinstance(v, list):
                    cur[k] = " ".join(x for x in v if x).strip() or None
            records.append(cur)
        cur, cur_field = None, None

    for pdf_page, line in lines_with_pages:
        m = L_BUREAU.match(line)
        if m:
            # bureau precedes a new record
            flush()
            pending_bureau = m.group(1).strip() or None
            pending_bureau_page = pdf_page
            continue
        m = L_APP_NAME.match(line)
        if m:
            flush()
            cur = {
                "user_bureau": pending_bureau,
                "application_name": [m.group(1).strip()],
                "year_activated": None,
                "application_description": None,
                "database_contents": None,
                "status": None,
                "confidentiality": None,
                "method_of_access": None,
                "pdf_page": (pending_bureau_page or pdf_page) + 1,
            }
            cur_field = "application_name"
            pending_bureau = pending_bureau_page = None
            continue
        if cur is None:
            continue
        matched = False
        for field, rx in FIELD_ORDER[2:]:
            m = rx.match(line)
            if m:
                val = next((g for g in m.groups() if g is not None), "").strip()
                cur[field] = [val] if val else []
                cur_field = field
                matched = True
                break
        if matched:
            continue
        # column-scrambled layout: empty NAME label then empty YEAR label,
        # followed by the name value line then the year value line
        if (cur_field == "year_activated"
                and isinstance(cur["application_name"], list)
                and not any(cur["application_name"])
                and not cur["year_activated"]):
            cur["application_name"] = [line]
            continue
        if cur_field:
            if not isinstance(cur[cur_field], list):
                cur[cur_field] = [cur[cur_field]] if cur[cur_field] else []
            cur[cur_field].append(line)
    flush()
    return records


def main():
    pages = load_pages()
    agencies = []
    current = None
    app_buffer = []  # (pdf_page, line) for current agency

    def close_agency():
        nonlocal app_buffer
        if current is not None and app_buffer:
            current["applications"] = parse_applications(app_buffer)
        app_buffer = []

    for idx, text in pages:
        kind, m = classify(text)
        if kind == "profile":
            close_agency()
            current = parse_profile(idx, text)
            agencies.append(current)
        elif kind == "applications" and current is not None:
            for l in clean_app_page(text):
                app_buffer.append((idx, l))
    close_agency()

    n_apps = sum(len(a["applications"]) for a in agencies)
    doc = {
        "title": "Public Data Directory, First Edition",
        "publisher": "New York City Commission on Public Information and Communication (COPIC), Office of the Mayor / Office of Operations",
        "published": "1993-04",
        "authority": "NYC Charter § 1062",
        "source_pdf": "18121479-1993-NYC-Public-Data-Directory.pdf (Google Drive ID 0B98QOZfGax93SU1VcFNaUUhKVnM)",
        "extraction_note": "Parsed from the PDF's embedded OCR text layer (pypdf). OCR errors from the 1993 typescript scan are preserved as-is in field values; labels were fuzzy-matched. Verify critical values against the PDF page cited in pdf_page.",
        "agency_count": len(agencies),
        "application_count": n_apps,
        "agencies": agencies,
    }
    out = DATA_DIR / "public-data-directory-1993.json"
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"agencies: {len(agencies)}, applications: {n_apps}")
    for a in agencies:
        print(f"  p{a['pdf_page']:>3}  {a['agency_name']}: {len(a['applications'])} apps")

    # flat CSV
    csv_path = DATA_DIR / "public-data-directory-1993-applications.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["agency", "user_bureau", "application_name", "year_activated",
                    "application_description", "database_contents", "status",
                    "confidentiality", "method_of_access", "pdf_page"])
        for a in agencies:
            for r in a["applications"]:
                w.writerow([a["agency_name"], r["user_bureau"], r["application_name"],
                            r["year_activated"], r["application_description"],
                            r["database_contents"], r["status"], r["confidentiality"],
                            r["method_of_access"], r["pdf_page"]])
    print("wrote", out.name, "and", csv_path.name)


if __name__ == "__main__":
    main()
