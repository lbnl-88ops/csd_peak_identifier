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

## Phase 8: Evaluation Saving (COMPLETED)
- [x] Extend `profiles.db` with `evaluations` and `evaluation_isotopes` tables
- [x] Implement `save_evaluation` method in `DatabaseManager`
- [x] Add "File > Save Evaluation" (Ctrl+S) to the main menu
- [x] Implement `save_current_evaluation` in the `Coordinator` to persist analysis results
- [x] Provide visual feedback via the status bar upon successful save

## Phase 9: Evaluation Mode and Unified Welcome Screen (COMPLETED)
- [x] Implement `get_user_stats` and `get_random_pending_timestamp` in `DatabaseManager`
- [x] Create "Evaluation Status" summary dialog (`EvaluationModeDialog`)
- [x] Implement "Evaluate pending CSD" and "Evaluate random CSD" logic in `Coordinator`
- [x] Add "File > Evaluation Mode..." to the main menu
- [x] Create unified **Welcome Dialog** with quick-start actions (Open, Pending, Random)
- [x] Refine startup flow: Application opens, window shows, Welcome Dialog overlays

## Phase 10: Remote Shared Database (COMPLETED)
- [x] Implement `RemoteDatabaseBackend` for REST communication with `ecris.lbl.gov`
- [x] Refactor `DatabaseManager` as a smart dispatcher (Remote first, Local fallback)
- [x] Implement server-side database endpoints in `csd-server` repository
- [x] Extend `PreferencesDialog` with "Use Remote Shared Database" toggle
- [x] Add color-coded DB status indicator to the main window status bar
- [x] Configure server-side persistence path in `systemd` environment file
- [x] Standardize absolute imports for cross-module reliability

## Phase 11: Documentation and User Education (COMPLETED)
- [x] Draft a comprehensive User Guide in Markdown
- [x] Explain "Cassette Futurism" UI elements and tactile controls
- [x] Document hotkeys (A, M, N, Esc) and Identification Mode workflow
- [x] Provide instructions for Profile management and Shared Database use
- [x] Include a "Troubleshooting" section for VPN/Remote issues

## Phase 12: Cross-Evaluation Analysis and Comparison (COMPLETED)
- [x] Research requirements for cross-operator evaluation comparison
- [x] Design an "Evaluation Review" or "Consensus" view
- [x] Implement logic to pull and overlay multiple evaluations for the same CSD
- [x] Visualize agreement/disagreement between researchers (e.g., color-coded isotopes)
- [x] Add an "Analysis Dashboard" for lab-wide progress tracking

## Phase 13: Analysis Configuration (COMPLETED)
- [x] Define `user_peak_parameters` table in local database
- [x] Create `PeakParametersDialog` for per-user analysis configuration
- [x] Add "Analysis" menu with "Peak search parameters..." action
- [x] Persist peak search parameters (min_height, threshold, distance, prominence, etc.) per-user
- [x] Automatically load user-specific parameters on login/switch
- [x] Prompt user to reload/re-calibrate CSD when parameters are modified
- [x] Integrate custom parameters into the `load_and_calibrate_csd` logic
- [x] Add visual guide image (`peak_description.png`) to the configuration dialog

## Phase 14: Ruler Enhancements and Polish (COMPLETED)
- [x] Implement q-range filtering (min/max) for the Charge State Ruler
- [x] Add second ruler option for custom mass reference
- [x] Ensure rulers are stacked and color-coded when both are active
- [x] Automatically adjust plot margins to accommodate multiple rulers
