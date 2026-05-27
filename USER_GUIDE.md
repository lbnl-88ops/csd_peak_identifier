# CSD Peak Identifier – User Guide

---

## 1. Login & Operator IDs
1. **Start the Application** – On launch, the main window opens, followed by the **ECRIS System Access** (Welcome) dialog.
2. **Operator ID** – Select your ID from the dropdown or type a new Operator ID.
3. **Quick-Start Actions**:
   - **OPEN A CSD**: Select a file from the local filesystem.
   - **EVALUATE PENDING CSD**: Load a random file analyzed by others but not yet by you (Peer Review).
   - **EVALUATE RANDOM CSD**: Load a random file from the server.
4. **Login** – Your Operator ID is persisted locally. To change it later, use **File > Switch Operator...**.

---

## 2. Main Spectrum View & Navigation
The central panel displays the spectral data.

### Zoom / Reset
- **ZOOM Button**: Toggle the zoom tool. When active, click and drag a box on the plot to zoom in. The tool auto-deactivates after one use.
- **RESET VIEW Button**: Instantly returns to the full spectral range.
- **Mouse Navigation**: Standard Matplotlib mouse interactions (middle-click pan, right-click zoom) are also supported.

---

## 3. Peak Identification Mode
Enter this mode by clicking **"IDENTIFY PEAKS"** or selecting a candidate from the Isotope Panel.

### Hotkeys
| Key | Action |
|-----|--------|
| **A** | **ACCEPT**: Confirms the isotope for this peak and moves to the next. |
| **M** | **MAYBE**: Marks the isotope as a possibility and moves to the next. |
| **N** | **NEXT**: Skips the current candidate and moves to the next. |
| **Esc** | **EXIT**: Leaves Identification Mode and returns to inspection. |

### Auto-Advance
The system automatically cycles through candidates. Once an isotope is Accepted or Marked as Maybe, it appears in the Evaluation List with a green (Accept) or orange (Maybe) highlight.

---

## 4. Saving Evaluations
When your analysis is complete:
1. Review your results in the **Isotope Panel** (Evaluation List).
2. Click the large **"SAVE EVALUATION"** button at the bottom of the panel, or use **File > Save Evaluation (Ctrl+S)**.
3. The result is saved to the database. If successful, you will be prompted to either review another CSD or stay on the current one.

---

## 5. Shared Database & Connectivity
The application can operate in two modes, indicated in the bottom-right of the status bar:

- **DB: REMOTE (Green)**: Connected to the lab's shared database at `ecris.lbl.gov`. This requires a VPN connection if you are off-site.
- **DB: LOCAL (Gray)**: Connected to your local `profiles.db`. Useful for offline work.
- **DB: REMOTE (OFFLINE) (Red)**: Remote mode is enabled, but the server cannot be reached.

Toggle this in **File > Preferences**.

---

## 6. Updates
The application automatically checks for new versions on GitHub.
- Use **File > Check for Updates** to manually trigger a check.
- Use **File > Preferences** to toggle automatic checks on startup.
- Updates are distributed via a Windows Installer (.exe) or macOS Disk Image (.dmg).

---

*End of User Guide (v0.2.0)*
