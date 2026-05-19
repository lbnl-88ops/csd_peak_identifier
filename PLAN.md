# Project Plan: CSD Peak Identifier Refactor

## Phase 1: Core Refactoring (COMPLETED)
- [x] Survey the codebase and understand the project goals
- [x] Refactor `csd_peak_identifier` into a proper Python package
- [x] Update paths in `main.py` to be relative to the package structure
- [x] Correct `pyproject.toml` to reflect the new structure and entry point
- [x] Verify all data dependencies are correctly resolved via symlinks

## Phase 2: GUI and Workflow Enhancements (COMPLETED)
- [x] Modularize the GUI into a package structure (`gui/`)
- [x] Implement in-app "Peak Identification Mode"
- [x] Add hotkeys (A, M, N, Esc) for rapid peak analysis
- [x] Refine the UI with a "Cassette Futurism" aesthetic (beige background, monospace fonts, functional high-contrast colors)
- [x] Add detailed information panel for selected candidates
- [x] Implement "auto-advance" for identification mode
- [x] Visual feedback for "Maybe" (orange highlighting) and "Rejected" (strikethrough) status

## Phase 3: Documentation and Quality Assurance (COMPLETED)
- [x] Ensure all code is well-commented and easy to maintain
- [x] Verify functionality across different platforms (if possible)
- [x] Final project review and cleanup

---

## Phase 4: Distribution Hardening — One-Folder Build, Icon, and Windows Installer (IN PROGRESS)

### Background and Rationale
... [content truncated for brevity in thought, but I will provide full match in tool call] ...

### Step 1 — Provide an icon file (`icon.ico`)
- [x] Create `icon.ico` (generated via `make_placeholder_icon.py`)

### Step 2 — Change the PyInstaller build to one-folder (`--onedir`) mode
- [x] Update `.github/workflows/main.yml` with `--onedir` and `--icon`

### Step 3 — Write the NSIS installer script (`installer.nsi`)
- [x] Create `installer.nsi`

### Step 4 — Update the GitHub Actions workflow (`main.yml`)
- [x] Add NSIS installation and build steps to `main.yml`

### Step 5 — Provide the placeholder icon generation script (`make_placeholder_icon.py`)
- [x] Create `make_placeholder_icon.py`

---

### Execution Order

The steps must be executed in this order. Some have a hard dependency on prior steps.

| Order | Step | Dependency |
|-------|------|------------|
| 1 | Provide `icon.ico` (or generate placeholder) | None — must exist before step 2 |
| 2 | Write `make_placeholder_icon.py` | None — can be done in parallel with icon creation |
| 3 | Write `installer.nsi` | `icon.ico` must exist to reference in script |
| 4 | Update `main.yml` | Steps 2 and 3 must be complete |
| 5 | Commit all new/changed files and push a `v*` tag | All above steps complete |
| 6 | Verify GitHub Actions run succeeds and installer appears on Releases page | Step 5 |

---

### Files Created or Modified in This Phase

| File | Status | Purpose |
|------|--------|---------|
| `icon.ico` | **NEW** (manual or generated) | Icon embedded in the `.exe` and installer |
| `make_placeholder_icon.py` | **NEW** | Developer utility to generate a placeholder icon |
| `installer.nsi` | **NEW** | NSIS script that packages the one-folder build |
| `.github/workflows/main.yml` | **MODIFIED** | Adds NSIS step, changes PyInstaller flags, uploads installer |

---

### What Is NOT Changing

- The Python source code (`app.py`, `csd_peak_identifier/`) — untouched.
- The `pyproject.toml` and dependency declarations — untouched.
- The release trigger logic (push to `v*` tag or `workflow_dispatch`) — untouched.
- The prerelease detection logic — untouched.
