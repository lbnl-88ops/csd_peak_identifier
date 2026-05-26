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

## Phase 4: Distribution Hardening — Windows Installer and Icon Integration (COMPLETED)
- [x] Provide a multi-resolution `icon.ico` (256x256 pixel art style)
- [x] Change the PyInstaller build to one-folder (`--onedir`) mode
- [x] Write the NSIS installer script (`installer.nsi`)
- [x] Update `.github/workflows/main.yml` with NSIS installation and build steps
- [x] Update `csd_peak_identifier/gui/constants.py` with `get_resource_path` for icon resolution

## Phase 5: Update Infrastructure (COMPLETED)
- [x] Use `QSettings` to store user preferences (e.g., "Check for updates automatically")
- [x] Implement GitHub API integration to query latest releases
- [x] Filter out "pre-releases" from update notifications to allow for internal beta testing
- [x] Add "File > Check for Updates" and "File > Preferences" menu items
- [x] Force traditional menu bar visibility with `setNativeMenuBar(False)`
- [x] Apply tactile, bordered aesthetic to menus via QSS
- [x] Implement non-blocking background thread for update checks
- [x] Use platform-specific, user-writable `TEMP_FOLDER` (%LOCALAPPDATA% on Windows)

## Phase 6: macOS Distribution (COMPLETED)
- [x] Add `macos-build` dependency group to `pyproject.toml`
- [x] Generate `icon.icns` inside the CI workflow using `sips` and `iconutil`
- [x] Update `.github/workflows/main.yml` with macOS build and DMG packaging steps
- [x] Package `.app` into a `.dmg` using `create-dmg`
- [x] Upload `.dmg` to the GitHub Release alongside the Windows installer

## Phase 7: Profile/Login System (COMPLETED)
- [x] Implement local database persistence using SQLite (`profiles.db`)
- [x] Create "Cassette Futurism" Profile Selection UI (`ProfileDialog`)
- [x] Support selecting from existing operators or creating new ones
- [x] Persist the "last used" operator via `QSettings` and database timestamps
- [x] Integrate login flow into application startup
- [x] Add "File > Switch Operator..." for on-the-fly profile changes
