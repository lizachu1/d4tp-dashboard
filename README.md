# d4tp-dashboard
D4TP Coalition Dashboard - auto-deployed to d4tp.netlify.app

## Data landscape (`data-landscape/`)

A map of California's cradle-to-career data systems, from birth through early care, TK-12, college and work.

- `data-landscape/index.html`: interactive dashboard (journey map, linkage network, identifier relay, gap heatmap, source explorer, 10-year roadmap). Linked from the main dashboard's tab bar.
- `data-landscape/REPORT.md`: gap analysis and 10-year linkage strategy recommendations.
- `data-landscape/data/`: the database as CSV and JSON, plus `DATA_DICTIONARY.md`.
- `data-landscape/scripts/build_data.py`: single source of truth for the database. Edit it and run `python3 data-landscape/scripts/build_data.py` to regenerate every data file.
