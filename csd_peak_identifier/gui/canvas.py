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
        # Tight margins to maximize plot area, leaving room for the secondary q-ruler at top
        fig.subplots_adjust(top=0.88, bottom=0.08, left=0.06, right=0.98) 
        self.axes = fig.add_subplot(111, facecolor=COLOR_PLOT_BG)
        self.axes.set_xlabel("m/q")
        self.axes.set_ylabel(r"Beam Current ($\mu$A)")
        self.axes.xaxis.set_major_locator(MultipleLocator(1.0))
        self.axes.spines["top"].set_linewidth(0.1)
        self.axes.spines["right"].set_linewidth(0.1)
        super().__init__(fig)
        self.setParent(parent)
        self.on_mq_clicked = None
        
        self._secax = None
        self.mpl_connect("button_press_event", self._on_button_press)
        self.mpl_connect("button_release_event", self._on_button_release)
        self.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.mpl_connect("scroll_event", self._on_scroll)
        
        # Panning state
        self._right_click_panning = False
        self._last_mouse_pos = None

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

    def _on_button_press(self, event):
        if event.inaxes != self.axes:
            return
            
        if event.button == 1: # Left click - Peak selection
            # Check if toolbar is in a mode that should prevent peak selection
            if hasattr(self, 'toolbar') and self.toolbar.mode != '':
                return
            if self.on_mq_clicked:
                self.on_mq_clicked(event.xdata, event.ydata)
        elif event.button == 3: # Right click - Start Panning
            # Only pan if we aren't in a special toolbar mode (zoom/built-in pan)
            if hasattr(self, 'toolbar') and self.toolbar.mode == '':
                self._right_click_panning = True
                self._last_mouse_pos = (event.x, event.y)

    def _on_button_release(self, event):
        if event.button == 3:
            self._right_click_panning = False
            self._last_mouse_pos = None

    def _on_mouse_move(self, event):
        if self._right_click_panning and event.x is not None and event.y is not None:
            dx = event.x - self._last_mouse_pos[0]
            dy = event.y - self._last_mouse_pos[1]
            self._last_mouse_pos = (event.x, event.y)
            
            self._updating_view = True
            try:
                # Use axes coordinate transforms to convert pixel delta to data delta
                inv = self.axes.transData.inverted()
                p0 = inv.transform((0, 0))
                p1 = inv.transform((dx, dy))
                dat_dx = p1[0] - p0[0]
                dat_dy = p1[1] - p0[1]
                
                xlim = self.axes.get_xlim()
                ylim = self.axes.get_ylim()
                self.axes.set_xlim(xlim[0] - dat_dx, xlim[1] - dat_dx)
                self.axes.set_ylim(ylim[0] - dat_dy, ylim[1] - dat_dy)
                
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

    def redraw(self, csd, identified, candidate=None, target=None, title=None, use_log_y=False):
        self._updating_view = True
        try:
            # Set scale
            if use_log_y:
                self.axes.set_yscale('log', nonpositive='clip')
            else:
                self.axes.set_yscale('linear')

            # Remove artists instead of clearing axes to preserve callbacks and configuration
            # This is critical for keeping our xlim_changed/ylim_changed connections alive
            for artist in (list(self.axes.lines) + list(self.axes.collections) + 
                           list(self.axes.texts) + list(self.axes.patches)):
                artist.remove()
            if self.axes.get_legend() is not None:
                self.axes.get_legend().remove()
            
            # Remove previous secondary axis if it exists
            if self._secax:
                try:
                    self._secax.remove()
                except Exception:
                    pass
                self._secax = None
                
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
                    markersize=10, # Increased from default
                    label=ev.symbol(),
                )
                style_cycle.rotate(-1)

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

            # NOW plot the q-state ruler as a secondary axis
            if candidate:
                from matplotlib.patches import Rectangle
                # Add a white background rectangle for the "ruler" area
                # Height reduced to 0.07 for a sleeker profile
                ruler_bg = Rectangle(
                    (0, 1.0), 1, 0.07, 
                    transform=self.axes.transAxes,
                    facecolor="white", 
                    edgecolor=COLOR_GRID, 
                    linewidth=0.5,
                    clip_on=False,
                    zorder=10
                )
                self.axes.add_patch(ruler_bg)

                # Create a secondary x-axis pinned to the top
                self._secax = self.axes.secondary_xaxis('top', functions=(lambda x: x, lambda x: x))
                
                q_mq_values = []
                q_labels = []
                for q in range(1, candidate.z + 1):
                    mq_exp = candidate.m / q
                    q_mq_values.append(mq_exp)
                    q_labels.append(str(q))
                    
                    # Also keep the vertical guide lines
                    vis_x_min, vis_x_max = self.axes.get_xlim()
                    if mq_exp >= vis_x_min and mq_exp <= vis_x_max:
                        self.axes.axvline(
                            mq_exp, ls="--", color=COLOR_CANDIDATE, alpha=0.3, lw=0.8
                        )

                self._secax.set_xticks(q_mq_values)
                self._secax.set_xticklabels(q_labels, rotation=90, fontsize=8, fontweight='bold', fontfamily='monospace')
                self._secax.set_xlabel("q", fontsize=8, fontweight='bold', color='#666666', labelpad=2)
                
                # Style the secondary axis to look like a clean ruler
                self._secax.spines['top'].set_visible(False) 
                self._secax.tick_params(axis='x', colors=COLOR_TEXT, direction='in', length=3, zorder=11)
                self._secax.zorder = 11

            self.axes.legend(loc="upper right", fontsize="small")
            self.axes.grid(color=COLOR_GRID, ls="--", alpha=0.5)

            # Synchronize the toolbar's internal view stack
            if hasattr(self.toolbar, "push_current"):
                self.toolbar.push_current()
            self.draw_idle()

        finally:
            self._updating_view = False
