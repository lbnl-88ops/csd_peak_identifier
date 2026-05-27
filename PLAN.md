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

## Phase 9: Evaluation Mode (COMPLETED)
- [x] Implement `get_user_stats` and `get_random_pending_timestamp` in `DatabaseManager`
- [x] Create "Evaluation Status" summary dialog (`EvaluationModeDialog`)
- [x] Implement "Evaluate pending CSD" and "Evaluate random CSD" logic in `Coordinator`
- [x] Add "File > Evaluation Mode..." to the main menu

---

## Phase 10: Remote Shared Database

### Mission Objective
Transition evaluation data from a per-machine local SQLite file to a shared, multi-user database
so that all operators' evaluations are visible to one another (enabling "pending CSD" cross-user
workflow). The local SQLite file remains as an offline fallback cache.

### Architecture Decision: REST API Extension (DO NOT expose a raw database port)
The existing `ecris.lbl.gov:5000` Flask server already handles CSD file serving. We extend it
with `/db/...` endpoints that mirror the six public methods of `DatabaseManager`. The client
remains a Python class with the identical interface — only the backend transport changes.

    Client (DatabaseManager)
      |-- online  --> HTTP requests to ecris.lbl.gov:5000/db/...  --> server-side SQLite/PostgreSQL
      |-- offline --> falls back to local ~/.local/share/csd_peak_identifier/profiles.db

This approach:
- Requires no firewall changes (already-open HTTP port)
- Requires no database driver installation on client machines
- Keeps credentials on the server only; clients authenticate with a shared API key
- Provides a natural offline fallback with zero GUI changes

### Security: Credential Management
- A shared API key (a random hex string, NOT a password) is stored in `~/.config/csd_peak_identifier/config.ini` (or `%APPDATA%\CSDPeakIdentifier\config.ini` on Windows).
- The key is NEVER hardcoded in source code or committed to the repo.
- The server validates the key on every `/db/` request.
- A "Remote Settings" section in Preferences allows the operator to set the API URL and paste the API key.
- If no key is configured, the app silently operates in local-only mode.

### Schema: No structural changes required
The three existing tables (`users`, `evaluations`, `evaluation_isotopes`) are correct and
sufficient. The server will host this schema. The client's local SQLite mirror uses the
same schema as a write-back cache.

### Step-by-Step Implementation

#### Step 10.1 — Server-Side API Endpoints (YOU provide the science/data decisions; we code)
Define and implement six REST endpoints on the existing Flask server at `ecris.lbl.gov:5000`:

    GET  /db/users                          -> get_all_users()
    POST /db/users                          -> add_user(username)
    PUT  /db/users/<username>/last_used     -> update_last_used(username)
    DELETE /db/users/<username>             -> delete_user(username)
    GET  /db/users/<username>/stats         -> get_user_stats(username)
    GET  /db/users/<username>/pending       -> get_random_pending_timestamp(username)
    POST /db/evaluations                    -> save_evaluation(username, csd_timestamp, isotopes)

All endpoints require the `X-API-Key` header. Server returns JSON. On error, server returns
`{"error": "..."}` with an appropriate HTTP status code.

NOTE: The server-side implementation is a separate repository/task. This plan covers the
CLIENT-SIDE changes only. Server work requires your involvement for deployment decisions.

#### Step 10.2 — `RemoteDatabaseBackend`: HTTP adapter class
Create `csd_peak_identifier/utils/remote_db.py`:
- Class `RemoteDatabaseBackend` with the same six public method signatures as `DatabaseManager`.
- Each method makes an HTTP request to the corresponding `/db/` endpoint.
- Uses `requests` (already a dependency) with a configurable timeout (default: 3 seconds).
- On `requests.exceptions.ConnectionError`, `Timeout`, or non-2xx response: raises
  `RemoteUnavailableError` (a custom exception defined in the same file).
- No SQLite imports. Pure HTTP.

#### Step 10.3 — Refactor `DatabaseManager` as a dispatcher
Modify `csd_peak_identifier/utils/database.py`:
- `DatabaseManager.__init__` reads config (API URL + API key) from the OS config file.
- If config is present and valid, instantiates `RemoteDatabaseBackend` as `self._remote`.
- Every public method: tries `self._remote.method(...)` first; on `RemoteUnavailableError`,
  logs a warning and falls back to the local SQLite implementation.
