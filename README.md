# Expense Tracker (Reports)

Menu-driven Python CLI for logging expenses by category, with monthly summaries,
budgets, search, CSV import/export and trend reports. Standard library only —
no install step.

## Run

```
git clone https://github.com/Lewis-P-T/expense-tracker-reports
cd expense-tracker-reports
python expense_tracker.py              # run the app
python expense_tracker.py --selfcheck  # run the built-in tests
```

Data is saved to `expenses.json` next to the script (amounts stored as integer cents,
written atomically). If that file is corrupt the app refuses to start rather than
overwrite it.

## Features

| Key | Feature |
|-----|---------|
| 1 | Add an expense (date, amount, category, note) with validation and category suggestions |
| 2 | List all expenses with a total |
| 3 / 4 | Edit or delete an expense by id |
| 5 | Monthly summary: per-category totals, % share and an ASCII bar chart |
| 6 | Per-category monthly budgets with OVER / WARN (90%) status |
| 7 | Search by date range, category and note text; sort by date or amount |
| 8 / 9 | CSV export and import (duplicates skipped, bad rows reported) |
| t | Trends: month-over-month change, 3-month rolling average, top categories |
