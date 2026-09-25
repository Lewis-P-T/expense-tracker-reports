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


def list_lines(expenses, presorted=False):
    rows = expenses if presorted else sorted(expenses, key=lambda e: (e["date"], e["id"]))
    lines = [f"{e['id']:>4}  {e['date']}  {fmt(e['cents']):>11}  {e['category']:<12} {e['note']}" for e in rows]
    lines.append(f"      Total: {fmt(sum(e['cents'] for e in rows))}")
    return lines


def parse_date(text):
    """Validate YYYY-MM-DD and return it normalised. Raises ValueError."""
    return date.fromisoformat(text.strip()).isoformat()


def categories(data):
    """Existing categories, most used first."""
    counts = {}
    for e in data["expenses"]:
        counts[e["category"]] = counts.get(e["category"], 0) + 1
    return sorted(counts, key=lambda c: (-counts[c], c))


def find(data, exp_id):
    return next((e for e in data["expenses"] if e["id"] == exp_id), None)


def delete_expense(data, exp_id):
    exp = find(data, exp_id)
    if exp:
        data["expenses"].remove(exp)
    return exp


def month_summary(expenses, month):
    """month = 'YYYY-MM'. Returns (total, [(category, cents, pct)]) biggest first."""
    totals = {}
    for e in expenses:
        if e["date"].startswith(month):
            totals[e["category"]] = totals.get(e["category"], 0) + e["cents"]
    total = sum(totals.values())
    rows = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    return total, [(c, v, 100 * v / total) for c, v in rows]


def summary_lines(expenses, month, width=30):
    total, rows = month_summary(expenses, month)
    if not rows:
        return [f"  No expenses in {month}."]
    top = rows[0][1]
    lines = [f"  Summary for {month}"]
    for cat, cents, pct in rows:
        bar = "#" * max(1, round(width * cents / top))
        lines.append(f"  {cat:<12} {fmt(cents):>11} {pct:5.1f}%  {bar}")
    lines.append(f"  {'TOTAL':<12} {fmt(total):>11}")
    return lines


def set_budget(data, category, cents):
    """Set a monthly budget for a category; cents=0 removes it."""
    budgets = data.setdefault("budgets", {})
    category = category.strip().lower()
    if cents:
        budgets[category] = cents
    else:
        budgets.pop(category, None)


def budget_report(data, month, warn_at=0.9):
    """Rows of (category, budget, spent, remaining, status) for budgeted categories."""
    spent = {}
    for e in data["expenses"]:
        if e["date"].startswith(month):
            spent[e["category"]] = spent.get(e["category"], 0) + e["cents"]
    rows = []
    for cat, budget in sorted(data.get("budgets", {}).items()):
        used = spent.get(cat, 0)
        if used > budget:
            status = "OVER"
        elif used >= budget * warn_at:
            status = "WARN"
        else:
            status = "ok"
        rows.append((cat, budget, used, budget - used, status))
    return rows


def budget_lines(data, month):
    rows = budget_report(data, month)
    if not rows:
        return ["  No budgets set."]
    lines = [f"  Budgets for {month}",
             f"  {'category':<12} {'budget':>11} {'spent':>11} {'left':>12}  status"]
    for cat, budget, used, left, status in rows:
        left_s = fmt(left) if left >= 0 else "-" + fmt(-left)
        lines.append(f"  {cat:<12} {fmt(budget):>11} {fmt(used):>11} {left_s:>12}  {status}")
    for cat, budget, used, left, status in rows:
        if status == "OVER":
            lines.append(f"  ! {cat} is over budget by {fmt(-left)}")
        elif status == "WARN":
            lines.append(f"  ! {cat} has used {100 * used // budget}% of its budget")
    return lines


SORT_KEYS = {"date": lambda e: (e["date"], e["id"]), "amount": lambda e: (e["cents"], e["id"])}


def filter_expenses(expenses, start=None, end=None, category=None, text=None, sort="date", desc=False):
    """Filter by inclusive date range, exact category and note substring (case-insensitive)."""
    category = category.strip().lower() if category else None
    text = text.lower() if text else None
    rows = [e for e in expenses
            if (not start or e["date"] >= start)
            and (not end or e["date"] <= end)
            and (not category or e["category"] == category)
            and (not text or text in e["note"].lower())]
    return sorted(rows, key=SORT_KEYS[sort], reverse=desc)


def ask(prompt, parse, default=None):
    """Re-prompt until parse() accepts the input. Blank returns default when given."""
    while True:
        text = input(prompt).strip()
        if not text and default is not None:
            return default
        try:
            return parse(text)
        except ValueError as err:
            print(f"  ! {err}")


def ask_category(data, default=None):
    known = categories(data)
    if known:
        print("  Known: " + ", ".join(known[:8]))
    label = f"Category [{default}]: " if default else "Category: "
    return input(label).strip() or default or "misc"


def ask_id(data):
    def parse(text):
        exp = find(data, int(text))
        if not exp:
            raise ValueError(f"no expense #{text}")
        return exp
    return ask("Expense id: ", parse)


def prompt_add(data):
    today = date.today().isoformat()
    day = ask(f"Date [YYYY-MM-DD, blank = {today}]: ", parse_date, today)
    cents = ask("Amount: ", parse_amount)
    category = ask_category(data)
    note = input("Note (optional): ")
    exp = add_expense(data, day, cents, category, note)
    save(data)
    print(f"  Added #{exp['id']}: {fmt(cents)} on {exp['category']}")


