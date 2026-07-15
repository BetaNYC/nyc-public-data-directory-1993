#!/usr/bin/env python3
"""Build the agency tables from the parsed 1993 directory.

Writes:
  data/agencies-1993.csv        - one row per agency as profiled in the 1993 directory
  data/agency-name-registry.csv - longitudinal agency-name registry, seeded with the
                                  1993 observations; designed for future sources
                                  (e.g. the City Record) to append rows

The slug is the durable join key across sources and years. The 1993 names were
hand-normalized from the OCR verbatim names against the scan.
"""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

# verbatim OCR name (as parsed) -> (slug, normalized 1993 name)
AGENCIES = {
    "DEPARTMENT FOR THE AGING": ("aging", "Department for the Aging"),
    "DEPARTMENT OF BUILDINGS": ("buildings", "Department of Buildings"),
    "DEPARTMENT OF BUSINESS SERVICES": ("business-services", "Department of Business Services"),
    "NEW YORK CITY CAMPAIGN FINANCE BOARD": ("campaign-finance-board", "New York City Campaign Finance Board"),
    "DEPARTMENT OF CITY PLANNING": ("city-planning", "Department of City Planning"),
    "OFFICE OF THE COMPTROLLER": ("comptroller", "Office of the Comptroller"),
    "DEPARTMENT OF CONSUMER AFFAIRS": ("consumer-affairs", "Department of Consumer Affairs"),
    "OFFICE OF CONTRACTS": ("contracts", "Office of Contracts"),
    "DEPARTMENT OF CORRECTION": ("correction", "Department of Correction"),
    "DEPARTMENT OF EMPLOYMENT ~": ("employment", "Department of Employment"),
    "DEPARTMENT OF ENVIRONMENTAL PROTECTION": ("environmental-protection", "Department of Environmental Protection"),
    "DEPARTMENT OF FINANCE": ("finance", "Department of Finance"),
    "FINANCIAL INFORMATION SERVICES AGENCY": ("fisa", "Financial Information Services Agency"),
    "FIRE DEPARTMENT": ("fire", "Fire Department"),
    "DEPARTMENT OF GENERAL SERVICES": ("general-services", "Department of General Services"),
    "DEPARTMENT OF HEALTH": ("health", "Department of Health"),
    "DEPARTMENT OF HOUSING PRESERVATION AND DEVELOPMENT": ("hpd", "Department of Housing Preservation and Development"),
    "HUMAN RESOURCES ADMINISTRATION": ("hra", "Human Resources Administration"),
    "DEPARTMENT OF JUVENILE JUSTICE": ("juvenile-justice", "Department of Juvenile Justice"),
    "OFFICE OF LABOR RELATIONS": ("labor-relations", "Office of Labor Relations"),
    "LANDMARKS PRESERVATION COMMISSION": ("landmarks", "Landmarks Preservation Commission"),
    "LAW DEPARTMENT": ("law", "Law Department"),
    "NYC LOFT BOARD": ("loft-board", "NYC Loft Board"),
    "OFFICE OF MANAGEMENT & BUDGET": ("omb", "Office of Management & Budget"),
    "DEPARTMENT OF MENTAL HEALTH, MENTAL RETARDATION AND ALCOHOLISM SERVICES": (
        "mental-health", "Department of Mental Health, Mental Retardation and Alcoholism Services"),
    "DEPARTMENT OF PARKS AND RECREATION": ("parks", "Department of Parks and Recreation"),
    "DEPARTMENT OF PERSONNEL": ("personnel", "Department of Personnel"),
    "POLICE DEPARTMENT": ("police", "Police Department"),
    "DEPARTMENT OF PROBATION": ("probation", "Department of Probation"),
    "OFFICE OF THE DEPUTY MAYOR FOR PUBLIC SAFETY (formerly, the OFFICE OF THE COORDINATOR OF CRIMINAL JUSTICE)": (
        "deputy-mayor-public-safety",
        "Office of the Deputy Mayor for Public Safety (formerly the Office of the Coordinator of Criminal Justice)"),
    "DEPARTMENT OF RECORDS AND INFORMATION SERVICES": ("records", "Department of Records and Information Services"),
    "DEPARTMENT OF SANITATION": ("sanitation", "Department of Sanitation"),
    "OFFICE OF THE CITY SHERIFF": ("sheriff", "Office of the City Sheriff"),
    "TAXI AND LIMOUSINE COMMISSION": ("tlc", "Taxi and Limousine Commission"),
    "DEP AR TMENT OF TELECOMMUNICATIONS AND ENERGY": (
        "telecommunications-energy", "Department of Telecommunications and Energy"),
    "DEPARTMENT OF TRANSPORTATION": ("transportation", "Department of Transportation"),
    "DEPARTMENT OF YOUTH SERVICES": ("youth-services", "Department of Youth Services"),
}

SOURCE = "Public Data Directory, First Edition (COPIC)"
SOURCE_DATE = "1993-04"


def main():
    doc = json.loads((DATA / "public-data-directory-1993.json").read_text())
    agencies = doc["agencies"]
    unmapped = [a["agency_name"] for a in agencies if a["agency_name"] not in AGENCIES]
    if unmapped:
        raise SystemExit(f"unmapped agency names (update AGENCIES): {unmapped}")

    with (DATA / "agencies-1993.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["agency_slug", "agency_name", "agency_name_verbatim", "address",
                    "public_liaison", "liaison_title", "phone_numbers",
                    "application_count", "pdf_page"])
        for a in agencies:
            slug, clean = AGENCIES[a["agency_name"]]
            w.writerow([slug, clean, a["agency_name"], a["address"],
                        a["public_liaison"], a["liaison_title"],
                        "; ".join(a["phone_numbers"]),
                        len(a["applications"]), a["pdf_page"]])

    with (DATA / "agency-name-registry.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["agency_slug", "observed_name", "observed_date",
                    "source", "source_detail", "notes"])
        for a in agencies:
            slug, clean = AGENCIES[a["agency_name"]]
            w.writerow([slug, clean, SOURCE_DATE, SOURCE,
                        f"pdf_page {a['pdf_page']}", ""])
    print(f"wrote agencies-1993.csv and agency-name-registry.csv ({len(agencies)} agencies)")


if __name__ == "__main__":
    main()
