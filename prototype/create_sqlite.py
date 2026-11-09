#!/usr/bin/env python3
"""Create the SimVascular SQLite database from the six current CSV inputs.

Run ``python create_sqlite.py`` from any directory. The database is rebuilt
on each run. Paper DOIs are stored only in the publications tables; SDR DOIs
remain project metadata. Uses only the Python standard library.
"""

import csv
from datetime import datetime
from pathlib import Path
import re
import sqlite3

# Input/output files: edit these paths if the files live elsewhere.
BASE = Path(__file__).resolve().parent
PROJECTS_CSV = BASE / "fixtures/dataset-svprojects.csv"
RESULTS_CSV = BASE / "fixtures/dataset-svresults.csv"
PUBLICATIONS_CSV = BASE / "fixtures/publications.csv"
PEOPLE_CSV = BASE / "fixtures/people.csv"
PUBLICATION_AUTHORS_CSV = BASE / "fixtures/publication_authors.csv"
PROJECT_CREATORS_CSV = BASE / "fixtures/project_creators.csv"
DATABASE = BASE / "sv_dataset.sqlite"

PROJECT_COLUMNS = {
    "Name": "name", "Legacy Name": "legacy_name", "Image Number": "image_number",
    "Sex": "sex", "Age": "age", "Species": "species", "Ethnicity": "ethnicity",
    "Animal": "animal", "Anatomy": "anatomy", "Disease": "disease",
    "Procedure": "procedure", "Images": "has_images", "Paths": "has_paths",
    "Segmentations": "has_segmentations", "Models": "has_models",
    "Meshes": "has_meshes", "Simulations": "has_simulations",
    "Notes": "notes", "Citation": "citation_raw", "SDR DOI": "sdr_doi",
    "Image Manufacturer": "image_manufacturer", "Image Type": "image_type",
    "Image Source": "image_source", "Image Modality": "image_modality",
    "Results": "has_results", "Date Added": "date_added",
    "Order Uploaded": "order_uploaded", "Model Creator": "model_creator_raw",
}

RESULT_COLUMNS = {
    "Full Simulation File Name": "filename",
    "Model Image Number": "model_image_number",
    "Short Simulation File Name": "short_filename",
    "Legacy Simulation File Name": "legacy_filename",
    "Simulation Fidelity": "simulation_fidelity",
    "Simulation Method": "simulation_method",
    "Simulation Condition": "simulation_condition",
    "Results Type": "results_type", "Results File Type": "results_file_type",
    "Simulation Creator": "simulation_creator", "Notes": "notes",
}

BOOL_COLUMNS = {
    "has_images", "has_paths", "has_segmentations", "has_models",
    "has_meshes", "has_simulations", "has_results",
}

# Matches paper DOIs embedded in the original projects CSV.
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[^\s,;<>\"'()]+", re.IGNORECASE)


def convert(column, value):
    """Normalize missing values and SQLite-friendly field types."""
    value = (value or "").strip()
    if value in ("", "-"):
        return None
    if column in BOOL_COLUMNS or column == "order_uploaded":
        return int(value)
    if column == "age":
        return float(value)
    if column == "date_added":
        return datetime.strptime(value, "%d %b %Y").date().isoformat()
    return value


