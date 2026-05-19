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

## Phase 6: macOS Distribution (IN PROGRESS)

### Overview
Add a macOS build job to the CI/CD pipeline that produces a distributable `.dmg` disk image
containing a `.app` bundle. The build runs on `macos-latest` GitHub Actions runners
(Apple Silicon, arm64). No Apple Developer account or notarization is required for internal
distribution; ad-hoc code signing (performed automatically by PyInstaller) is sufficient.

### Prerequisites / Key Decisions
- **Icon format**: `icon.png` is 256x256 RGBA PNG — must be converted to `icon.icns`
  (multi-resolution Apple icon) using `sips` + `iconutil` (both ship with macOS).
  No third-party tools needed.
- **App bundle**: PyInstaller with `--windowed --onedir` produces `dist/peak_identifier.app`
  on macOS automatically. The `--windowed` flag is the macOS trigger.
- **DMG packaging**: Use `create-dmg` (installable via `brew install create-dmg`).
  Produces a clean disk image with an Applications symlink for drag-to-install UX.
- **Code signing**: PyInstaller performs ad-hoc signing automatically on macOS. This is
  sufficient for lab-internal distribution. Notarization (Apple Developer Program, $99/yr)
  is NOT required and is out of scope.
- **Menu bar**: `setNativeMenuBar(False)` is already set in `main_window.py` — the macOS
  native menu bar takeover is already neutralised. No additional code changes needed.
- **`--add-data` separator**: macOS/Linux uses `:` not `;` (Windows). The build command
  must use the correct separator for the runner OS.
- **Poetry dependency group**: A new `macos-build` group mirrors the `windows-build` group,
  containing `pyinstaller` and `pillow`.

### Step-by-Step Execution Plan

#### Step 6.1 — Add `macos-build` dependency group to `pyproject.toml`
Add a `[tool.poetry.group.macos-build]` section analogous to `windows-build`.
Dependencies: `pyinstaller ^6.18.0`, `pillow ^11.0.0`.

#### Step 6.2 — Generate `icon.icns` inside the CI workflow
Use a shell script block inside the GitHub Actions job:
1. Create a temporary `icon.iconset/` directory.
2. Use `sips` to resize `icon.png` to each required resolution
   (16, 32, 64, 128, 256, 512 px, plus @2x variants).
3. Run `iconutil --convert icns icon.iconset` to produce `icon.icns`.
This runs natively on the macOS runner; no Python or third-party tools required.

#### Step 6.3 — Run PyInstaller to produce the `.app` bundle
Command:
```
poetry run pyinstaller \
  --noconsole \
  --name peak_identifier \
  --onedir \
  --icon icon.icns \
  --add-data "icon.png:." \
  --add-data "data:data" \
  app.py
```
Output: `dist/peak_identifier.app`

#### Step 6.4 — Package `.app` into a `.dmg` using `create-dmg`
Install via `brew install create-dmg`, then run:
```
create-dmg \
  --volname "CSD Peak Identifier" \
  --window-size 540 380 \
  --icon-size 128 \
  --icon "peak_identifier.app" 140 185 \
  --app-drop-link 400 185 \
  --skip-jenkins \
  "CSD_Peak_Identifier.dmg" \
  "dist/"
```
`--skip-jenkins` is required: GitHub Actions runners are headless (no Finder/GUI), and
the AppleScript cosmetic step would fail without it.
Output: `CSD_Peak_Identifier.dmg`

#### Step 6.5 — Upload `.dmg` to the GitHub Release
Extend the existing `softprops/action-gh-release@v2` step (or add a parallel one in the
macOS job) to upload `CSD_Peak_Identifier.dmg` alongside the Windows installer.

#### Step 6.6 — Validate and test
- Confirm the CI workflow triggers correctly on `v*` tags and `workflow_dispatch`.
- Verify the `.dmg` mounts and the `.app` launches (requires a macOS machine or VM).
- Confirm the Windows build is unaffected.

### Known Constraints and Gotchas
- `--skip-jenkins` is MANDATORY in CI; without it `create-dmg` will hang waiting for
  Finder AppleScript that cannot run in a headless environment.
- macOS runner is arm64 (Apple Silicon). The resulting app will run natively on M-series
  Macs and via Rosetta 2 on Intel Macs (Python 3.13 universal2 wheels cover both).
- The `--add-data` separator is `:` on macOS (not `;` as on Windows). This is different
  from the Windows build command and must not be cross-contaminated.
- `setNativeMenuBar(False)` is already set — the macOS system menu bar override is
  neutralised. No code changes to `main_window.py` are needed.
- Gatekeeper will warn users on first launch ("unidentified developer") because the app
  is ad-hoc signed, not notarized. Users must right-click > Open the first time.
  This is acceptable for lab-internal distribution and should be documented.
- Do not use `--onefile` on macOS; it requires unpacking on every run and cannot be
  sandbox-signed, which worsens the Gatekeeper experience.
