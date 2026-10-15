from pathlib import Path
import csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "sprints_cohort_data_2023.csv"


def test_csv_structure():
    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        rows = list(csv.reader(file))

    header = rows[0]
    expected_columns = len(header)

    repaired_rows = []
    repaired_records = []

    for line_number, row in enumerate(rows[1:], start=2):
        original_length = len(row)

        # Remove only trailing empty fields beyond the header width.
        while len(row) > expected_columns and row[-1] == "":
            row.pop()

        if len(row) != expected_columns:
            raise ValueError(
                f"Line {line_number} still has {len(row)} fields; "
                f"expected {expected_columns}."
            )

        if original_length != len(row):
            repaired_records.append({
                "line": line_number,
                "learner_id": row[0],
                "original_fields": original_length,
                "final_fields": len(row),
            })

        repaired_rows.append(row)

    print("CSV structure test passed.")
    print(f"Columns: {expected_columns}")
    print(f"Data records preserved: {len(repaired_rows)}")
    print(f"Rows requiring repair: {len(repaired_records)}")

    for record in repaired_records:
        print(record)


if __name__ == "__main__":
    test_csv_structure()