schema = """
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    legacy_name TEXT, image_number TEXT, sex TEXT, age REAL,
    species TEXT, ethnicity TEXT, animal TEXT, anatomy TEXT,
    disease TEXT, procedure TEXT,
    has_images INTEGER, has_paths INTEGER, has_segmentations INTEGER,
    has_models INTEGER, has_meshes INTEGER, has_simulations INTEGER,
    notes TEXT, citation_raw TEXT, sdr_doi TEXT UNIQUE,
    image_manufacturer TEXT, image_type TEXT, image_source TEXT,
    image_modality TEXT, has_results INTEGER, date_added TEXT,
    order_uploaded INTEGER, model_creator_raw TEXT
);

CREATE TABLE result_files (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    filename TEXT NOT NULL UNIQUE,
    model_image_number TEXT, short_filename TEXT, legacy_filename TEXT,
    simulation_fidelity TEXT, simulation_method TEXT,
    simulation_condition TEXT, results_type TEXT, results_file_type TEXT,
    simulation_creator TEXT, notes TEXT
);

CREATE TABLE publications (
    paper_doi TEXT PRIMARY KEY COLLATE NOCASE,
    title TEXT NOT NULL,
    source_url TEXT
);

CREATE TABLE people (
    person_id INTEGER PRIMARY KEY,
    display_name TEXT NOT NULL,
    given_name TEXT,
    family_name TEXT,
    orcid TEXT UNIQUE,
    openalex_id TEXT UNIQUE,
    identity_status TEXT,
    identity_source_url TEXT
);

CREATE TABLE project_publications (
    project_id INTEGER NOT NULL REFERENCES projects(id),
    paper_doi TEXT NOT NULL REFERENCES publications(paper_doi),
    PRIMARY KEY (project_id, paper_doi)
);

CREATE TABLE publication_authors (
    paper_doi TEXT NOT NULL REFERENCES publications(paper_doi),
    person_id INTEGER NOT NULL REFERENCES people(person_id),
    author_order INTEGER NOT NULL,
    PRIMARY KEY (paper_doi, person_id)
);

CREATE TABLE project_creators (
    project_id INTEGER NOT NULL REFERENCES projects(id),
    person_id INTEGER NOT NULL REFERENCES people(person_id),
    creator_order INTEGER NOT NULL,
    PRIMARY KEY (project_id, person_id)
);

CREATE INDEX idx_projects_anatomy ON projects(anatomy);
CREATE INDEX idx_projects_disease ON projects(disease);
CREATE INDEX idx_results_project ON result_files(project_id);
CREATE INDEX idx_publications_title ON publications(title);
CREATE INDEX idx_people_display_name ON people(display_name);
CREATE INDEX idx_people_family_name ON people(family_name);
CREATE INDEX idx_project_publications_doi ON project_publications(paper_doi);
CREATE INDEX idx_publication_authors_person ON publication_authors(person_id);
CREATE INDEX idx_project_creators_person ON project_creators(person_id);
"""

for path in (
    PROJECTS_CSV,
    RESULTS_CSV,
    PUBLICATIONS_CSV,
    PEOPLE_CSV,
    PUBLICATION_AUTHORS_CSV,
    PROJECT_CREATORS_CSV,
):
    if not path.is_file():
        raise FileNotFoundError(f"Missing input CSV: {path}")

DATABASE.parent.mkdir(parents=True, exist_ok=True)
if DATABASE.exists():
    DATABASE.unlink()

