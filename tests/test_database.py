import os
import tempfile
import unittest

from module_tracker import database as db


class ModuleTrackerTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")

    def tearDown(self):
        self.conn.close()

    def test_add_and_list(self):
        db.add_module(self.conn, "prg101", "Programming", 2024, 12, 68)
        rows = db.list_modules(self.conn)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["code"], "PRG101")  # code is normalised to upper case

    def test_duplicate_same_year_rejected(self):
        db.add_module(self.conn, "PRG101", "Programming", 2024, 12)
        with self.assertRaises(ValueError):
            db.add_module(self.conn, "PRG101", "Programming", 2024, 12)

    def test_invalid_values_rejected(self):
        with self.assertRaises(ValueError):
            db.add_module(self.conn, "PRG101", "Programming", 2024, 12, 150)
        with self.assertRaises(ValueError):
            db.add_module(self.conn, "PRG101", "Programming", 2024, 0)
        with self.assertRaises(ValueError):
            db.add_module(self.conn, "", "Programming", 2024, 12)

    def test_status(self):
        self.assertEqual(db.status(None), "In progress")
        self.assertEqual(db.status(49.9), "Failed")
        self.assertEqual(db.status(50), "Passed")

    def test_set_mark_and_delete(self):
        db.add_module(self.conn, "NET101", "Networks", 2024, 10)
        db.set_mark(self.conn, "net101", 2024, 72)
        self.assertEqual(db.list_modules(self.conn)[0]["mark"], 72)
        db.delete_module(self.conn, "NET101", 2024)
        self.assertEqual(db.list_modules(self.conn), [])
        with self.assertRaises(ValueError):
            db.delete_module(self.conn, "NET101", 2024)

    def test_weighted_average(self):
        db.add_module(self.conn, "A1", "A", 2024, 10, 80)
        db.add_module(self.conn, "B1", "B", 2024, 20, 50)
        s = db.summary(self.conn)
        self.assertAlmostEqual(s["average"], (80 * 10 + 50 * 20) / 30)
        self.assertEqual(s["credits_earned"], 30)

    def test_redo_replaces_failed_attempt_in_stats(self):
        db.add_module(self.conn, "MAT101", "Maths", 2024, 10, 40)
        db.add_module(self.conn, "MAT101", "Maths", 2025, 10, 61)
        s = db.summary(self.conn)
        self.assertEqual(s["modules"], 1)
        self.assertEqual(s["failed"], 0)
        self.assertEqual(s["passed"], 1)
        self.assertAlmostEqual(s["average"], 61)
        self.assertEqual(len(db.list_modules(self.conn)), 2)  # history is kept

    def test_in_progress_not_counted_in_average(self):
        db.add_module(self.conn, "A1", "A", 2025, 10, 70)
        db.add_module(self.conn, "B1", "B", 2025, 10)
        s = db.summary(self.conn)
        self.assertEqual(s["in_progress"], 1)
        self.assertAlmostEqual(s["average"], 70)

    def test_empty_summary(self):
        s = db.summary(self.conn)
        self.assertIsNone(s["average"])
        self.assertEqual(s["modules"], 0)

    def test_csv_round_trip_and_bad_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            source = os.path.join(folder, "in.csv")
            with open(source, "w", encoding="utf-8") as f:
                f.write("code,name,year,credits,mark\n")
                f.write("A1,Alpha,2024,10,65\n")
                f.write("B1,Beta,2024,10,\n")
                f.write("C1,Gamma,2024,10,999\n")  # invalid mark
            added, errors = db.import_csv(self.conn, source)
            self.assertEqual(added, 2)
            self.assertEqual(len(errors), 1)

            target = os.path.join(folder, "out.csv")
            self.assertEqual(db.export_csv(self.conn, target), 2)
            other = db.connect(":memory:")
            added, errors = db.import_csv(other, target)
            other.close()
            self.assertEqual((added, errors), (2, []))


if __name__ == "__main__":
    unittest.main()
