#!/usr/bin/env python3
import argparse
import csv
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

NON_IDENT = re.compile(r"[^A-Za-z0-9_]+")
MULTI_US = re.compile(r"_+")

def sanitize(name: str) -> str:
    """Sanitize a column or table name according to the specification."""
    if name is None:
        name = ""
    # Trim leading/trailing whitespace
    n = unicodedata.normalize("NFC", str(name)).strip().lower()
    # Replace any run of non [A-Za-z0-9_] characters with a single underscore
    n = NON_IDENT.sub("_", n)
    # Collapse multiple underscores to one
    n = MULTI_US.sub("_", n)
    # Strip leading/trailing underscores
    n = n.strip("_")
    # If empty, use 'col'
    if not n:
        n = "col"
    # If starts with digit, prefix underscore
    if n[0].isdigit():
        n = f"_{n}"
    return n


def unique_names(names):
    """Sanitize names and ensure uniqueness by appending _2, _3, etc."""
    seen = {}
    out = []
    for n in names:
        base = sanitize(n)
        cand = base
        i = 2
        while cand in seen:
            cand = f"{base}_{i}"
            i += 1
        seen[cand] = True
        out.append(cand)
    return out


def read_header(csv_path: Path):
    """Read the first row (header) from the CSV file."""
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            print("Error: CSV has no header row.", file=sys.stderr)
            sys.exit(2)
        return header


def create_table(conn: sqlite3.Connection, table: str, columns: list):
    """Drop table if exists and create new table with TEXT columns."""
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table}")
    cols_sql = ", ".join(f"{c} TEXT" for c in columns)
    cur.execute(f"CREATE TABLE {table} ({cols_sql})")
    conn.commit()


def insert_rows(conn: sqlite3.Connection, table: str, columns: list, csv_path: Path) -> int:
    """Insert all rows from CSV (excluding header) into the table."""
    placeholders = ", ".join(["?"] * len(columns))
    col_list = ", ".join(columns)
    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    count = 0
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        cur = conn.cursor()
        for row in reader:
            # Pad/truncate row to match column count
            if len(row) < len(columns):
                row = row + [None] * (len(columns) - len(row))
            elif len(row) > len(columns):
                row = row[:len(columns)]
            cur.execute(sql, row)
            count += 1
    conn.commit()
    return count


def main():
    p = argparse.ArgumentParser(
        description="Import a CSV into a SQLite database as a table named after the CSV file."
    )
    p.add_argument("db_path", help="Path to SQLite database, e.g. data.db")
    p.add_argument("csv_path", help="Path to CSV file to import")
    args = p.parse_args()

    db = Path(args.db_path)
    csv_file = Path(args.csv_path)
    if not csv_file.exists():
        print(f"Error: CSV not found: {csv_file}", file=sys.stderr)
        sys.exit(2)

    # Table name from CSV stem, sanitized with the same logic
    table = sanitize(csv_file.stem)

    # Read & sanitize header -> unique TEXT columns
    raw_header = read_header(csv_file)
    columns = unique_names(raw_header)

    try:
        conn = sqlite3.connect(str(db))
    except sqlite3.Error as e:
        print(f"Error: Could not open SQLite DB '{db}': {e}", file=sys.stderr)
        sys.exit(2)

    try:
        create_table(conn, table, columns)
        inserted = insert_rows(conn, table, columns, csv_file)
    except sqlite3.Error as e:
        print(f"Error: SQLite error while importing: {e}", file=sys.stderr)
        sys.exit(2)
    finally:
        conn.close()

    print(f"Successfully created/updated table '{table}' with {inserted} rows")


if __name__ == "__main__":
    main()
