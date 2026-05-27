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
    COLOR_ACTION,
    FONT_SANS
)


class MqPlotCanvas(FigureCanvas):
    zoom_finished = Signal()

    def __init__(self, parent=None):
        fig = Figure(figsize=(9, 6), facecolor=COLOR_BG)
        fig.subplots_adjust(top=0.92, bottom=0.12) # Closer fit to top labels
        self.axes = fig.add_subplot(111, facecolor=COLOR_PLOT_BG)
        self.axes.set_xlabel("m/q")
        self.axes.set_ylabel(r"Beam Current ($\mu$A)")
        self.axes.xaxis.set_major_locator(MultipleLocator(1.0))
        self.axes.spines["top"].set_linewidth(0.1)
        self.axes.spines["right"].set_linewidth(0.1)
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
        
        # Connect signals for view changes
        self.axes.callbacks.connect('xlim_changed', self._on_view_changed)
        self.axes.callbacks.connect('ylim_changed', self._on_view_changed)
        self.mpl_connect("scroll_event", self._on_scroll)

    def toggle_zoom(self):
        self.toolbar.zoom()

    def toggle_pan(self):
        self.toolbar.pan()

    def _on_scroll(self, event):
        """Handle mouse wheel scrolling for zooming."""
        if event.inaxes != self.axes or (hasattr(self, 'toolbar') and self.toolbar.mode != ''):
            return
            
        self._updating_view = True
        try:
            # Get current limits
            cur_xlim = self.axes.get_xlim()
            cur_ylim = self.axes.get_ylim()
            
            xdata = event.xdata
            ydata = event.ydata
            
            # Zoom factor
            base_scale = 1.3
            if event.button == 'up':
                scale_factor = 1 / base_scale
            elif event.button == 'down':
                scale_factor = base_scale
            else:
                return
                
            # Compute new width and height
            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
            
            # Keep the point under the mouse stationary
            rel_x = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
            rel_y = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
            
            self.axes.set_xlim([xdata - new_width * (1 - rel_x), xdata + new_width * rel_x])
            self.axes.set_ylim([ydata - new_height * (1 - rel_y), ydata + new_height * rel_y])
            
            # Update user limits and sync toolbar
            self._user_limits = (self.axes.get_xlim(), self.axes.get_ylim())
            if hasattr(self.toolbar, "push_current"):
                self.toolbar.push_current()
            self.draw_idle()
        finally:
            self._updating_view = False

    def _on_view_changed(self, ax):
        if self._updating_view:
            return
        # Save any view change as the user's intended view
        self._user_limits = (ax.get_xlim(), ax.get_ylim())

    def reset_view(self):
        self._user_limits = None
        self._updating_view = True
        try:
            # Clear toolbar history to ensure 'home' is a fresh start
            # Handle different Matplotlib versions (older _views/_positions vs newer _nav_stack)
            if hasattr(self.toolbar, "_nav_stack"):
                self.toolbar._nav_stack.clear()
            else:
                if hasattr(self.toolbar, "_views"):
                    self.toolbar._views.clear()
                if hasattr(self.toolbar, "_positions"):
                    self.toolbar._positions.clear()
            
            # home() might fail if stack is empty, so we just clear and we'll push_current in redraw
            # but usually home() is what we want for 'reset'
            try:
                self.toolbar.home()
            except Exception:
                pass 
        finally:
            self._updating_view = False
            self._user_limits = None

    def _on_click(self, event):
        if event.inaxes == self.axes and event.button == 1 and self.on_mq_clicked:
            # Check if toolbar is in a mode that should prevent peak selection
            if hasattr(self, 'toolbar') and self.toolbar.mode != '':
                return
            self.on_mq_clicked(event.xdata, event.ydata)

    def redraw(self, csd, identified, candidate=None, target=None, title=None):
        self._updating_view = True
        try:
            # Remove artists instead of clearing axes to preserve callbacks and configuration
            # This is critical for keeping our xlim_changed/ylim_changed connections alive
            for artist in (list(self.axes.lines) + list(self.axes.collections) + 
                           list(self.axes.texts) + list(self.axes.patches)):
                artist.remove()
            if self.axes.get_legend() is not None:
                self.axes.get_legend().remove()
                
            # Temporarily enable autoscale so the new data can define the base bounds
            self.axes.set_autoscalex_on(True)
            self.axes.set_autoscaley_on(True)
            
            if csd is None:
                self.axes.grid(color=COLOR_GRID, ls="--", alpha=0.5)
                self.draw_idle()
                return

            # Plot main CSD data
            if csd.m_over_q is not None:
                self.axes.plot(
                    csd.m_over_q,
                    csd.beam_current,
                    "-",
                    color="black",
                    alpha=0.4,
                    label="CSD",
                )

            # Recompute data limits from newly plotted data
            self.axes.relim()
            self.axes.autoscale_view()
            
            # Calculate standard headroom for markers using the autoscaled limits
            y_min, y_max = self.axes.get_ylim()
            y_range = max(y_max - y_min, 0.1)

            # Determine the visible x-range for clipping the q-state ruler
            if self._user_limits:
                vis_x_min, vis_x_max = self._user_limits[0]
            else:
                vis_x_min, vis_x_max = self.axes.get_xlim()

            # Draw target/candidate markers
            if candidate:
                self.axes.plot(
                    candidate.m_over_q,
                    candidate.current + 0.05 * y_range,
                    "v",
                    color=COLOR_CANDIDATE,
                    markersize=10,
                    label=f"CAND: {candidate.symbol()}",
                )
                
                # Indicator for what the numbers represent
                self.axes.text(
                    0.0, 1.05, "CHARGE STATES (q):",
                    transform=self.axes.transAxes,
                    color="#666666",
                    fontsize=8,
                    fontweight="bold",
                    fontfamily="sans-serif",
                    va="bottom",
                    ha="left"
                )

                for q in range(1, candidate.z + 1):
                    mq_exp = candidate.m / q
                    if mq_exp < vis_x_min or mq_exp > vis_x_max:
                        continue
                    self.axes.axvline(
                        mq_exp, ls="--", color=COLOR_CANDIDATE, alpha=0.4, lw=1
                    )
                    # "Ruler" style labels: anchored ABOVE the axes, rotated for density
                    self.axes.text(
                        mq_exp,
                        1.02, # Positioned above the axes boundary (1.0)
                        str(q),
                        color=COLOR_TEXT,
                        ha="center",
                        va="bottom",
                        fontsize=9,
                        fontweight="bold",
                        fontfamily="monospace",
                        transform=self.axes.get_xaxis_transform(), # X is data, Y is 0.0-1.0 (axes)
                        rotation=90
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

            if target:
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

            # Draw identified peaks with style cycling
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

            # FINAL STEP: Apply view limits
            # If the user has a custom zoom, enforce it.
            # Otherwise, use standard autoscale with headroom.
            if self._user_limits:
                self.axes.set_xlim(self._user_limits[0])
                self.axes.set_ylim(self._user_limits[1])
                self.axes.set_autoscalex_on(False)
                self.axes.set_autoscaley_on(False)
            else:
                self.axes.autoscale_view()
                if candidate or target:
                    self.axes.set_ylim(y_min, y_max + 0.15 * y_range)

            # Synchronize the toolbar's internal view stack
            if hasattr(self.toolbar, "push_current"):
                self.toolbar.push_current()
            self.draw_idle()

        finally:
            self._updating_view = False
