"""SQLite storage and business logic for the Student Module Tracker."""

import csv
import sqlite3

PASS_MARK = 50

SCHEMA = """
CREATE TABLE IF NOT EXISTS modules (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    code    TEXT NOT NULL,
    name    TEXT NOT NULL,
    year    INTEGER NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0),
    mark    REAL CHECK (mark IS NULL OR (mark >= 0 AND mark <= 100)),
    UNIQUE (code, year)
);
"""


def connect(path="modules.db"):
    """Open (and create if needed) the database. Use ':memory:' for tests."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def status(mark):
    """Return a readable status for a mark (None means not marked yet)."""
    if mark is None:
        return "In progress"
    return "Passed" if mark >= PASS_MARK else "Failed"


def _clean_mark(mark):
    if mark is None or str(mark).strip() == "":
        return None
    try:
        mark = float(mark)
    except (TypeError, ValueError):
        raise ValueError("Mark must be a number between 0 and 100.")
    if not 0 <= mark <= 100:
        raise ValueError("Mark must be between 0 and 100.")
    return mark


def _clean(code, name, year, credits, mark):
    code = (code or "").strip().upper()
    name = (name or "").strip()
    if not code:
        raise ValueError("Module code is required.")
    if not name:
        raise ValueError("Module name is required.")
    try:
        year = int(year)
        credits = int(credits)
    except (TypeError, ValueError):
        raise ValueError("Year and credits must be whole numbers.")
    if not 2000 <= year <= 2100:
        raise ValueError("Year must be between 2000 and 2100.")
    if credits <= 0:
        raise ValueError("Credits must be greater than 0.")
    return code, name, year, credits, _clean_mark(mark)


def add_module(conn, code, name, year, credits, mark=None):
    """Add a module attempt. The same code can be added again in a later year (a redo)."""
    code, name, year, credits, mark = _clean(code, name, year, credits, mark)
    try:
        cur = conn.execute(
            "INSERT INTO modules (code, name, year, credits, mark) VALUES (?, ?, ?, ?, ?)",
            (code, name, year, credits, mark),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"{code} for {year} is already in the tracker.")
    return cur.lastrowid


def list_modules(conn, year=None):
    """Return all module attempts, optionally for one year."""
    if year is None:
        cur = conn.execute("SELECT * FROM modules ORDER BY year, code")
    else:
        cur = conn.execute("SELECT * FROM modules WHERE year = ? ORDER BY code", (int(year),))
    return cur.fetchall()


def set_mark(conn, code, year, mark):
    """Set or change the mark for one module attempt."""
    mark = _clean_mark(mark)
    cur = conn.execute(
        "UPDATE modules SET mark = ? WHERE code = ? AND year = ?",
        (mark, code.strip().upper(), int(year)),
    )
    conn.commit()
    if cur.rowcount == 0:
        raise ValueError(f"No module {code.upper()} found for {year}.")


def delete_module(conn, code, year):
    """Delete one module attempt."""
    cur = conn.execute(
        "DELETE FROM modules WHERE code = ? AND year = ?",
        (code.strip().upper(), int(year)),
    )
    conn.commit()
    if cur.rowcount == 0:
        raise ValueError(f"No module {code.upper()} found for {year}.")


def latest_attempts(conn):
    """Return the most recent attempt of each module code.

    If a module was redone, only the latest attempt counts in the statistics.
    """
    cur = conn.execute(
        """
        SELECT m.* FROM modules m
        WHERE m.year = (SELECT MAX(year) FROM modules WHERE code = m.code)
        ORDER BY m.year, m.code
        """
    )
    return cur.fetchall()


def _weighted_average(rows):
    credits = sum(r["credits"] for r in rows)
    if credits == 0:
        return None
    return sum(r["mark"] * r["credits"] for r in rows) / credits


def summary(conn):
    """Return overall statistics based on the latest attempt of each module."""
    rows = latest_attempts(conn)
    marked = [r for r in rows if r["mark"] is not None]
    passed = [r for r in marked if r["mark"] >= PASS_MARK]
    failed = [r for r in marked if r["mark"] < PASS_MARK]
    in_progress = [r for r in rows if r["mark"] is None]

    by_year = {}
    for year in sorted({r["year"] for r in marked}):
        by_year[year] = _weighted_average([r for r in marked if r["year"] == year])

    return {
        "modules": len(rows),
        "passed": len(passed),
        "failed": len(failed),
        "in_progress": len(in_progress),
        "credits_earned": sum(r["credits"] for r in passed),
        "credits_attempted": sum(r["credits"] for r in marked),
        "average": _weighted_average(marked),
        "by_year": by_year,
    }


def import_csv(conn, path):
    """Import modules from a CSV with columns: code,name,year,credits,mark.

    Returns (number_added, list_of_error_messages). Bad rows are skipped, not fatal.
    """
    added = 0
    errors = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            try:
                add_module(
                    conn,
                    row.get("code"),
                    row.get("name"),
                    row.get("year"),
                    row.get("credits"),
                    row.get("mark"),
                )
                added += 1
            except ValueError as err:
                errors.append(f"Line {line_no}: {err}")
    return added, errors


def export_csv(conn, path):
    """Write every module attempt to a CSV file. Returns the number of rows written."""
    rows = list_modules(conn)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "name", "year", "credits", "mark"])
        for r in rows:
            writer.writerow([r["code"], r["name"], r["year"], r["credits"],
                             "" if r["mark"] is None else r["mark"]])
    return len(rows)
