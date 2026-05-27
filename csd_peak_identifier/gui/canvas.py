from collections import deque
from itertools import product
from PySide6.QtCore import Signal
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
from csd_peak_identifier.gui.constants import (
    COLOR_BG,
    COLOR_PLOT_BG,
    COLOR_TARGET,
    COLOR_CANDIDATE,
    COLOR_TEXT,
    MARKERS,
    SHADES,
    COLOR_GRID,
    COLOR_ACTION
)


class MqPlotCanvas(FigureCanvas):
    zoom_finished = Signal()

    def __init__(self, parent=None):
        fig = Figure(figsize=(9, 6), facecolor=COLOR_BG)
        self.axes = fig.add_subplot(111, facecolor=COLOR_PLOT_BG)
        self.axes.set_xlabel("m/q")
        self.axes.set_ylabel(r"Beam Current ($\mu$A)")
        self.axes.xaxis.set_major_locator(MultipleLocator(1.0))
        super().__init__(fig)
        self.setParent(parent)
        self.on_mq_clicked = None
        self.mpl_connect("button_press_event", self._on_click)
        
        # Use a hidden NavigationToolbar to leverage its high-quality zoom logic
        self.toolbar = NavigationToolbar(self, parent)
        self.toolbar.hide()
        
        # Wrap release_zoom to detect when a user finished dragging a zoom box
        orig_release_zoom = self.toolbar.release_zoom
        def wrapped_release_zoom(event):
            orig_release_zoom(event)
            if self.toolbar.mode == 'zoom rect': # Only emit if we were actually zooming
                 self.zoom_finished.emit()
        self.toolbar.release_zoom = wrapped_release_zoom
        
        self._user_limits = None
        self._updating_view = False
        self.axes.callbacks.connect('xlim_changed', self._on_view_changed)
        self.axes.callbacks.connect('ylim_changed', self._on_view_changed)

    def toggle_zoom(self):
        self.toolbar.zoom()

    def _on_view_changed(self, ax):
        if self._updating_view:
            return
        # If the toolbar is in zoom mode, it means the user is changing the view
        if self.toolbar.mode == 'zoom rect':
            self._user_limits = (ax.get_xlim(), ax.get_ylim())

    def reset_view(self):
        self._user_limits = None
        self.toolbar.home()
        self._user_limits = None

    def _on_click(self, event):
        if event.inaxes == self.axes and event.button == 1 and self.on_mq_clicked:
            # Check if toolbar is in a mode that should prevent peak selection
            if hasattr(self, 'toolbar') and self.toolbar.mode != '':
                return
            self.on_mq_clicked(event.xdata, event.ydata)

    def redraw(self, csd, identified, candidate=None, target=None, title=None):
        self._updating_view = True
        self.axes.clear()
        if title:
            self.axes.set_title(title, fontfamily="monospace", fontsize=10, loc="left")
        self.axes.set_xlabel("m/q")
        self.axes.set_ylabel(r"Beam Current ($\mu$A)")
        self.axes.xaxis.set_major_locator(MultipleLocator(1.0))
        self.axes.spines["top"].set_linewidth(0.1)
        self.axes.spines["right"].set_linewidth(0.1)

        if csd is None:
            self.axes.grid(color=COLOR_GRID, ls="--", alpha=0.5)
            self.draw()
            self._updating_view = False
            return

        if csd.m_over_q is not None:
            self.axes.plot(
                csd.m_over_q,
                csd.beam_current,
                ".:",
                color="black",
                alpha=0.4,
                label="CSD",
            )

        y_min, y_max = self.axes.get_ylim()
        y_range = max(y_max - y_min, 0.1)

        # Draw target/candidate markers
        if target and not candidate:
            self.axes.plot(
                target.m_over_q,
                target.current + 0.05 * y_range,
                "v",
                color=COLOR_TARGET,
                markersize=12,
                label="TARGET",
            )
            self.axes.axvline(
                target.m_over_q[0], color=COLOR_TARGET, ls="-", alpha=0.3, lw=1.5
            )

        if candidate:
            self.axes.plot(
                candidate.m_over_q,
                candidate.current + 0.05 * y_range,
                "v",
                color=COLOR_CANDIDATE,
                markersize=10,
                label=f"CAND: {candidate.symbol()}",
            )
            for q in range(1, candidate.z + 1):
                mq_exp = candidate.m / q
                self.axes.axvline(
                    mq_exp, ls="--", color=COLOR_CANDIDATE, alpha=0.4, lw=1
                )
                self.axes.text(
                    mq_exp,
                    y_max + 0.05 * y_range,
                    str(q),
                    color=COLOR_CANDIDATE,
                    ha="center",
                    fontsize=9,
                    fontweight="bold",
                )
            if len(candidate.missing_m_over_q) > 0:
                self.axes.plot(
                    candidate.missing_m_over_q,
                    candidate.missing_current,
                    "o",
                    mfc="none",
                    mec=COLOR_CANDIDATE,
                    alpha=0.6,
                )

        # Draw identified peaks
        peak_counts, style_cycle = (
            {},
            deque([(m, s) for s, m in product(SHADES, MARKERS)]),
        )
        for ev in identified:
            m, c = style_cycle[0]
            cur_off = [
                cur + peak_counts.setdefault(round(mq, 2), 0) * 0.02 * y_range
                for mq, cur in zip(ev.m_over_q, ev.current)
            ]
            for mq in ev.m_over_q:
                peak_counts[round(mq, 2)] += 1
            self.axes.plot(
                ev.m_over_q,
                cur_off,
                m,
                mfc=c,
                mec=COLOR_TEXT,
                label=ev.symbol(),
            )
            style_cycle.rotate(-1)

        self.axes.legend(loc="upper right", fontsize="small")
        self.axes.grid(color=COLOR_GRID, ls="--", alpha=0.5)

        # Apply saved limits if they exist
        if self._user_limits:
            self.axes.set_xlim(self._user_limits[0])
            self.axes.set_ylim(self._user_limits[1])
        else:
            # If not zoomed, apply the standard extra headroom for labels
            if candidate or target:
                self.axes.set_ylim(y_min, y_max + 0.15 * y_range)

        self.draw()
        self._updating_view = False
