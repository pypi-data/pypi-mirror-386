"""
MapView class for visualizing network topologies.

This module provides visualization methods for Topology objects.
"""

from typing import Any, Optional
from topolib.topology import Topology
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point
import pyproj
from topolib.elements.link import Link
from topolib.elements.node import Node
from matplotlib.widgets import Button as _ContButton


class MapView:
    def _add_zoom_buttons(self):
        """Add custom zoom buttons to the figure.

        Adds two small Matplotlib Button widgets to the figure to allow the
        user to zoom in and out. The buttons are placed in figure coordinates
        near the bottom-left corner.

        This method mutates ``self._fig`` by adding new axes and stores the
        created Button widgets on this instance.
        """
        # Zoom in button
        zoomin_ax = self._fig.add_axes([0.01, 0.01, 0.08, 0.06])
        self._zoomin_btn = Button(zoomin_ax, "+", color="lightgray", hovercolor="0.975")
        self._zoomin_btn.on_clicked(self._on_zoom_in)

        # Zoom out button
        zoomout_ax = self._fig.add_axes([0.10, 0.01, 0.08, 0.06])
        self._zoomout_btn = Button(
            zoomout_ax, "-", color="lightgray", hovercolor="0.975"
        )
        self._zoomout_btn.on_clicked(self._on_zoom_out)

    def _on_zoom_in(self, event):
        """Zoom in one step.

        This is a short wrapper that calls :meth:`_zoom` with a scale factor
        greater than 1 to zoom into the map center.

        :param event: Matplotlib click event (ignored).
        :type event: matplotlib.backend_bases.Event
        """
        self._zoom(1.2)

    def _on_zoom_out(self, event):
        """Zoom out one step.

        Wrapper for :meth:`_zoom` that uses a scale factor smaller than 1.

        :param event: Matplotlib click event (ignored).
        :type event: matplotlib.backend_bases.Event
        """
        self._zoom(1 / 1.2)

    def _zoom(self, scale):
        """Zoom the map by a scale factor while keeping the current center.

        The method computes new axis limits that are scaled around the
        current center of ``self._ax`` and triggers a redraw of the map
        content via :meth:`_redraw_map`.

        :param scale: Scale factor (>1 zooms in, <1 zooms out)
        :type scale: float
        """
        xlim = self._ax.get_xlim()
        ylim = self._ax.get_ylim()
        xmid = (xlim[0] + xlim[1]) / 2
        ymid = (ylim[0] + ylim[1]) / 2
        xsize = (xlim[1] - xlim[0]) / scale
        ysize = (ylim[1] - ylim[0]) / scale
        new_xlim = [xmid - xsize / 2, xmid + xsize / 2]
        new_ylim = [ymid - ysize / 2, ymid + ysize / 2]
        self._redraw_map(xlim=new_xlim, ylim=new_ylim)

    """
    Provides visualization methods for Topology objects.
    """

    def __init__(self, topology: Topology) -> None:
        """Create a MapView instance for a :class:`topolib.topology.Topology`.

        :param topology: Topology object to visualize and mutate.
        :type topology: topolib.topology.Topology
        """
        self.topology = topology
        # Interactive add node mode state
        self._add_node_mode = False
        self._add_node_button = None
        self._cid_click = None
        self._fig = None
        self._ax = None
        # Interactive add link mode state
        self._add_link_mode = False
        self._link_button = None
        self._cid_link_click = None
        self._link_start_node: Optional[object] = None
        # Node form state
        self._node_form_artists: list = []
        # Artists used to show a provisional node on the map before confirmation
        self._provisional_artists: list = []

    def show_map(self) -> None:
        """Render the interactive map window with nodes and links.

        This method prepares a Matplotlib figure and axes, renders all
        current nodes and links projected to Web Mercator (EPSG:3857), adds
        a contextily basemap, and installs the interactive widgets for
        adding nodes/links and zooming. The figure is displayed with
        :func:`matplotlib.pyplot.show`.

        :returns: None
        """
        lons: list[float] = [node.longitude for node in self.topology.nodes]
        lats: list[float] = [node.latitude for node in self.topology.nodes]
        names: list[str] = [node.name for node in self.topology.nodes]
        gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
            {"name": names},
            geometry=[Point(x, y) for x, y in zip(lons, lats)],
            crs="EPSG:4326",
        )
        gdf = gdf.to_crs(epsg=3857)

        # Map node id to projected coordinates
        node_id_to_xy = {
            node.id: (pt.x, pt.y) for node, pt in zip(self.topology.nodes, gdf.geometry)
        }

        # Try to get topology name (from attribute or fallback)
        topo_name = getattr(self.topology, "name", None)
        if topo_name is None:
            # Try to get from dict if loaded from JSON
            topo_name = getattr(self.topology, "_name", None)
        if topo_name is None:
            topo_name = "Topology"

        fig, ax = plt.subplots(figsize=(10, 7))
        self._fig = fig
        self._ax = ax
        # Continue flag used by the 'Continue' button to close the map and resume execution
        self._continue_pressed = False
        fig.suptitle(topo_name, fontsize=16)
        # Hide the default matplotlib toolbar for a cleaner UI
        try:
            fig.canvas.manager.toolbar.hide()
        except Exception:
            try:
                fig.canvas.toolbar_visible = False
            except Exception:
                pass
        # Draw links as simple lines
        for link in getattr(self.topology, "links", []):
            src_id = getattr(link, "source").id
            tgt_id = getattr(link, "target").id
            if src_id in node_id_to_xy and tgt_id in node_id_to_xy:
                x0, y0 = node_id_to_xy[src_id]
                x1, y1 = node_id_to_xy[tgt_id]
                ax.plot(
                    [x0, x1], [y0, y1], color="gray", linewidth=1, alpha=0.7, zorder=2
                )
        # Draw nodes
        gdf.plot(ax=ax, color="blue", markersize=40, zorder=5)
        for x, y, name in zip(gdf.geometry.x, gdf.geometry.y, gdf["name"]):
            ax.text(
                x,
                y,
                name,
                fontsize=8,
                ha="right",
                va="bottom",
                color="black",
                clip_on=True,
            )
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
        ax.set_axis_off()
        ax.set_title(f"Nodes and links ({topo_name})")
        # plt.tight_layout()  # Removed to avoid warning with widgets

        # Add interactive button for 'Add Node' mode
        self._add_interactive_add_node_button()
        # Add zoom in/out buttons
        self._add_zoom_buttons()
        # Add interactive button for 'Add Link' mode
        self._add_interactive_add_link_button()
        # Add continue button to close the map and continue execution
        self._add_continue_button()
        plt.show()

    def _add_interactive_add_node_button(self):
        """Create and attach the "Add Node" Button widget.

        When clicked the button enables a one-shot mode where the next
        click on the map will place a provisional marker and open the
        node-edit dialog.
        """
        # Place button in a new axes
        button_ax = self._fig.add_axes([0.81, 0.01, 0.15, 0.06])
        self._add_node_button = Button(
            button_ax, "Add Node", color="lightgray", hovercolor="0.975"
        )
        self._add_node_button.on_clicked(self._on_add_node_button_clicked)

    def _add_interactive_add_link_button(self):
        """Create and attach the "Add Link" Button widget.

        When enabled the map will accept two node selections and will
        create a bidirectional link (two Link objects) between them.
        """
        # Place button in a new axes (left of Add Node button)
        link_ax = self._fig.add_axes([0.63, 0.01, 0.15, 0.06])
        self._link_button = Button(
            link_ax, "Add Link", color="lightgray", hovercolor="0.975"
        )
        self._link_button.on_clicked(self._on_add_link_button_clicked)

    def _add_continue_button(self):
        """Add a 'Continue' button.

        The button closes the map window and allows the calling code to
        continue executing (``show_map`` returns after the figure
        window is closed via this button).
        """
        cont_ax = self._fig.add_axes([0.81, 0.08, 0.15, 0.06])

        self._cont_button = _ContButton(
            cont_ax, "Continue", color="lightgray", hovercolor="0.975"
        )
        self._cont_button.on_clicked(self._on_continue_clicked)

    def _on_continue_clicked(self, event):
        """Handle clicks on the Continue button.

        Sets an internal flag and attempts to close the Matplotlib figure.

        :param event: Matplotlib click event (ignored)
        :type event: matplotlib.backend_bases.Event
        """
        self._continue_pressed = True
        try:
            plt.close(self._fig)
        except Exception:
            pass

    def _on_add_link_button_clicked(self, event):
        """Toggle the persistent "Add Link" mode.

        When the mode is active the map will listen to clicks and allow the
        user to select two nodes to create a link. The button's appearance
        is changed to provide feedback about the active state.

        :param event: Matplotlib click event (ignored)
        :type event: matplotlib.backend_bases.Event
        """
        self._add_link_mode = not self._add_link_mode
        if self._add_link_mode:
            # connect click handler
            if self._cid_link_click is None:
                self._cid_link_click = self._fig.canvas.mpl_connect(
                    "button_press_event", self._on_map_click_add_link
                )
            # visually mark button pressed by changing color
            try:
                self._link_button.color = "lightblue"
            except Exception:
                pass
            self._link_start_node = None
        else:
            # disconnect handler
            if self._cid_link_click is not None:
                self._fig.canvas.mpl_disconnect(self._cid_link_click)
                self._cid_link_click = None
            try:
                self._link_button.color = "lightgray"
            except Exception:
                pass
            self._link_start_node = None

    def _on_map_click_add_link(self, event):
        """Handle map clicks while in "Add Link" mode.

        The handler finds the nearest node to the click (within a tolerance)
        and treats the first selection as a "start" node and the second
        one as the "end" node. When both nodes are selected two Link
        instances are created (forward and reverse) and added to the
        topology. Link length is computed using geodesic distance (WGS84)
        and stored in kilometers.

        :param event: Matplotlib mouse event containing ``xdata``/``ydata``
        :type event: matplotlib.backend_bases.MouseEvent
        """
        if not self._add_link_mode or event.inaxes != self._ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        # We have projected coordinates in xdata,ydata (EPSG:3857)
        click_x, click_y = event.xdata, event.ydata

        # Build projected GeoDataFrame of nodes to find nearest
        lons = [node.longitude for node in self.topology.nodes]
        lats = [node.latitude for node in self.topology.nodes]
        gdf_nodes = gpd.GeoDataFrame(
            {"id": [n.id for n in self.topology.nodes]},
            geometry=[Point(x, y) for x, y in zip(lons, lats)],
            crs="EPSG:4326",
        ).to_crs(epsg=3857)

        # Find the nearest node within a tolerance (in meters/pixels depending on map scale).
        # We'll use a simple distance-based tolerance (e.g., 10000 meters) but adjust if necessary.
        tol = 100000  # meters in projected coordinates; conservative default
        nearest = None
        min_dist = float("inf")
        for idx, geom in enumerate(gdf_nodes.geometry):
            dx = geom.x - click_x
            dy = geom.y - click_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < min_dist and dist <= tol:
                min_dist = dist
                nearest = self.topology.nodes[idx]

        if nearest is None:
            # nothing clicked near a node
            return

        # If start node not selected yet, set it and highlight
        if self._link_start_node is None:
            self._link_start_node = nearest
            # optionally highlight by drawing a red marker
            self._ax.plot(
                [gdf_nodes.geometry[self.topology.nodes.index(nearest)].x],
                [gdf_nodes.geometry[self.topology.nodes.index(nearest)].y],
                marker="o",
                color="red",
                markersize=12,
                zorder=10,
            )
            self._fig.canvas.draw_idle()
            return

        # If start selected and clicked on a different node, create link
        if nearest.id != self._link_start_node.id:
            # determine new link ids (reserve two consecutive ids)
            max_id = max([l.id for l in self.topology.links], default=0)
            id1 = max_id + 1
            id2 = max_id + 2

            # compute geodesic distance between the two nodes (meters)
            lon1 = self._link_start_node.longitude
            lat1 = self._link_start_node.latitude
            lon2 = nearest.longitude
            lat2 = nearest.latitude
            geod = pyproj.Geod(ellps="WGS84")
            _, _, distance = geod.inv(lon1, lat1, lon2, lat2)
            distance_km = distance / 1000.0

            # create forward and reverse links with same length (in km)
            new_link = Link(id1, self._link_start_node, nearest, distance_km)
            new_link_rev = Link(id2, nearest, self._link_start_node, distance_km)
            self.topology.add_link(new_link)
            self.topology.add_link(new_link_rev)
            # redraw map to show new links
            self._redraw_map()

        # Reset start node selection but keep add-link mode active until toggled
        self._link_start_node = None

    def _on_add_node_button_clicked(self, event):
        """Enable "Add Node" mode and wait for a map click.

        After this method runs, the next valid click inside the map axes
        will place a provisional marker and open the node editor dialog.

        :param event: Matplotlib click event (ignored)
        :type event: matplotlib.backend_bases.Event
        """
        self._add_node_mode = True
        # Connect click event if not already connected
        if self._cid_click is None:
            self._cid_click = self._fig.canvas.mpl_connect(
                "button_press_event", self._on_map_click_add_node
            )
        # Now waiting for a click on the map to place the provisional marker and open the dialog

    def _on_map_click_add_node(self, event):
        """Handle a map click when in "Add Node" mode.

        Places a provisional marker and label at the clicked position (in
        Web Mercator coordinates), computes the corresponding longitude
        and latitude and opens a modal dialog to edit the new node
        attributes. The provisional marker is removed when the dialog is
        closed (confirmed or cancelled).

        :param event: Matplotlib mouse event (must have ``xdata`` and ``ydata``)
        :type event: matplotlib.backend_bases.MouseEvent
        """
        if not self._add_node_mode or event.inaxes != self._ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        # Convert from Web Mercator (EPSG:3857) to lon/lat (EPSG:4326)
        proj_3857 = pyproj.CRS("EPSG:3857")
        proj_4326 = pyproj.CRS("EPSG:4326")
        transformer = pyproj.Transformer.from_crs(proj_3857, proj_4326, always_xy=True)
        lon, lat = transformer.transform(event.xdata, event.ydata)

        # Prepare default id and name
        next_id = max([n.id for n in self.topology.nodes], default=0) + 1
        default_name = f"new node {next_id}"

        # Draw a provisional node marker and label on the map so the user sees it immediately
        try:
            marker_line = self._ax.plot(
                [event.xdata],
                [event.ydata],
                marker="o",
                color="green",
                markersize=10,
                zorder=20,
            )[0]
            txt = self._ax.text(
                event.xdata,
                event.ydata,
                default_name,
                fontsize=8,
                ha="right",
                va="bottom",
                color="green",
                zorder=21,
            )
            self._provisional_artists = [marker_line, txt]
            try:
                self._fig.canvas.draw()
            except Exception:
                try:
                    self._fig.canvas.draw_idle()
                except Exception:
                    pass
            # Give the GUI event loop a small chance to render the canvas so the provisional
            # marker becomes visible before opening the modal tkinter dialog.
            try:
                plt.pause(0.05)
            except Exception:
                try:
                    plt.pause(0.01)
                except Exception:
                    pass
        except Exception:
            self._provisional_artists = []

        # Show interactive form to enter node details (prefill id, name, lon/lat)
        self._show_node_form(
            event.xdata,
            event.ydata,
            lon,
            lat,
            prefill_id=next_id,
            prefill_name=default_name,
        )

        # After showing form, disable add-node mode (user must re-click button to add more)
        self._add_node_mode = False
        if self._cid_click is not None:
            self._fig.canvas.mpl_disconnect(self._cid_click)
            self._cid_click = None

    def _close_node_form(self):
        """Remove any Matplotlib widgets/axes used by the node form.

        This method attempts to remove stored widget axes from the
        figure (if any) and requests a canvas redraw.
        """
        for a in self._node_form_artists:
            try:
                a.remove()
            except Exception:
                pass
        self._node_form_artists = []
        try:
            self._fig.canvas.draw_idle()
        except Exception:
            pass

    def _show_node_form(
        self,
        x_proj,
        y_proj,
        lon_prefill,
        lat_prefill,
        prefill_id: Optional[int] = None,
        prefill_name: Optional[str] = None,
    ):
        """Open a native tkinter modal dialog to edit node attributes.

        This dialog is modal and will block until the user confirms or
        cancels. The dialog is pre-filled with the provided longitude and
        latitude and a suggested id and name. If the dialog is confirmed
        a new :class:`topolib.elements.node.Node` is created and added to
        the topology; otherwise the provisional marker is removed.

        Note: tkinter must be available in the Python environment. On
        many Linux distributions the package providing tkinter is called
        ``python3-tk``.

        :param x_proj: Click X coordinate in Web Mercator (EPSG:3857).
        :param y_proj: Click Y coordinate in Web Mercator (EPSG:3857).
        :param lon_prefill: Suggested longitude (EPSG:4326).
        :param lat_prefill: Suggested latitude (EPSG:4326).
        :param prefill_id: Suggested node id, if any.
        :param prefill_name: Suggested node name, if any.
        :returns: None
        """
        # Use a native tkinter modal dialog for reliable popup behavior across backends.
        try:
            import tkinter as tk

            # Prepare defaults
            if prefill_id is None:
                prefill_id = max([n.id for n in self.topology.nodes], default=0) + 1
            if prefill_name is None:
                prefill_name = f"new node {prefill_id}"

            root = tk.Tk()
            root.withdraw()  # hide main root

            dialog = tk.Toplevel(root)
            dialog.title("Add node")
            dialog.resizable(False, False)
            dialog.grab_set()  # modal

            # Labels and entries
            tk.Label(dialog, text="ID").grid(
                row=0, column=0, sticky="e", padx=6, pady=4
            )
            en_id = tk.Entry(dialog)
            en_id.insert(0, str(prefill_id))
            en_id.grid(row=0, column=1, padx=6, pady=4)

            tk.Label(dialog, text="Name").grid(
                row=1, column=0, sticky="e", padx=6, pady=4
            )
            en_name = tk.Entry(dialog)
            en_name.insert(0, prefill_name)
            en_name.grid(row=1, column=1, padx=6, pady=4)

            tk.Label(dialog, text="Latitude").grid(
                row=2, column=0, sticky="e", padx=6, pady=4
            )
            en_lat = tk.Entry(dialog)
            en_lat.insert(0, str(lat_prefill))
            en_lat.grid(row=2, column=1, padx=6, pady=4)

            tk.Label(dialog, text="Longitude").grid(
                row=3, column=0, sticky="e", padx=6, pady=4
            )
            en_lon = tk.Entry(dialog)
            en_lon.insert(0, str(lon_prefill))
            en_lon.grid(row=3, column=1, padx=6, pady=4)

            # Additional node attributes (initialize to zero)
            tk.Label(dialog, text="Weight").grid(
                row=4, column=0, sticky="e", padx=6, pady=4
            )
            en_weight = tk.Entry(dialog)
            en_weight.insert(0, "0")
            en_weight.grid(row=4, column=1, padx=6, pady=4)

            tk.Label(dialog, text="Pop").grid(
                row=5, column=0, sticky="e", padx=6, pady=4
            )
            en_pop = tk.Entry(dialog)
            en_pop.insert(0, "0")
            en_pop.grid(row=5, column=1, padx=6, pady=4)

            tk.Label(dialog, text="DC").grid(
                row=6, column=0, sticky="e", padx=6, pady=4
            )
            en_dc = tk.Entry(dialog)
            en_dc.insert(0, "0")
            en_dc.grid(row=6, column=1, padx=6, pady=4)

            tk.Label(dialog, text="IXP").grid(
                row=7, column=0, sticky="e", padx=6, pady=4
            )
            en_ixp = tk.Entry(dialog)
            en_ixp.insert(0, "0")
            en_ixp.grid(row=7, column=1, padx=6, pady=4)

            result = {"ok": False}

            def on_confirm():
                try:
                    nid = int(en_id.get().strip())
                    name = en_name.get().strip() or f"new node {nid}"
                    lat = float(en_lat.get().strip())
                    lon = float(en_lon.get().strip())
                except Exception:
                    # invalid input: ignore (or add dialog message)
                    return
                # parse additional attributes, default to 0 on parse error
                try:
                    weight = float(en_weight.get().strip())
                except Exception:
                    weight = 0
                try:
                    pop = int(en_pop.get().strip())
                except Exception:
                    pop = 0
                try:
                    dc = int(en_dc.get().strip())
                except Exception:
                    dc = 0
                try:
                    ixp = int(en_ixp.get().strip())
                except Exception:
                    ixp = 0

                # Check id uniqueness
                if any(n.id == nid for n in self.topology.nodes):
                    return
                # Create and add node with additional attributes
                new_node = Node(nid, name, lat, lon, weight, pop, dc, ixp)
                self.topology.add_node(new_node)
                result.update({"ok": True})
                dialog.destroy()

            def on_cancel():
                dialog.destroy()

            btn_frame = tk.Frame(dialog)
            btn_frame.grid(row=8, column=0, columnspan=2, pady=(4, 8))
            tk.Button(btn_frame, text="Confirm", command=on_confirm, bg="#9fdf9f").pack(
                side="left", padx=6
            )
            tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(
                side="right", padx=6
            )

            # Center the dialog relative to the main figure window if possible
            try:
                mgr = getattr(self._fig.canvas, "manager", None)
                if mgr is not None:
                    win = getattr(mgr, "window", None)
                    if win is not None and hasattr(win, "winfo_rootx"):
                        # For TkAgg integration, position near the plot window
                        try:
                            x = win.winfo_rootx() + 50
                            y = win.winfo_rooty() + 50
                            dialog.geometry(f"+{x}+{y}")
                            # make dialog transient/child of the plot window and lift it
                            try:
                                dialog.transient(win)
                                dialog.lift()
                                dialog.attributes("-topmost", True)
                                dialog.attributes("-topmost", False)
                            except Exception:
                                try:
                                    dialog.lift()
                                except Exception:
                                    pass
                        except Exception:
                            pass
            except Exception:
                pass

            root.wait_window(dialog)
            try:
                root.destroy()
            except Exception:
                pass

            # If the dialog confirmed and node added, redraw map
            if result.get("ok"):
                try:
                    # clear provisional artists (they will be redrawn from topology)
                    for a in self._provisional_artists:
                        try:
                            a.remove()
                        except Exception:
                            pass
                    self._provisional_artists = []
                except Exception:
                    pass
                try:
                    self._redraw_map()
                except Exception:
                    pass
            else:
                # user cancelled: remove provisional marker and redraw to erase it
                try:
                    for a in self._provisional_artists:
                        try:
                            a.remove()
                        except Exception:
                            pass
                    self._provisional_artists = []
                except Exception:
                    pass
                try:
                    self._fig.canvas.draw()
                except Exception:
                    try:
                        self._fig.canvas.draw_idle()
                    except Exception:
                        pass
            return
        except Exception:
            # Fallback: do nothing if tkinter not available
            return

    def _redraw_map(self, xlim=None, ylim=None):
        """Redraw the map content (nodes and links) on the existing axes.

        The axes are cleared and nodes/links are re-plotted from the
        current topology. Optionally, axis limits can be supplied so the
        view is preserved after redraw.

        :param xlim: Optional 2-tuple with x-axis limits in projected units.
        :type xlim: Optional[tuple(float, float)]
        :param ylim: Optional 2-tuple with y-axis limits in projected units.
        :type ylim: Optional[tuple(float, float)]
        :returns: None
        """
        # geopandas, shapely Point and contextily already imported at module level

        # Clear axes
        self._ax.clear()
        if xlim is not None:
            self._ax.set_xlim(xlim)
        if ylim is not None:
            self._ax.set_ylim(ylim)
        lons = [node.longitude for node in self.topology.nodes]
        lats = [node.latitude for node in self.topology.nodes]
        names = [node.name for node in self.topology.nodes]
        gdf = gpd.GeoDataFrame(
            {"name": names},
            geometry=[Point(x, y) for x, y in zip(lons, lats)],
            crs="EPSG:4326",
        )
        gdf = gdf.to_crs(epsg=3857)
        node_id_to_xy = {
            node.id: (pt.x, pt.y) for node, pt in zip(self.topology.nodes, gdf.geometry)
        }
        topo_name = getattr(self.topology, "name", None)
        if topo_name is None:
            topo_name = getattr(self.topology, "_name", None)
        if topo_name is None:
            topo_name = "Topology"
        # Draw links
        for link in getattr(self.topology, "links", []):
            src_id = getattr(link, "source").id
            tgt_id = getattr(link, "target").id
            if src_id in node_id_to_xy and tgt_id in node_id_to_xy:
                x0, y0 = node_id_to_xy[src_id]
                x1, y1 = node_id_to_xy[tgt_id]
                self._ax.plot(
                    [x0, x1], [y0, y1], color="gray", linewidth=1, alpha=0.7, zorder=2
                )
        # Draw nodes
        gdf.plot(ax=self._ax, color="blue", markersize=40, zorder=5)
        for x, y, name in zip(gdf.geometry.x, gdf.geometry.y, gdf["name"]):
            self._ax.text(
                x,
                y,
                name,
                fontsize=8,
                ha="right",
                va="bottom",
                color="black",
                clip_on=True,
            )
        ctx.add_basemap(self._ax, source=ctx.providers.OpenStreetMap.Mapnik)
        self._ax.set_axis_off()
        self._ax.set_title(f"Nodes and links ({topo_name})")
        self._fig.suptitle(topo_name, fontsize=16)
        # self._fig.tight_layout()  # Removed to avoid warning with widgets
        self._fig.canvas.draw_idle()

    def export_map_png(self, filename: str, dpi: int = 150) -> None:
        """
        Export the topology map as a PNG image using Matplotlib and Contextily.

        :param filename: Output PNG file path.
        :type filename: str
        :param dpi: Dots per inch for the saved image (default: 150).
        :type dpi: int
        """
        lons: list[float] = [node.longitude for node in self.topology.nodes]
        lats: list[float] = [node.latitude for node in self.topology.nodes]
        names: list[str] = [node.name for node in self.topology.nodes]
        gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
            {"name": names},
            geometry=[Point(x, y) for x, y in zip(lons, lats)],
            crs="EPSG:4326",
        )
        gdf = gdf.to_crs(epsg=3857)

        node_id_to_xy = {
            node.id: (pt.x, pt.y) for node, pt in zip(self.topology.nodes, gdf.geometry)
        }

        topo_name = getattr(self.topology, "name", None)
        if topo_name is None:
            topo_name = getattr(self.topology, "_name", None)
        if topo_name is None:
            topo_name = "Topology"

        fig, ax = plt.subplots(figsize=(10, 7))
        fig.suptitle(topo_name, fontsize=16)
        for link in getattr(self.topology, "links", []):
            src_id = getattr(link, "source").id
            tgt_id = getattr(link, "target").id
            if src_id in node_id_to_xy and tgt_id in node_id_to_xy:
                x0, y0 = node_id_to_xy[src_id]
                x1, y1 = node_id_to_xy[tgt_id]
                ax.plot(
                    [x0, x1], [y0, y1], color="gray", linewidth=1, alpha=0.7, zorder=2
                )
        gdf.plot(ax=ax, color="blue", markersize=40, zorder=5)
        for x, y, name in zip(gdf.geometry.x, gdf.geometry.y, gdf["name"]):
            ax.text(x, y, name, fontsize=8, ha="right", va="bottom", color="black")
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
        ax.set_axis_off()
        ax.set_title(f"Nodes and links ({topo_name})")
        plt.tight_layout()
        plt.savefig(filename, dpi=dpi)
        plt.close(fig)
