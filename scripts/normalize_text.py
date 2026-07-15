#!/usr/bin/env python3
"""Produce spell-normalized ("clean") editions of the 1993 Public Data Directory data.

Reads:  data/public-data-directory-1993.json  (verbatim OCR values)
Writes: data/public-data-directory-1993-clean.json
        data/public-data-directory-1993-applications-clean.csv

Strategy: deterministic, dictionary-checked repair of the scan's known OCR
substitutions. A token is only altered when (a) it is not already a known
word and (b) applying one or more of the substitutions below yields a word
found in the system dictionary (plus a small domain wordlist). Tokens that
cannot be confidently repaired are left verbatim. No language model, no
guessing beyond the substitution table.

Known 1993-typescript OCR substitutions:
    q -> g   (aqency -> agency)      z -> i   (applzcatzon -> application)
    x -> i   (actxvated -> activated) k -> m  (kanaqement -> management)
    h -> m   (hanagement -> management) 9 -> o (acc9unts -> accounts)
    0 -> o   1 -> l   ~ -> b (contri~utes -> contributes)
"""
import csv
import json
import itertools
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

SUBS = {"q": ("g",), "z": ("i",), "x": ("i",), "k": ("m",), "h": ("m", "b"),
        "9": ("o",), "0": ("o",), "1": ("l", "i"),
        "~": ("b", "r", "m", "s", "t", "a", "e", "n", "d", "g")}

DOMAIN_WORDS = {
    "citywide", "online", "database", "databases", "printout", "printouts",
    "reimbursement", "reimbursements", "subsystem", "subsystems", "workload",
    "payroll", "payrolls", "backlog", "microfilm", "micrographics",
    "intergovernmental", "programmatic", "demographics", "geocoded",
    "adjudication", "adjudications", "arrestee", "arrestees", "recidivism",
    "vouchering", "misdemeanor", "misdemeanors", "landmarked", "rezoning",
    "brooklyn", "queens", "manhattan", "bronx", "yorkers",
    "immunobiology", "retrovirology", "geosupport", "geocoding",
}


def load_dictionary():
    words = set(DOMAIN_WORDS)
    for p in ("/usr/share/dict/words",):
        try:
            with open(p) as f:
                words.update(w.strip().lower() for w in f)
        except OSError:
            pass
    if len(words) < 10000:
        sys.exit("system dictionary not found; refusing to normalize blind")
    return words


DICT = load_dictionary()
TOKEN = re.compile(r"[A-Za-z0-9~']+")

# Hand-verified fixes for tokens the substitution table cannot reach
# (glued words, dropped letters). Checked against the scan's context.
EXPLICIT_FIXES = {
    "aanaqers": "managers",
    "byaqency": "by agency",
    "dat~ase": "database",
    "demoqraphi~": "demographic",
    "planninqlicenses": "planning licenses",
    "prevent~le": "preventable",
    "p~lic": "public",
    "qeoqraphyonly": "geography only",
    "~istory": "history",
    "~y": "by",
}


def known(word):
    w = word.lower().strip("'")
    if not w or w.isdigit() or len(w) <= 2 or w in DICT:
        return True
    if w.endswith("'s") and w[:-2] in DICT:
        return True
    # /usr/share/dict/words omits most inflected forms; check the stem
    for suf in ("s", "es", "ed", "ing", "ly"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            stem = w[: -len(suf)]
            if stem in DICT or stem + "e" in DICT:
                return True
            # doubled final consonant: planning -> plann -> plan
            if suf in ("ed", "ing") and len(stem) >= 4 and stem[-1] == stem[-2] and stem[:-1] in DICT:
                return True
    # categories -> category
    if w.endswith("ies") and len(w) >= 6 and w[:-3] + "y" in DICT:
        return True
    return False


def repair(word):
    """Try substitutions at every combination of suspicious positions."""
    positions = [i for i, ch in enumerate(word) if ch.lower() in SUBS]
    if not positions or len(positions) > 6:
        return None
    attempts = 0
    for r in range(1, len(positions) + 1):
        for combo in itertools.combinations(positions, r):
            choice_sets = [SUBS[word[i].lower()] for i in combo]
            for reps in itertools.product(*choice_sets):
                attempts += 1
                if attempts > 5000:
                    return None
                chars = list(word)
                for i, rep in zip(combo, reps):
                    chars[i] = rep.upper() if chars[i].isupper() else rep
                cand = "".join(chars)
                if known(cand):
                    return cand
    return None


def fix_case(word):
    """pUblic -> public / Public; leave acronyms and normal words alone."""
    if word.isupper() or word.islower() or word.istitle():
        return word
    if word.lower() in DICT:
        return word.capitalize() if word[0].isupper() else word.lower()
    return word


STATS = {"checked": 0, "repaired": 0, "recased": 0}


def normalize_token(m):
    word = m.group(0)
    if word.lower() in EXPLICIT_FIXES:
        STATS["repaired"] += 1
        fix = EXPLICIT_FIXES[word.lower()]
        return fix.capitalize() if word[0].isupper() else fix
    if any(ch.isalpha() for ch in word):
        STATS["checked"] += 1
        if word.isupper() and "~" not in word and not any(ch.isdigit() for ch in word):
            return word  # likely acronym; leave alone
        if not known(word):
            fixed = repair(word)
            if fixed is not None:
                STATS["repaired"] += 1
                return fixed
        recased = fix_case(word)
        if recased != word:
            STATS["recased"] += 1
        return recased
    return word


def normalize_str(s):
    return TOKEN.sub(normalize_token, s)


def walk(obj):
    if isinstance(obj, str):
        return normalize_str(obj)
    if isinstance(obj, list):
        return [walk(x) for x in obj]
    if isinstance(obj, dict):
        return {k: walk(v) for k, v in obj.items()}
    return obj


def main():
    doc = json.loads((DATA / "public-data-directory-1993.json").read_text())
    clean = walk(doc)
    clean["extraction_note"] = (
        "Machine-normalized edition: known OCR substitutions (q>g, z/x>i, k/h>m, "
        "digit>letter, ~>b) were repaired only where the result is a dictionary "
        "word; everything else is verbatim from the scan. For the untouched OCR "
        "text, use public-data-directory-1993.json. Verify citations against the "
        "PDF page in pdf_page.")
    out = DATA / "public-data-directory-1993-clean.json"
    out.write_text(json.dumps(clean, indent=2, ensure_ascii=False))

    csv_path = DATA / "public-data-directory-1993-applications-clean.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["agency", "user_bureau", "application_name", "year_activated",
                    "application_description", "database_contents", "status",
                    "confidentiality", "method_of_access", "pdf_page"])
        for a in clean["agencies"]:
            for r in a["applications"]:
                w.writerow([a["agency_name"], r["user_bureau"], r["application_name"],
                            r["year_activated"], r["application_description"],
                            r["database_contents"], r["status"], r["confidentiality"],
                            r["method_of_access"], r["pdf_page"]])
    print(f"tokens checked: {STATS['checked']}, repaired: {STATS['repaired']}, "
          f"recased: {STATS['recased']}")
    print("wrote", out.name, "and", csv_path.name)


if __name__ == "__main__":
    main()
