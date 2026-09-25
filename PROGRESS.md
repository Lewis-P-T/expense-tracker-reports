# Expense Tracker (Reports) — Progress

Python CLI. Log expenses by category to a JSON file, with monthly summaries, budgets, trends and CSV export. Stdlib only.

- [x] 1. Skeleton: menu-driven CLI, add expense (date/amount/category/note), list expenses, JSON persistence, amounts stored as integer cents, `--selfcheck` flag.
- [x] 2. Robust input: date/amount validation with re-prompt, category suggestions from existing data; edit and delete an expense by id.
- [x] 3. Monthly summary: totals per category for a chosen month, percentage share, and an ASCII bar chart.
- [x] 4. Budgets: set per-category monthly budgets (saved), report over/under/remaining for a month with warnings.
- [x] 5. Search & filter: by date range, category, and note text; sortable by date or amount.
- [ ] 6. CSV export and import (csv module), with duplicate detection on import and a round-trip check.
- [ ] 7. Trends report: month-over-month change per category, 3-month rolling average, top categories across all months.
- [ ] 8. Polish: cleaner menu formatting, empty-data guards, README with run instructions, extended assert-based self-check.