- The local SQLite path and all existing local methods remain unchanged.
- Add `self.is_online: bool` property reflecting last known connection state.

#### Step 10.4 — Config file read/write utility
Create `csd_peak_identifier/utils/config.py`:
- Uses Python stdlib `configparser` only (no new dependencies).
- `get_remote_config() -> dict | None`: reads `[remote]` section with keys `api_url` and `api_key`.
  Returns `None` if file does not exist or section is missing.
- `set_remote_config(api_url, api_key)`: writes the config file.
- Config file path: `APP_DATA_DIR / "config.ini"` (already-defined constant, OS-appropriate).

#### Step 10.5 — Preferences UI: "Remote Database" tab
Modify `csd_peak_identifier/gui/preferences_dialog.py`:
- Add a "Remote Database" section below the existing auto-update checkbox.
- Fields: "API URL" (text input, pre-filled from config) and "API Key" (password input, masked).
- "Test Connection" button: calls `DatabaseManager.ping()` (new method, returns bool) and
  shows a status line: "CONNECTED" (green) or "UNREACHABLE" (red).
- On Save: writes values to config file via `set_remote_config()`.
- If fields are blank on Save: clears remote config (reverts to local-only mode).

#### Step 10.6 — Status bar connection indicator
Modify `csd_peak_identifier/gui/main_window.py`:
- Add a persistent label on the RIGHT side of the status bar: "DB: REMOTE" or "DB: LOCAL".
- Updated on login and after every Save Evaluation attempt.
- No color — text-only, consistent with cassette futurism philosophy.

#### Step 10.7 — Sync on startup (optional, deferred)
On login (after credentials are confirmed), if remote is available:
- Pull down all evaluations not present in local cache and write them to local SQLite.
- This ensures the "pending" count is correct even after a period offline.
- Implemented as a background thread (same pattern as update checker).
- DEFER this step until Steps 10.1–10.6 are confirmed working.

### Constraints Honored
- `DatabaseManager` public interface is UNCHANGED. GUI and Coordinator require zero edits.
- Credentials never hardcoded. Config file is in the user's OS data directory (gitignored).
- Connection failures are caught and logged; app continues in local mode transparently.
- No new dependencies: `requests` already present; `configparser` is stdlib.
- Server-side database choice (SQLite vs PostgreSQL) is YOUR decision — the client doesn't care.

### Open Questions for the Scientist (YOU must answer before Step 10.1 begins)
1. **Server DB backend**: Should the server use a single SQLite file (simplest, fine for <10 concurrent users) or PostgreSQL (necessary for high write concurrency)? For a lab with ~5 operators, SQLite is adequate.
2. **API key distribution**: How will new operators receive the shared key? (Suggested: a README in a private lab share, or the PI emails it.)
3. **Who deploys the server?** The Flask server already runs. Who has SSH access to add the new endpoints and restart the service?
4. **Write conflict policy**: If two operators save evaluations for the same CSD simultaneously, both are recorded (separate rows, both valid). Is that acceptable, or should we lock/warn?

### Files to be Created/Modified
    NEW:   csd_peak_identifier/utils/remote_db.py
    NEW:   csd_peak_identifier/utils/config.py
    MOD:   csd_peak_identifier/utils/database.py     (dispatcher logic)
    MOD:   csd_peak_identifier/gui/preferences_dialog.py  (remote settings UI)
    MOD:   csd_peak_identifier/gui/main_window.py    (DB mode indicator)
    SERVER-SIDE (separate repo): new /db/ endpoints on ecris.lbl.gov:5000

### Steps
- [ ] 10.1 Answer open questions and confirm server-side deployment plan (SCIENTIST required)
- [ ] 10.2 Implement `RemoteDatabaseBackend` in `remote_db.py`
- [ ] 10.3 Implement `config.py` utility
- [ ] 10.4 Refactor `DatabaseManager` as remote/local dispatcher
- [ ] 10.5 Extend `PreferencesDialog` with remote settings UI
- [ ] 10.6 Add DB mode indicator to status bar
- [ ] 10.7 Server-side endpoint implementation (coordinate with server admin)
- [ ] 10.8 Integration test: online mode, offline fallback, credential rejection
- [ ] 10.9 (Deferred) Startup sync of remote evaluations to local cache
