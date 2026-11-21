# CLAUDE.md

Causalitty is a PySide6 desktop app that helps researchers build a causal graph
(CPDAG) from their own domain knowledge, check it against a dataset, and patch
it where the data disagrees, without writing code. It sits between manual tools
like DAGitty and fully automatic causal discovery algorithms.

## What the app does

1. **Start:** create a new project (import a dataset; its variables become
   nodes in an empty graph) or load a saved one. Projects can be saved and
   reloaded at any time. CPDAGs can also be imported from DAGitty.
2. **Build the CPDAG:** editing should feel nearly identical to DAGitty
   (select, drag, add/remove edges). Edges are directed or undirected.
3. **Domain Search:** the user selects variables; for every pair the app fetches
   meta-analysis abstracts from PubMed and asks an LLM which edge fits:
   directed, undirected, or none.
   - Meta-analyses that disagree on direction → undirected edge.
   - Meta-analyses that disagree on whether a link exists → show the user a
     summary of the claims and let them decide.
   - Suggested edges are highlighted, optional, and accepted or rejected one by
     one.
   - Batch 2–5 pairs per LLM prompt and run pairs in parallel (the LLM, not the
     CPU, should be the bottleneck). Only abstracts are sent, never full texts.
4. **CI Tests:** derive every conditional independence the graph implies
   (d-separation) and test each one against the dataset, singly or all at once,
   from the CI panel. Partial correlation for continuous data, Chi-squared for
   discrete. Show pass (green check) / fail (red cross) with p-values and
   estimates.
5. **GES Fix:** when CI tests fail, patch the graph with a modified Greedy
   Equivalence Search. It starts from the user's graph, not an empty one, and
   makes as few changes as possible. Score:
   `S(G) = BIC(G | D) − γ · SHD(G, G_orig)`, where SHD counts edge additions,
   deletions and flips from the original graph, and γ > 0 is set by the user
   (higher keeps more of the original graph).

## Technical requirements

- External services (PubMed, the LLM provider) sit behind their own
  interfaces so they can be swapped without touching the rest of the app.
  Custom / local LLMs must be supported.
- Datasets can be larger than RAM: compute CI statistics from chunks
  (covariance matrices, contingency tables) instead of loading the whole file.
- The graph canvas must stay smooth (30 fps) while dragging on large graphs.
- Ships as a standalone executable via PyInstaller; users don't install Python.
- Libraries: PySide6 (UI), pgmpy (graphs, CI tests, discovery), numpy / pandas
  (data), google-genai (LLM), requests (PubMed).

## Running

- Use the project's virtual environment: `.venv\Scripts\python.exe`.
- Run the app from the repo root: `.venv\Scripts\python.exe src\main.py`.
- Imports are relative to `src/` (e.g. `from models.app_info import ...`), so
  run inline scripts / `python -c` checks from inside `src/`.
- Without a screen (quick checks), set `QT_QPA_PLATFORM=offscreen`.

## Project layout (`src/`)

- `main.py`: entry point; shows the splash screen, then the main window.
- `screens/`: every screen / window / dock (main screen, splash, CI panel).
- `graph_editor/`: the self-contained graph editor widget (scene, nodes, arrows).
- `CPDAG/`: the graph model and the CI logic, with no UI code.
- `models/`: all shared statics and config (variable types, colors, app name,
  window size, splash steps).

## Architecture & Rules

- Every screen / container goes inside `src/screens`, except fully built
  widgets like `graph_editor`.
- All statics / configs (colors, names, sizes, settings shared across files)
  live in `src/models` as plain Python values (hex strings, not `QColor`).
  Sizes that belong to one widget stay as named constants on its class; don't
  leave magic numbers inline.
- Use `qtawesome` for icons (e.g. `qta.icon("mdi6.play")`), not fixed-color
  icons like `QStyle.standardIcon`, so they follow light and dark mode.
  qtawesome caches icons in the current text color, so on a
  `QEvent.PaletteChange` call `qta.reset_cache()` and set the icons again.
- Make every file runnable on its own for testing when possible
  (`if __name__ == "__main__":`).
- Don't overuse comments. Use them to explain the general purpose of the code,
  or to describe a piece of code that's hard to understand.

## Git & GitHub

- Before every commit, check that `requirements.txt` matches the venv
  (`.venv\Scripts\python.exe -m pip freeze`) and update it if a package was
  added, removed or upgraded. Keep it UTF-8: write it with
  `pip freeze | Out-File -Encoding utf8 requirements.txt`, never a plain
  PowerShell `>` redirect, which can produce UTF-16.
- Don't add yourself to commits (no `Co-Authored-By` or other AI attribution).
  Some code is written manually and you're only committing it to get good
  commit messages.
- Commit every change on its suitable branch, and suggest a new branch when
  needed.
- Never merge unless asked, except updating the current branch from `main`.
- Never push unless asked.
