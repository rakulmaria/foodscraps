# Foodscraps: A Data Pipeline for Restaurant Menu Carbon Footprinting in Copenhagen

This research project was developed at the IT University of Copenhagen (ITU) during Spring 2026 as part of a 5th semester MSc course.
The project was supervised by [Vedran Sekara](https://vedransekara.github.io/).
The project investigates the Copenhagen restaurant landscape as groundwork for research into food-related carbon footprints and climate choices. It scrapes all restaurants within Copenhagen from the Google Maps Places API, uses LLMs to collect menu data, and analyses the results across models and prompts.
The project was developed by Rakul Maria Hjalmarsdóttir Tórgarð.

---

## Package management

Dependencies are managed with [uv](https://github.com/astral-sh/uv).

```bash
# install uv (if not already installed)
curl -Lf https://astral.sh/uv/install.sh | sh

# create virtual environment and install all dependencies
uv sync

# activate the virtual environment
source .venv/bin/activate
```

Dependencies are declared in [pyproject.toml](pyproject.toml). Dev dependencies (ruff linter) are in the `[dependency-groups]` section and are installed automatically by `uv sync`.

A `.env` file is required at the repo root with the following keys:

```
MAPS_PLATFORM_API_KEY=<your_google_maps_key>
LLMGATEWAY_API_KEY=<your_llmgateway_key>
```

---

## Codebase structure

```
foodscraps/
├── src/
│   ├── foodscraper/            # installable Python package
│   │   ├── config.py           # ROOT_DIR / DATA_DIR / RUNS_DIR / GOOGLE_MAPS_DIR path constants
│   │   ├── logger.py           # logging setup
│   │   ├── data_collector.py   # Google Maps Places API calls (nearby search, area insights)
│   │   ├── quadtree.py         # quadtree scraper — entry point for data collection
│   │   ├── data_cleaner.py     # loads + cleans the raw JSON into a pandas DataFrame
│   │   ├── menu_finder.py      # LLM menu scraping via llmgateway.io
│   │   └── streamlit_app.py    # interactive dashboard with all visualisations
│   └── notebooks/              # Jupyter notebooks for exploration and analysis
│       ├── explorer.ipynb
│       ├── plot_exporter.ipynb
│       └── respones_analyzer.ipynb
├── data/                       # gitignored — local only
│   ├── sources/
│   │   └── google-maps-api/    # raw restaurant data fetched from Google Maps Places API
│   └── runs/
│       └── YYYY-MM-DD/         # dated LLM run outputs
│           ├── responses/      # parsed CSV responses per model
│           └── raw_responses/  # raw JSONL API responses per model
├── plots/                      # exported SVG figures (output of plot_exporter.ipynb)
├── prompts/                    # versioned LLM prompt files (named by date)
├── docs/                       # reference literature and project documents (PDFs, Gantt chart)
├── foodscraper.wiki/           # project wiki (meeting notes, literature, todos)
├── pyproject.toml              # project metadata and dependencies
├── uv.lock                     # locked dependency tree
├── .python-version             # pinned Python version (3.12)
├── .pre-commit-config.yaml     # pre-commit hooks (commitlint + end-of-file fixer)
└── commitlint.config.js        # conventional commits ruleset
```

### Key modules

`quadtree.py`: the data collection entry point. Defines a `BoundingBox` and `Node` class that together implement a [quadtree](https://en.wikipedia.org/wiki/Quadtree) over the Copenhagen bounding box. Because the Google Maps Nearby Search API caps results at 20 per query, a cell is recursively split into four quadrants whenever it returns ≥ 10 results, guaranteeing that no restaurants are missed. After traversal, `collect_results()` walks the leaf nodes and deduplicates by place ID.

`data_collector.py`: thin wrappers around the Google Maps Places API (New). `nearby_search()` is the core call used by the quadtree. `find_aggregated_places()` uses the Area Insights API to count total restaurants in a polygon (used for validation).

`data_cleaner.py`: `get_df()` loads the collected JSON, selects the relevant columns, keeps only `OPERATIONAL` restaurants, and unwraps nested location/name dictionaries into flat columns.

`menu_finder.py`: sends restaurant data to LLMs via [llmgateway.io](https://llmgateway.io) and instructs them to locate digital menus. Results are saved to `data/runs/<date>/` as both CSV and raw JSONL per model.

`streamlit_app.py`: builds and renders five charts:
- 2D histogram density map of restaurant locations
- Top 20 restaurant types (bar chart)
- Quadtree cell visualisation (shows how the bounding box was subdivided)
- Vegetarian food availability by Copenhagen district (stacked horizontal bar)
- Rating vs. price range (box plot)

---

## Commit message guidelines

Commits that don't follow the [Conventional Commits](https://www.conventionalcommits.org/) hooks will be rejected.

### Format
```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

- **`type`** — required, lowercase
- **`scope`** — optional, lowercase, describes what part of the codebase is affected
- **`subject`** — required, lowercase, no trailing period, max 100 characters total in the header

### Acceptable types

| Type | When to use |
|----------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, whitespace — no logic changes |
| `refactor` | Code restructuring without fixing a bug or adding a feature |
| `perf` | Performance improvements |
| `test` | Adding or updating tests |
| `build` | Changes to the build system or external dependencies |
| `ci` | Changes to CI configuration or scripts |
| `chore` | Miscellaneous tasks that don't change source or tests |
| `revert` | Reverting a previous commit |

### Examples
```bash
# Minimal
git commit -m "fix: handle null response from API"

# With scope
git commit -m "feat(auth): add OAuth2 login flow"

# With body
git commit -m "refactor(db): simplify query builder

Extracted filter logic into a separate helper function
to improve readability and testability."

# Breaking change via footer
git commit -m "feat(api)!: drop support for v1 endpoints

BREAKING CHANGE: all v1 routes have been removed, migrate to v2."
```

### Breaking changes

A breaking change can be signalled in two ways:
```bash
# Using ! after the type
feat!: remove deprecated config option

# Using a footer
feat: remove deprecated config option

BREAKING CHANGE: the `legacyMode` config key is no longer supported.
```
