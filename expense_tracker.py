"""Expense Tracker — menu-driven CLI for logging expenses by category.
Standard library only. Amounts are stored as integer cents.
"""

import json
import os
import sys
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.json")


def parse_amount(text):
    """Parse '12.5' / '$12.50' into integer cents. Raises ValueError."""
    text = text.strip().lstrip("$")
    if not text:
        raise ValueError("empty amount")
    whole, _, frac = text.partition(".")
    if len(frac) > 2 or not (whole or frac).isdigit() or (frac and not frac.isdigit()) or (whole and not whole.isdigit()):
        raise ValueError(f"bad amount: {text!r}")
    cents = int(whole or 0) * 100 + int(frac.ljust(2, "0") or 0)
    if cents <= 0:
        raise ValueError("amount must be positive")
    return cents


def fmt(cents):
    return f"${cents // 100:,}.{cents % 100:02d}"


def load(path=DATA_FILE):
    if not os.path.exists(path):
        return {"next_id": 1, "expenses": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(data, path=DATA_FILE):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)  # atomic: never leave a half-written file


def add_expense(data, day, cents, category, note=""):
    exp = {"id": data["next_id"], "date": day, "cents": cents,
           "category": category.strip().lower(), "note": note.strip()}
    data["expenses"].append(exp)
    data["next_id"] += 1
    return exp


def list_lines(expenses):
    rows = sorted(expenses, key=lambda e: (e["date"], e["id"]))
    lines = [f"{e['id']:>4}  {e['date']}  {fmt(e['cents']):>11}  {e['category']:<12} {e['note']}" for e in rows]
    lines.append(f"      Total: {fmt(sum(e['cents'] for e in rows))}")
    return lines


def prompt_add(data):
    day = input(f"Date [YYYY-MM-DD, blank = {date.today()}]: ").strip() or str(date.today())
    try:
        date.fromisoformat(day)
        cents = parse_amount(input("Amount: "))
    except ValueError as err:
        print(f"  ! {err}")
        return
    category = input("Category: ").strip() or "misc"
    note = input("Note (optional): ")
    exp = add_expense(data, day, cents, category, note)
    save(data)
    print(f"  Added #{exp['id']}: {fmt(cents)} on {category}")


def main():
    data = load()
    while True:
        print("\n== Expense Tracker ==\n1) Add expense\n2) List expenses\nq) Quit")
        choice = input("> ").strip().lower()
        if choice == "1":
            prompt_add(data)
        elif choice == "2":
            if not data["expenses"]:
                print("  No expenses yet.")
            else:
                print("\n".join(list_lines(data["expenses"])))
        elif choice == "q":
            break


def selfcheck():
    import tempfile
    assert parse_amount("12.5") == 1250
    assert parse_amount("$3") == 300
    assert parse_amount(".99") == 99
    for bad in ("", "abc", "1.234", "-5", "0"):
        try:
            parse_amount(bad)
            raise AssertionError(f"accepted {bad!r}")
        except ValueError:
            pass
    assert fmt(123456) == "$1,234.56"
    data = {"next_id": 1, "expenses": []}
    add_expense(data, "2026-09-02", 1000, " Food ", "lunch")
    add_expense(data, "2026-09-01", 250, "Transport")
    assert [e["id"] for e in data["expenses"]] == [1, 2]
    assert data["expenses"][0]["category"] == "food"
    lines = list_lines(data["expenses"])
    assert lines[0].split()[0] == "2" and "$12.50" in lines[-1]
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "e.json")
        save(data, p)
        assert load(p) == data
        assert load(os.path.join(d, "missing.json"))["expenses"] == []
    print("selfcheck OK")


if __name__ == "__main__":
    selfcheck() if "--selfcheck" in sys.argv else main()
