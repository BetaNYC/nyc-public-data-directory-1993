# NYC Public Data Directory (1993), machine readable

In April 1993, New York City published its first inventory of the computerized databases held by City agencies: the **Public Data Directory, First Edition**. It was produced by the Commission on Public Information and Communication (COPIC) under NYC Charter § 1062, a requirement added by the 1989 Charter revision, with design and preparation funded in part by a grant from the New York Times Foundation.

Nearly two decades before the City's open data law (Local Law 11 of 2012) and the launch of the NYC Open Data portal, this typewritten directory told researchers, community groups, and the public what electronic data the City kept, which agency held it, and who to call about it. It is the direct ancestor of today's open data catalog.

This repository makes that document machine readable for the first time: **37 agencies and 269 database ("application") records**, parsed from the original scan into JSON and CSV.

## What's here

| Path | Contents |
|---|---|
| `data/public-data-directory-1993.json` | Full structured record, **verbatim OCR values**: document metadata, plus each agency's address, public liaison, phone numbers, mission statement, and nested application entries |
| `data/public-data-directory-1993-applications.csv` | Flat table of all 269 application records (verbatim), one row per database |
| `data/public-data-directory-1993-clean.json` | **Spell-normalized edition** of the JSON (see "Two editions" below) |
| `data/public-data-directory-1993-applications-clean.csv` | Spell-normalized edition of the applications table |
| `data/agencies-1993.csv` | One row per agency: durable slug, normalized name, verbatim name, address, public liaison, phones, application count |
| `data/agency-name-registry.csv` | Longitudinal agency-name registry, seeded with the 37 names observed in 1993 (see "Agency name registry" below) |
| `source/1993-NYC-Public-Data-Directory.pdf` | The original scan (169 pages) |
| `source/extracted-text.txt` | Raw OCR text layer, page by page, for full-text search |
| `scripts/parse_directory.py` | The parser that produced the verbatim data files from the PDF |
| `scripts/normalize_text.py` | Produces the clean edition from the verbatim JSON |
| `scripts/build_agency_tables.py` | Produces the agency table and the name registry |

## Two editions: verbatim and clean

The **verbatim** files preserve the scan's OCR errors exactly as extracted and are the citation-grade source of truth. The **clean** files repair the typescript's known OCR substitutions (`q`→`g`, `z`/`x`→`i`, `k`/`h`→`m`, digit-for-letter, `~`) using a deterministic, dictionary-checked pass: a token is only changed when applying a known substitution yields a real word, plus a short hand-verified fix list for glued or double-error tokens. About 600 of roughly 17,000 tokens were repaired; anything that could not be confidently fixed remains verbatim. If a value matters, verify it against the PDF page in `pdf_page`.

## Agency name registry

`data/agency-name-registry.csv` is an authority file for NYC agency names over time. Each row is one observation of an agency name in a dated source:

| Column | Meaning |
|---|---|
| `agency_slug` | Durable join key for the agency across sources and decades (e.g. `hpd`, `tlc`, `city-planning`) |
| `observed_name` | The name exactly as the source styles it (normalized for OCR, not modernized) |
| `observed_date` | Date or month of the source (`1993-04`) |
| `source` | The document or system the name was observed in |
| `source_detail` | Pointer for verification (PDF page, URL, notice ID) |
| `notes` | Renames, merges, successor relationships, anything a future researcher needs |

It is seeded with the 37 agencies of the 1993 directory. The intent is longitudinal: future sources append rows under the same slug, so the file accumulates each agency's naming history. The next planned source is the City Record (notices back to the early 2000s), which BetaNYC will be processing in a companion repository; its crawler can append one row per distinct agency-name spelling it encounters. When an agency is renamed or absorbed (for example, the 1993 Department of Personnel or Department of General Services, whose functions later moved to DCAS), record the relationship in `notes` on the newer observation rather than rewriting history on the older row.

## The data

Each application record has these fields:

| Field | Description |
|---|---|
| `agency` | Agency name from the profile page |
| `user_bureau` | Bureau or division operating the system (where listed) |
| `application_name` | Name of the database or system |
| `year_activated` | Year the system went live (as reported in 1993) |
| `application_description` | What the system did |
| `database_contents` | What kinds of records it held |
| `status` / `confidentiality` / `method_of_access` | Present on a minority of records |
| `pdf_page` | 1-indexed page of the source PDF, so every value can be checked against the scan |

Three agencies (the Police Department, Housing Preservation and Development, and the Human Resources Administration) filed placeholders promising entries "in future editions" and therefore have zero records. That is the original document, not a parsing gap.

## Caveats

The data was extracted from the scan's embedded OCR text layer, and field values preserve its errors verbatim. Common substitutions in the 1993 typescript include `q` for `g` ("aqency"), `Z` or `X` for `I` ("APPLZCATZON"), and `K` or `H` for `M` ("Kanaqement"). Field labels were fuzzy-matched during parsing so records were not lost, but the values themselves are uncorrected. Use `pdf_page` to verify anything you plan to cite.

Corrections are welcome. If you spot an OCR error against the scan, open an issue or a pull request.

## Reproducing the extraction

```bash
uv run --with pypdf scripts/parse_directory.py   # PDF -> verbatim JSON + CSV
python3 scripts/normalize_text.py                # verbatim JSON -> clean JSON + CSV
python3 scripts/build_agency_tables.py           # verbatim JSON -> agency tables
```

The pipeline reads `source/1993-NYC-Public-Data-Directory.pdf` and rewrites everything in `data/`.

## Why this matters

The 1993 directory is a census of municipal computing at a specific moment: mainframe payroll tapes, COBOL-era claim systems, and the first generation of agency databases, each with a named human being you could call. Comparing it with today's [NYC Open Data catalog](https://opendata.cityofnewyork.us/) shows how far public access has come, and which systems quietly persisted for decades.

## About BetaNYC

BetaNYC is a civic organization dedicated to improving lives in New York through civic design, technology, and data. We organize NYC's civic tech community, teach New Yorkers how to use open data, and advocate for a more open and equitable government.

Get involved:

- 🌐 [beta.nyc](https://beta.nyc)
- 🛠️ [Become a BetaBuilder](https://beta.nyc/donate)
- 📰 [Subscribe to our weekly newsletter](https://beta.nyc)
- 📅 [Come to an event](https://www.beta.nyc/events/)

## License

The parser (`scripts/`) is released under the [MIT License](LICENSE). The 1993 Public Data Directory is a publication of the City of New York and is in the public domain as a government record; the extracted data files in `data/` are dedicated to the public domain.
