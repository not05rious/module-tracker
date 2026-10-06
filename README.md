# Student Module Tracker

A small command-line app for keeping track of your university modules, marks and averages. Built with Python and SQLite, using only the standard library (nothing to install).

## Features

- Add, list, update and delete modules
- Marks are optional, so you can add modules that are still in progress
- Weighted average (by credits), credits earned, and a per-year breakdown
- Handles redone modules: the same module code can be added again in a later year, and only the **latest attempt** counts in the statistics while the history is kept
- Import and export modules as CSV
- Input validation (marks from 0 to 100, positive credits, no duplicate module in the same year)
- Unit tests

## Requirements

Python 3.9 or newer.

## Usage

Run all commands from the project folder.

```bash
# Add modules (leave out --mark if it has not been marked yet)
python -m module_tracker add PRG101 "Introduction to Programming" --year 2024 --credits 12 --mark 68
python -m module_tracker add SEC301 "Software Security" --year 2026 --credits 15

# List everything, or one year
python -m module_tracker list
python -m module_tracker list --year 2025

# Set or change a mark
python -m module_tracker mark SEC301 --year 2026 71

# Show statistics
python -m module_tracker stats

# Delete a module attempt
python -m module_tracker delete PRG101 --year 2024

# CSV import / export
python -m module_tracker import sample_data.csv
python -m module_tracker export exported.csv
```

By default the data is stored in `modules.db` in the current folder. Use `--db other.db` before the command to use a different file, for example `python -m module_tracker --db test.db list`.

### CSV format

```
code,name,year,credits,mark
PRG101,Introduction to Programming,2024,12,68
SEC301,Software Security,2026,15,
```

Leave `mark` empty for modules that are still in progress. The pass mark is 50.

## Example output

```
$ python -m module_tracker stats
Modules counted (latest attempt of each): 6
Passed: 5   Failed: 0   In progress: 1
Credits earned: 56 of 56 marked
Weighted average: 66.8%
  2024: 69.8%
  2025: 64.9%
```

## Running the tests

```bash
python -m unittest discover -s tests
```

## Project structure

```
module-tracker/
  module_tracker/
    __init__.py
    __main__.py     # lets you run: python -m module_tracker
    cli.py          # argument parsing and printing
    database.py     # SQLite storage, validation and statistics
  tests/
    test_database.py
  sample_data.csv   # made-up example data
  README.md
```

## Ideas for next steps

- A small Flask web interface on top of `database.py`
- A chart of averages per year
- Support for different pass marks or grading scales
