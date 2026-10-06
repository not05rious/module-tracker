"""Command-line interface for the Student Module Tracker."""

import argparse
import sys

from . import database as db


def format_table(rows):
    """Return a plain-text table for a list of module rows."""
    headers = ["Code", "Name", "Year", "Credits", "Mark", "Status"]
    data = [
        [
            r["code"],
            r["name"],
            str(r["year"]),
            str(r["credits"]),
            "-" if r["mark"] is None else f"{r['mark']:g}",
            db.status(r["mark"]),
        ]
        for r in rows
    ]
    widths = [max(len(h), *(len(row[i]) for row in data)) if data else len(h)
              for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    out = [line, "  ".join("-" * w for w in widths)]
    for row in data:
        out.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(out)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="module_tracker",
        description="Track your university modules, marks and averages.",
    )
    parser.add_argument("--db", default="modules.db", help="database file (default: modules.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a module")
    add.add_argument("code")
    add.add_argument("name")
    add.add_argument("--year", type=int, required=True)
    add.add_argument("--credits", type=int, required=True)
    add.add_argument("--mark", type=float, help="leave out if not marked yet")

    ls = sub.add_parser("list", help="list modules")
    ls.add_argument("--year", type=int, help="only show this year")

    mark = sub.add_parser("mark", help="set or change a module mark")
    mark.add_argument("code")
    mark.add_argument("--year", type=int, required=True)
    mark.add_argument("value", type=float)

    delete = sub.add_parser("delete", help="delete a module")
    delete.add_argument("code")
    delete.add_argument("--year", type=int, required=True)

    sub.add_parser("stats", help="show averages and credits")

    imp = sub.add_parser("import", help="import modules from a CSV file")
    imp.add_argument("file")

    exp = sub.add_parser("export", help="export modules to a CSV file")
    exp.add_argument("file")
    return parser


def run(args, conn):
    if args.command == "add":
        db.add_module(conn, args.code, args.name, args.year, args.credits, args.mark)
        print(f"Added {args.code.upper()} ({args.year}).")
    elif args.command == "list":
        rows = db.list_modules(conn, args.year)
        print(format_table(rows) if rows else "No modules yet. Add one with: add CODE NAME --year Y --credits C")
    elif args.command == "mark":
        db.set_mark(conn, args.code, args.year, args.value)
        print(f"Updated {args.code.upper()} ({args.year}) to {args.value:g}%.")
    elif args.command == "delete":
        db.delete_module(conn, args.code, args.year)
        print(f"Deleted {args.code.upper()} ({args.year}).")
    elif args.command == "stats":
        s = db.summary(conn)
        print(f"Modules counted (latest attempt of each): {s['modules']}")
        print(f"Passed: {s['passed']}   Failed: {s['failed']}   In progress: {s['in_progress']}")
        print(f"Credits earned: {s['credits_earned']} of {s['credits_attempted']} marked")
        avg = "n/a" if s["average"] is None else f"{s['average']:.1f}%"
        print(f"Weighted average: {avg}")
        for year, value in s["by_year"].items():
            print(f"  {year}: {value:.1f}%")
    elif args.command == "import":
        added, errors = db.import_csv(conn, args.file)
        print(f"Imported {added} module(s).")
        for message in errors:
            print(f"Skipped - {message}")
    elif args.command == "export":
        count = db.export_csv(conn, args.file)
        print(f"Exported {count} module(s) to {args.file}.")


def main(argv=None):
    args = build_parser().parse_args(argv)
    conn = db.connect(args.db)
    try:
        run(args, conn)
    except (ValueError, OSError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0
