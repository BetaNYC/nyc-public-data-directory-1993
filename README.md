# NYC Public Data Directory (1993), machine readable

In April 1993, New York City published its first inventory of the computerized databases held by City agencies: the **Public Data Directory, First Edition**. It was produced by the Commission on Public Information and Communication (COPIC) under NYC Charter § 1062, a requirement added by the 1989 Charter revision, with design and preparation funded in part by a grant from the New York Times Foundation.

Nearly two decades before the City's open data law (Local Law 11 of 2012) and the launch of the NYC Open Data portal, this typewritten directory told researchers, community groups, and the public what electronic data the City kept, which agency held it, and who to call about it. It is the direct ancestor of today's open data catalog.

This repository makes that document machine readable for the first time: **37 agencies and 269 database ("application") records**, parsed from the original scan into JSON and CSV.

## What's here

| Path | Contents |
|---|---|
| `data/public-data-directory-1993.json` | Full structured record: document metadata, plus each agency's address, public liaison, phone numbers, mission statement, and nested application entries |
| `data/public-data-directory-1993-applications.csv` | Flat table of all 269 application records, one row per database |
| `source/1993-NYC-Public-Data-Directory.pdf` | The original scan (169 pages) |
| `source/extracted-text.txt` | Raw OCR text layer, page by page, for full-text search |
| `scripts/parse_directory.py` | The parser that produced the data files from the PDF |

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
uv run --with pypdf scripts/parse_directory.py
```

This reads `source/1993-NYC-Public-Data-Directory.pdf` and rewrites both files in `data/`.

## Why this matters

The 1993 directory is a census of municipal computing at a specific moment: mainframe payroll tapes, COBOL-era claim systems, and the first generation of agency databases, each with a named human being you could call. Comparing it with today's [NYC Open Data catalog](https://opendata.cityofnewyork.us/) shows how far public access has come, and which systems quietly persisted for decades.

## About BetaNYC

BetaNYC is a civic organization dedicated to improving lives in New York through civic design, technology, and data. We organize NYC's civic tech community, teach New Yorkers how to use open data, and advocate for a more open and equitable government.

Get involved:

- 🌐 [beta.nyc](https://beta.nyc)
- 💬 [Join our Slack community](https://slack.beta.nyc/)
- 📰 [Subscribe to our weekly newsletter](https://beta.nyc)
- 📅 [Come to an event](https://www.beta.nyc/events/)
- ❤️ [Support our work](https://beta.nyc/donate)

## License

The parser (`scripts/`) is released under the [MIT License](LICENSE). The 1993 Public Data Directory is a publication of the City of New York and is in the public domain as a government record; the extracted data files in `data/` are dedicated to the public domain.