with sqlite3.connect(DATABASE) as db:
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(schema)

    # Publications: one row per paper DOI.
    with PUBLICATIONS_CSV.open(newline="", encoding="utf-8-sig") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            try:
                db.execute(
                    "INSERT INTO publications (paper_doi, title, source_url) VALUES (?, ?, ?)",
                    (
                        row["paper_doi"].strip().lower(),
                        row["title"].strip(),
                        (row.get("source_url") or "").strip() or None,
                    ),
                )
            except Exception as exc:
                raise ValueError(f"{PUBLICATIONS_CSV.name}, line {line_number}: {exc}") from exc

    # People: stable person_id values used by both author and creator junction tables.
    with PEOPLE_CSV.open(newline="", encoding="utf-8-sig") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            try:
                db.execute(
                    """INSERT INTO people (
                        person_id, display_name, given_name, family_name,
                        orcid, openalex_id, identity_status, identity_source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        int(row["person_id"]),
                        row["display_name"].strip(),
                        (row.get("given_name") or "").strip() or None,
                        (row.get("family_name") or "").strip() or None,
                        (row.get("orcid") or "").strip() or None,
                        (row.get("openalex_id") or "").strip() or None,
                        (row.get("identity_status") or "").strip() or None,
                        (row.get("identity_source_url") or "").strip() or None,
                    ),
                )
            except Exception as exc:
                raise ValueError(f"{PEOPLE_CSV.name}, line {line_number}: {exc}") from exc

    # Projects: IDs are explicitly assigned in source-file order so they match
    # project_creators.csv exactly.
    project_ids = {}
    with PROJECTS_CSV.open(newline="", encoding="utf-8-sig") as f:
        for project_id, row in enumerate(csv.DictReader(f), start=1):
            try:
                record = {
                    field: convert(field, row[heading])
                    for heading, field in PROJECT_COLUMNS.items()
                }
                record = {"id": project_id, **record}
                columns = ", ".join(record)
                placeholders = ", ".join("?" for _ in record)
                db.execute(
                    f"INSERT INTO projects ({columns}) VALUES ({placeholders})",
                    tuple(record.values()),
                )
                project_ids[record["name"]] = project_id
            except Exception as exc:
                raise ValueError(f"{PROJECTS_CSV.name}, line {project_id + 1}: {exc}") from exc

    # Result files link back to projects by Model Name from the original CSV.
    with RESULTS_CSV.open(newline="", encoding="utf-8-sig") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            try:
                project_name = (row.get("Model Name") or "").strip()
                if project_name not in project_ids:
                    raise ValueError(f"Unknown project: {project_name!r}")

                record = {"project_id": project_ids[project_name]}
                record.update({
                    field: convert(field, row[heading])
                    for heading, field in RESULT_COLUMNS.items()
                })
                columns = ", ".join(record)
                placeholders = ", ".join("?" for _ in record)
                db.execute(
                    f"INSERT INTO result_files ({columns}) VALUES ({placeholders})",
                    tuple(record.values()),
                )
            except Exception as exc:
                raise ValueError(f"{RESULTS_CSV.name}, line {line_number}: {exc}") from exc

    # Link projects to papers by extracting paper DOIs from the original project data.
    with PROJECTS_CSV.open(newline="", encoding="utf-8-sig") as f:
        for project_id, row in enumerate(csv.DictReader(f), start=1):
            doi_text = (row.get("DOI") or "").strip()
            if doi_text in ("", "-"):
                doi_text = (row.get("Citation") or "") + " " + (row.get("Notes") or "")

            for paper_doi in {
                match.rstrip(".,;").lower()
                for match in DOI_PATTERN.findall(doi_text)
            }:
                if not db.execute(
                    "SELECT 1 FROM publications WHERE paper_doi = ?", (paper_doi,)
                ).fetchone():
                    raise ValueError(
                        f"{PROJECTS_CSV.name}, project {project_id}: "
                        f"paper DOI {paper_doi!r} is missing from {PUBLICATIONS_CSV.name}"
                    )
                db.execute(
                    "INSERT OR IGNORE INTO project_publications (project_id, paper_doi) "
                    "VALUES (?, ?)",
                    (project_id, paper_doi),
                )

    # Paper-author many-to-many relationships.
    with PUBLICATION_AUTHORS_CSV.open(newline="", encoding="utf-8-sig") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            try:
                db.execute(
                    """INSERT INTO publication_authors
                       (paper_doi, person_id, author_order)
                       VALUES (?, ?, ?)""",
                    (
                        row["paper_doi"].strip().lower(),
                        int(row["person_id"]),
                        int(row["author_order"]),
                    ),
                )
            except Exception as exc:
                raise ValueError(
                    f"{PUBLICATION_AUTHORS_CSV.name}, line {line_number}: {exc}"
                ) from exc

    # Project-creator many-to-many relationships.
    with PROJECT_CREATORS_CSV.open(newline="", encoding="utf-8-sig") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            try:
                db.execute(
                    """INSERT INTO project_creators
                       (project_id, person_id, creator_order)
                       VALUES (?, ?, ?)""",
                    (
                        int(row["project_id"]),
                        int(row["person_id"]),
                        int(row["creator_order"]),
                    ),
                )
            except Exception as exc:
                raise ValueError(
                    f"{PROJECT_CREATORS_CSV.name}, line {line_number}: {exc}"
                ) from exc

    errors = db.execute("PRAGMA foreign_key_check").fetchall()
    if errors:
        raise RuntimeError(f"Foreign key violations: {errors}")

    for table in (
        "projects",
        "result_files",
        "publications",
        "people",
        "project_publications",
        "publication_authors",
        "project_creators",
    ):
        count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")

print(f"Database created: {DATABASE}")