def prompt_edit(data):
    exp = ask_id(data)
    print("  Blank keeps the current value.")
    exp["date"] = ask(f"Date [{exp['date']}]: ", parse_date, exp["date"])
    exp["cents"] = ask(f"Amount [{fmt(exp['cents'])}]: ", parse_amount, exp["cents"])
    exp["category"] = ask_category(data, exp["category"]).lower()
    exp["note"] = input(f"Note [{exp['note']}]: ").strip() or exp["note"]
    save(data)
    print(f"  Updated #{exp['id']}.")


def prompt_delete(data):
    exp = ask_id(data)
    if input(f"Delete #{exp['id']} ({fmt(exp['cents'])} {exp['category']})? [y/N]: ").strip().lower() == "y":
        delete_expense(data, exp["id"])
        save(data)
        print("  Deleted.")


def prompt_summary(data):
    print("\n".join(summary_lines(data["expenses"], ask_month())))


def ask_month():
    this_month = date.today().isoformat()[:7]
    return ask(f"Month [YYYY-MM, blank = {this_month}]: ",
               lambda t: parse_date(t + "-01")[:7], this_month)


def prompt_budgets(data):
    while True:
        print("\n".join(budget_lines(data, date.today().isoformat()[:7])))
        choice = input("s) Set budget  r) Report for another month  b) Back\n> ").strip().lower()
        if choice == "s":
            category = ask_category(data)
            cents = ask("Monthly budget (0 = remove): ",
                        lambda t: 0 if t.strip() in ("0", "0.00") else parse_amount(t))
            set_budget(data, category, cents)
            save(data)
        elif choice == "r":
            print("\n".join(budget_lines(data, ask_month())))
        elif choice == "b":
            return


def prompt_search(data):
    print("  Blank skips a filter.")
    start = ask("From date: ", parse_date, "")
    end = ask("To date: ", parse_date, "")
    category = input("Category: ").strip()
    text = input("Note contains: ").strip()
    def parse_sort(t):
        if t.lower() not in SORT_KEYS:
            raise ValueError("enter date or amount")
        return t.lower()
    sort = ask("Sort by [date/amount, blank = date]: ", parse_sort, "date")
    desc = input("Descending? [y/N]: ").strip().lower() == "y"
    rows = filter_expenses(data["expenses"], start, end, category, text, sort, desc)
    print("\n".join(list_lines(rows, presorted=True)) if rows else "  No matches.")


def main():
    data = load()
    while True:
        print("\n== Expense Tracker ==\n1) Add expense\n2) List expenses\n3) Edit expense\n"
              "4) Delete expense\n5) Monthly summary\n6) Budgets\n7) Search & filter\nq) Quit")
        choice = input("> ").strip().lower()
        if choice == "q":
            break
        if choice in ("2", "3", "4", "5", "7") and not data["expenses"]:
            print("  No expenses yet.")
        elif choice == "6":
            prompt_budgets(data)
        elif choice == "7":
            prompt_search(data)
        elif choice == "1":
            prompt_add(data)
        elif choice == "2":
            print("\n".join(list_lines(data["expenses"])))
        elif choice == "3":
            prompt_edit(data)
        elif choice == "4":
            prompt_delete(data)
        elif choice == "5":
            prompt_summary(data)


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
    assert parse_date(" 2026-02-03 ") == "2026-02-03"
    for bad in ("2026-02-30", "03/02/2026", ""):
        try:
            parse_date(bad)
            raise AssertionError(f"accepted date {bad!r}")
        except ValueError:
            pass
    add_expense(data, "2026-09-03", 750, "food")
    add_expense(data, "2026-08-31", 9999, "rent")
    assert categories(data) == ["food", "rent", "transport"]
    total, rows = month_summary(data["expenses"], "2026-09")
    assert total == 2000 and rows[0][:2] == ("food", 1750)
    assert abs(sum(r[2] for r in rows) - 100) < 1e-9
    out = summary_lines(data["expenses"], "2026-09")
    assert "87.5%" in out[1] and out[1].endswith("#" * 30) and "$20.00" in out[-1]
    assert summary_lines(data["expenses"], "2020-01") == ["  No expenses in 2020-01."]
    assert budget_lines(data, "2026-09") == ["  No budgets set."]
    set_budget(data, " Food ", 1800)
    set_budget(data, "transport", 200)
    set_budget(data, "fun", 5000)
    rep = {r[0]: r for r in budget_report(data, "2026-09")}
    assert rep["food"] == ("food", 1800, 1750, 50, "WARN")
    assert rep["transport"] == ("transport", 200, 250, -50, "OVER")
    assert rep["fun"][4] == "ok" and rep["fun"][2] == 0
    out = budget_lines(data, "2026-09")
    assert any("transport is over budget by $0.50" in l for l in out)
    assert any("food has used 97%" in l for l in out)
    set_budget(data, "fun", 0)
    assert "fun" not in data["budgets"]
    exps = data["expenses"]
    assert [e["id"] for e in filter_expenses(exps)] == [4, 2, 1, 3]
    assert [e["id"] for e in filter_expenses(exps, start="2026-09-01", end="2026-09-02")] == [2, 1]
    assert [e["id"] for e in filter_expenses(exps, category=" FOOD")] == [1, 3]
    assert [e["id"] for e in filter_expenses(exps, text="LUN")] == [1]
    assert [e["id"] for e in filter_expenses(exps, sort="amount", desc=True)] == [4, 1, 3, 2]
    assert filter_expenses(exps, start="2027-01-01") == []
    assert delete_expense(data, 4)["category"] == "rent" and find(data, 4) is None
    assert delete_expense(data, 99) is None
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "e.json")
        save(data, p)
        assert load(p) == data
        assert load(os.path.join(d, "missing.json"))["expenses"] == []
    print("selfcheck OK")


if __name__ == "__main__":
    selfcheck() if "--selfcheck" in sys.argv else main()
