"""
hurdat2parser 2.3.0.1, Copyright (c) 2024, Kyle S. Gentry

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import operator
import json
import statistics
import math
import os
import re
import csv
import itertools
import collections
import sys
import copy

import shapefile

import geojson

from . import _calculations
from . import _gis
from . import _maps

import matplotlib
import matplotlib.style as mplstyle
import matplotlib.pyplot as plt
import matplotlib.ticker as _ticker
import matplotlib.dates as _dates
import matplotlib.figure as _figure
import matplotlib.patches as _patches

CSV_VARS = [
    ('TC Qty', 'tracks'),
    # ('Trk Dist', 'track_distance'),
    ('Landfalls (Acc.)', 'landfalls'),
    ('TC Trk Dist', 'track_distance_TC'),
    ('TC Landfall', 'landfall_TC'),
    ('TS', 'TSreach'),
    ('TS Landfall', 'landfall_TS'),
    ('ACE', 'ACE'),
    ('TS Trk Dist', 'track_distance_TS'),
    ('TS-Excl', 'TSonly'),
    ('HU', 'HUreach'),
    ('HU Landfall', 'landfall_HU'),
    ('HDP', 'HDP'),
    ('HU Trk Dist', 'track_distance_HU'),
    ('HU-1and2', 'HUonly'),
    ('MHU', 'MHUreach'),
    ('MHU Landfall', 'landfall_MHU'),
    ('MHDP', 'MHDP'),
    ('MHU Trk Dist', 'track_distance_MHU'),
    ('Cat 4 and 5 Qty', 'cat45reach'),
    ('Cat 5 Qty', 'cat5reach'),
]

CSV_CLIMO_VARS = [('Climatology', "era")] + CSV_VARS

CSV_SEASON_VARS = [
    ('Year', 'year'),
    ('Duration (days)', 'duration'),
    ('Start Ordinal', 'start_ordinal'),
    ('End Ordinal', 'end_ordinal'),
] + CSV_VARS

CSV_TC_VARS = [
    ('Year', 'year'),
    ('ATCF Num', 'atcf_num'),
    ('ATCF Id', 'atcfid'),
    ('Name', 'name'),
    ('Duration (days) as TC', 'duration_TC'),
    ('Start Ordinal', 'start_ordinal'),
    ('End Ordinal', 'end_ordinal'),
    ('Min MSLP', 'minmslp'),
    ('Max Wind', 'maxwind'),
    ('Highest Status Reached', 'status_highest'),
] + [
    VAR for VAR in CSV_VARS[1:]
    if "only" not in VAR[-1]
    and "reach" not in VAR[-1]
]

Era = collections.namedtuple(
    "Era",
    [attr for desc, attr in CSV_CLIMO_VARS]
)

class ClimateEra(object):
    """Used to house information from the <Hurdat2>.multi_season_info method."""
    def __init__(self, **kw):
        self.__dict__.update(**kw)

# class Ellipsoid:    # Uncomment for lambda release
class Ellipsoid(_patches.Ellipse):
    """
    An extended matplotlib.patches.Ellipse class.

    This is used to form wind-extent ellipses in the <TropicalCyclone>.track_map
    method.
    """
    @property
    def slice_ne(self):
        return list(self.get_verts()[
            len(self.get_verts()) // 4: (len(self.get_verts()) // 4) * 2 + 1
        ]) + [list(self.get_center())]
        # return list(self.get_verts()[6:13]) + [list(self.get_center())]
    @property
    def slice_se(self):
        return list(self.get_verts()[
            0 : len(self.get_verts()) // 4 + 1
        ]) + [list(self.get_center())]
        # return list(self.get_verts()[:7]) + [list(self.get_center())]
    @property
    def slice_sw(self):
        return list(self.get_verts()[
            len(self.get_verts()) // 4 * 3 :
        ]) + [list(self.get_center())]
        # return list(self.get_verts()[-7:]) + [list(self.get_center())]
    @property
    def slice_nw(self):
        return list(self.get_verts()[
            len(self.get_verts()) // 4 * 2: (len(self.get_verts()) // 4) * 3 + 1
        ]) + [list(self.get_center())]
        # return list(self.get_verts()[12:19]) + [list(self.get_center())]

class Hurdat2Reports:

    def from_map(self, landfall_assist=True, digits=3, **kw):
        """
        Returns a list of clicked-coordinates from a mpl-interactive map where
        the coordinates are tuples in (longitude, latitude) format. Initialized
        map extents are relative to the atlantic or east/central pacific basins.

        This method is designed to be a companion to the
        <TropicalCyclone>.crosses method. If the list is passed to the
        aforementioned method, it will be tested against a cyclone's track.
        This can be useful to narrow down crossings over certain bearings and
        landfalls across a coordinate polyline of interest.

        Controls (also displayed on the interactive map):
        -------------------------------------------------
        Alt + LeftClick -> Add a point to the path
        Alt + RightClick -> Remove previous point from the path
        Alt + C -> Erase/Clear Path (start over)
        Q (mpl-defined shortcut) -> close the screen but return the coordinates

        N: toggle landfall_assist and any drawn arrows
        <SHIFT> + arrows: Zoom
        <CTRL> + arrows: Pan

        Default Arguments:
        ------------------
            landfall_assist (True): This is an aid to assist you in drawing a
                path in the proper direction if testing for landfall or
                direction-dependent barrier crossing using the
                <TropicalCyclone>.crosses method. If True, semi-transparent
                arrows will be placed on the map to show from what direction
                intersection would be tested for. A convenience kb shortcut
                (L) has been included to toggle the display of the arrows
            digits (3): The number of decimal places (precision) that the
                returned coordinates will have.

        Keyword Arguments
        -----------------
            backend (None): what mpl backend to request using
        """
        if kw.get("backend"):
            matplotlib.use(kw.get("backend"))

        plt.ion()

        def add_point(x,y):
            nonlocal clicked_coords
            nonlocal point
            nonlocal _arrows

            try:
                point.remove()
            except Exception as e:
                # print(e)
                pass

            clicked_coords.append(
                (
                    float(x),
                    float(y)
                )
            )
            point = plt.scatter(
                x, y,
                s = matplotlib.rcParams['lines.markersize'] ** 1.5,
                facecolor = "black",
            )
            # draw arrow dependent upon landfall_assist
            try:
                segment = _gis.BoundingBox(
                    _gis.Coordinate(*clicked_coords[-2]),
                    _gis.Coordinate(*clicked_coords[-1]),
                )
                rotated = segment.rotate(-90)
                
                arrow_maxlen = 10
                _dx = rotated.delta_x
                _dy = rotated.delta_y
                # modify if arrow is not user friendly
                if rotated.length > arrow_maxlen:
                    _dx = rotated.delta_hypot(arrow_maxlen).delta_x
                    _dy = rotated.delta_hypot(arrow_maxlen).delta_y
                _width = min(
                    rotated.length * 0.2,
                    1.5
                )
                _arrows.append(
                    ax.arrow(
                        rotated.p1.x,
                        rotated.p1.y,
                        _dx,
                        _dy,
                        width = _width,
                        head_width = _width * 2.5,
                        head_length = _width * 1.5,
                        length_includes_head = True,
                        # headwidth=segment.length * 0.9 * 19/8,
                        facecolor=(1,0,0,0.3),
                        edgecolor=(1,1,1,0),
                        visible = landfall_assist
                    )
                )
            except Exception as e:
                pass

        def remove_point():
            nonlocal clicked_coords
            nonlocal point
            nonlocal _arrows

            try:
                point.remove()
            except Exception as e:
                # print(e)
                pass

            if len(clicked_coords) > 0:
                del clicked_coords[-1]
                try:
                    point = plt.scatter(
                        *clicked_coords[-1],
                        s = matplotlib.rcParams['lines.markersize'] ** 1.5,
                        facecolor = "black",
                    )
                    _arrows.pop().remove()
                except Exception as e:
                    pass

        def onclick(event):
            nonlocal point
            nonlocal line
            nonlocal _arrows
            nonlocal clicked_coords

            if str(event.key).lower() == "alt":
                # Add a point/segment (alt + left click)
                if event.button.value == 1:
                    add_point(
                        round(event.xdata, digits),
                        round(event.ydata, digits)
                    )
                # remove point/segment (alt + right click)
                if event.button.value == 3:
                    remove_point()

                # combine all clicked coordinates into one
                if len(clicked_coords) >= 1:
                    try:
                        line[-1].remove()
                    except:
                        pass
                    line = plt.plot(
                        [x for x,y in clicked_coords],
                        [y for x,y in clicked_coords],
                        color = "red",
                    )

        def onpress(event):
            nonlocal point
            nonlocal line
            nonlocal _arrows
            nonlocal landfall_assist
            nonlocal clicked_coords
            # print(event.__dict__)

            try:
                # add home view if not already appended
                if len(fig.canvas.toolbar._nav_stack) == 0:
                    fig.canvas.toolbar.push_current()
            except:
                pass

            if str(event.key).lower() == "alt+c":
                try:
                    line[-1].remove()
                    point.remove()
                    clicked_coords = []
                    for arw in _arrows:
                        arw.remove()
                    _arrows = []
                except:
                    pass

            # ylim (south, north)
            # xlim (west, east)

            # aspect ratio >= 1 -> x <= y
            # aspect ratio < 1 -> x > y
            ar = abs(operator.sub(*ax.get_ylim()) / operator.sub(*ax.get_xlim()))

            # toggle landfall assist
            if event.key.lower() == "n":
                landfall_assist = not landfall_assist
                lfall_text.set_text(
                    "Landfall Assist (key: N): {}".format(
                        "ON" if landfall_assist else
                        "OFF"
                    )
                )
                # toggle visibility of the arrows
                for arrow in _arrows:
                    arrow.set_visible(landfall_assist)

            # Zoom in (shift + up or right)
            if event.key.lower() in [
                "shift+" + arrow for arrow in ("up","right")
            ]:
                min_span = 4
                # ensure valid zoom in to avoid folding
                new_xlim = (
                    ax.get_xlim()[0] + 3 * (ar if ar >= 1 else 1),
                    ax.get_xlim()[1] - 3 * (ar if ar >= 1 else 1)
                )
                new_ylim = (
                    ax.get_ylim()[0] + 3 * (ar if ar < 1 else 1),
                    ax.get_ylim()[1] - 3 * (ar if ar < 1 else 1)
                )
                # only zoom in if no folding will occur (west extent > east extent)
                # and if the zoom-in won't be too much
                if operator.le(*new_xlim) and operator.le(*new_ylim) \
                and abs(operator.sub(*new_xlim)) > min_span \
                and abs(operator.sub(*new_ylim)) > min_span:
                    ax.set_xlim(
                        ax.get_xlim()[0] + 3 * (ar if ar >= 1 else 1),
                        ax.get_xlim()[1] - 3 * (ar if ar >= 1 else 1),
                    )
                    ax.set_ylim(
                        ax.get_ylim()[0] + 3 * (ar if ar < 1 else 1),
                        ax.get_ylim()[1] - 3 * (ar if ar < 1 else 1),
                    )
                    # Record the new view in the navigation stack (so home/back/forward will work)
                    try:
                        fig.canvas.toolbar.push_current()
                    except:
                        pass
                # if it would zoom in too much, but the extents wouldn't fold,
                #   zoom in, but do so at a minimum
                elif operator.le(*new_xlim) and operator.le(*new_ylim):
                    ax.set_xlim(
                        statistics.mean(new_xlim) - 2,
                        statistics.mean(new_xlim) + 2,
                    )
                    ax.set_ylim(
                        statistics.mean(new_ylim) - 2,
                        statistics.mean(new_ylim) + 2,
                    )
                    # Record the new view in the navigation stack (so home/back/forward will work)
                    try:
                        fig.canvas.toolbar.push_current()
                    except:
                        pass
            # Zoom out (shift + up or right)
            if event.key.lower() in [
                "shift+" + arrow for arrow in ("down","left")
            ]:
                ax.set_xlim(
                    ax.get_xlim()[0] - 3 * (ar if ar >= 1 else 1),
                    ax.get_xlim()[1] + 3 * (ar if ar >= 1 else 1),
                )
                # Record the new view in the navigation stack (so home/back/forward will work)
                try:
                    fig.canvas.toolbar.push_current()
                except:
                    pass

            # pan (ctrl+arrows)
            if event.key.lower() in [
                "ctrl+" + arrow for arrow in ("up","down","left","right")
            ]:
                everybody_move = min(
                    abs(operator.sub(*ax.get_ylim())) / 5,
                    abs(operator.sub(*ax.get_xlim())) / 5,
                )
                ax.set_xlim(
                    ax.get_xlim()[0] + (
                        everybody_move if "right" in event.key else
                        everybody_move * -1 if "left" in event.key else
                        0
                    ),
                    ax.get_xlim()[1] + (
                        everybody_move if "right" in event.key else
                        everybody_move * -1 if "left" in event.key else
                        0
                    ),
                )
                ax.set_ylim(
                    ax.get_ylim()[0] + (
                        everybody_move if "up" in event.key else
                        everybody_move * -1 if "down" in event.key else
                        0
                    ),
                    ax.get_ylim()[1] + (
                        everybody_move if "up" in event.key else
                        everybody_move * -1 if "down" in event.key else
                        0
                    ),
                )
                # Record the new view in the navigation stack (so home/back/forward will work)
                try:
                    fig.canvas.toolbar.push_current()
                except Exception as e:
                    pass

        point = None
        line = None
        _arrows = []
        clicked_coords = []
        # matplotlib.use("TkAgg")
        matplotlib.rcParams['path.simplify_threshold'] = 1

        fig = plt.figure(
            num = "Path Selector",
            figsize = (
                matplotlib.rcParams["figure.figsize"][0],
                matplotlib.rcParams["figure.figsize"][0]
            ),
            layout = "constrained",
        )
        cid = fig.canvas.mpl_connect("button_press_event", onclick)
        fig.canvas.mpl_connect("key_press_event", onpress)
        plt.ion()
        figman = plt.get_current_fig_manager()
        figman.set_window_title(fig._label)

        figtitle = fig.suptitle(
            "\n".join([
                "Path Selector",
                "Alt+<LeftClick>: Add point to the path",
                "Alt+<RightClick>: Remove previous point from the path",
                "Alt+C: Erase/Clear Path",
                "Q: Finish / Return path",
            ]),
            fontsize = "small",
            linespacing = 0.8,
        )

        ax = plt.axes(
            facecolor = "lightblue",
            aspect="equal",
            adjustable="datalim",   # aspect: equal and adj: datalim allows 1:1 in data-coordinates!
        )

        # Set the axis labels
        ax.set_ylabel("Latitude")
        ax.set_xlabel("Longitude")
        ax.yaxis.set_major_locator(_ticker.MultipleLocator(5))
        ax.yaxis.set_minor_locator(_ticker.MultipleLocator(1))
        ax.xaxis.set_major_locator(_ticker.MultipleLocator(5))
        ax.xaxis.set_minor_locator(_ticker.MultipleLocator(1))
        ax.grid(True, color=(0.3, 0.3, 0.3))
        ax.grid(True, which="minor", color=(0.6, 0.6, 0.6), linestyle=":")

        # Draw Map

        for postal, geo in _maps._polygons:
            for polygon in geo:
                ax.fill(
                    [lon for lon, lat in polygon],
                    [lat for lon, lat in polygon],
                    color = "lightseagreen",
                    edgecolor = "black",
                    linewidth = 0.5,
                )
        for lake, geo in _maps._lakes:
            for polygon in geo:
                ax.fill(
                    [lon for lon, lat in polygon],
                    [lat for lon, lat in polygon],
                    color = "lightblue",
                    edgecolor = "black",
                    linewidth = 0.3,
                )

        # Equator
        # ax.plot([-180,180], [0,0], color="red")

        # pacific basins
        if "EP" in self.basin_abbr() or "CP" in self.basin_abbr():
            ax.set_xlim(-160, -80)
        # atlantic
        else:
            ax.set_xlim(-100, -40)
        ax.set_ylim(0, 60)
        # ax.set_box_aspect(1)
        # ax.set_ylim(
            # 42.5 - 85 * 3/4 / 2,
            # 42.5 + 85 * 3/4 / 2,
        # )
        mplstyle.use("fast")

        # KB Shortcuts
        plt.figtext(
            0.995,
            0.01,
            "\n".join([
                "<SHIFT> + arrows: Zoom-in",
                "<CTRL> + arrows: Pan",
            ]),
            color = (0,0,0,0.6),
            ha = "right",
            fontsize = "x-small",
        )

        # landfall assist toggle
        lfall_text = plt.figtext(
            0.005,
            0.01,
            "Landfall Assist (N): {}".format(
                "ON" if landfall_assist else
                "OFF"
            ),
            color = (0,0,0,0.6),
            fontsize = "small",
        )

        # Map credits
        plt.text(
            0.995,
            0.01,
            "Map Data: Made with Natural Earth",
            ha = "right",
            fontsize = "x-small",
            bbox = dict(
                boxstyle = "Square, pad=0.1",
                # edgecolor = (1,1,1,0),
                facecolor = (1,1,1,0.6),
                linewidth = 0,
            ),
            transform = ax.transAxes,
        )

        plt.show(block=True)

        return clicked_coords

    def multi_season_info(self, year1=None, year2=None):
        """Grab a chunk of multi-season data and report on that climate era.
        This method can be viewed as a climatological era info method.
        
        Default Arguments:
            year1 (None): The start year
            year2 (None): The end year
        """

        year1 = self.record_range[0] if year1 is None \
            or year1 < self.record_range[0] else year1
        year2 = self.record_range[1] if year2 is None \
            or year2 > self.record_range[1] else year2
        # ---------------------

        yrrange = range(year1, year2+1)
        clmt = ClimateEra(
            era = (year1, year2),
            tracks = sum(self.season[s].tracks for s in yrrange),
            landfalls = sum(self.season[s].landfalls for s in yrrange),
            landfall_TC = sum(self.season[s].landfall_TC for s in yrrange),
            landfall_TD = sum(self.season[s].landfall_TD for s in yrrange),
            landfall_TS = sum(self.season[s].landfall_TS for s in yrrange),
            landfall_HU = sum(self.season[s].landfall_HU for s in yrrange),
            landfall_MHU = sum(self.season[s].landfall_MHU for s in yrrange),
            TSreach = sum(self.season[s].TSreach for s in yrrange),
            TSonly = sum(self.season[s].TSonly for s in yrrange),
            HUreach = sum(self.season[s].HUreach for s in yrrange),
            HUonly = sum(self.season[s].HUonly for s in yrrange),
            MHUreach = sum(self.season[s].MHUreach for s in yrrange),
            cat45reach = sum(self.season[s].cat45reach for s in yrrange),
            cat5reach = sum(self.season[s].cat5reach for s in yrrange),
            track_distance = sum(self.season[s].track_distance for s in yrrange),
            track_distance_TC = sum(self.season[s].track_distance_TC for s in yrrange),
            track_distance_TS = sum(self.season[s].track_distance_TS for s in yrrange),
            track_distance_HU = sum(self.season[s].track_distance_HU for s in yrrange),
            track_distance_MHU = sum(self.season[s].track_distance_MHU for s in yrrange),
            ACE = sum(self.season[s].ACE for s in yrrange),
            HDP = sum(self.season[s].HDP for s in yrrange),
            MHDP = sum(self.season[s].MHDP for s in yrrange)
        )

        # Print Report
        totalyrs = year2 - year1 + 1
        print("")
        print(" --------------------------------------------------------")
        print(" Tropical Cyclone Season Stats, for {} to {}".format(year1, year2))
        print(" --------------------------------------------------------")
        print(" {:^56}".format(
            "* Distances in nmi; * Energy Indices in 10**(-4) kt^2"
        ))
        print(" --------------------------------------------------------")
        print(" Avg Track Qty (Total): {}/yr ({})".format(
            round(clmt.tracks / totalyrs,1),
            clmt.tracks
        ))
        print(" Avg TC Track Distance (Total): {}/yr ({})".format(
            round(clmt.track_distance_TC / totalyrs,1),
            round(clmt.track_distance_TC,1)
        ))
        print(" Avg TS Qty (Total): {}/yr ({})".format(
            round(clmt.TSreach / totalyrs,1),
            clmt.TSreach
        ))
        print("   -- Avg TS Track Distance (Total): {}/yr ({})".format(
            round(clmt.track_distance_TS / totalyrs,1),
            round(clmt.track_distance_TS,1)
        ))
        print("   -- Avg ACE (Total): {}/yr ({})".format(
            round(clmt.ACE * 10**(-4) / totalyrs,1),
            round(clmt.ACE * 10**(-4),1)
        ))
        print(" Avg HU Qty (Total): {}/yr ({})".format(
            round(clmt.HUreach / totalyrs,1),
            clmt.HUreach
        ))
        print("   -- Avg HU Track Distance (Total): {}/yr ({})".format(
            round(clmt.track_distance_HU / totalyrs,1),
            round(clmt.track_distance_HU,1)
        ))
        print("   -- Avg HDP (Total): {}/yr ({})".format(
            round(clmt.HDP * 10**(-4) / totalyrs,1),
            round(clmt.HDP * 10**(-4),1)
        ))
        print(" Avg MHU Qty (Total): {}/yr ({})".format(
            round(clmt.MHUreach / totalyrs,1),
            clmt.MHUreach
        ))
        print(" Avg Cat-4 and Cat-5 Qty (Total): {}/yr ({})".format(
            round(clmt.cat45reach / totalyrs,1),
            clmt.cat45reach
        ))
        print(" Avg Cat-5 Qty (Total): {}/yr ({})".format(
            round(clmt.cat5reach / totalyrs,1),
            clmt.cat5reach
        ))
        print("   -- Avg MHU Track Distance (Total): {}/yr ({})".format(
            round(clmt.track_distance_MHU / totalyrs,1),
            round(clmt.track_distance_MHU,1)
        ))
        print("   -- Avg MHDP (Total): {}/yr ({})".format(
            round(clmt.MHDP * 10**(-4) / totalyrs,1),
            round(clmt.MHDP * 10**(-4),1)
        ))
        print(" Avg Landfalling System Qty (Total): {}/yr ({})".format(
            round(clmt.landfall_TC / totalyrs,1),
            clmt.landfall_TC
        ))
        print("")

    def output_climo(self, climo_len=30):
        """Output a csv of stats from all climatological eras from the record
        of specifiable era-spans. Temporal separations of 1-year increments
        will be used.

        Default Arguments:
            climo_len (30): The length of time in years each climate era will
                be assessed.
        """

        ofn = "{}_HURDAT2_{}-yr_climatology.csv".format(
            "".join(self.basin_abbr()),
            climo_len
        )
        
        if os.path.exists(ofn):
            choice = input(
                "* A file named '{}' already exists.".format(ofn) \
                + "Continue? (y/n): "
            )
            if choice.lower()[0] != "y": return None
        print("** PLEASE WAIT; THIS MAY TAKE A MOMENT **")

        year1, year2 = self.record_range
        climo = {}
        for yr1, yr2 in [
            (y, y+climo_len-1) \
            for y in range(year1, year2+1) \
            if year1 <= y <= year2 \
            and year1 <= y+climo_len-1 <= year2
        ]:
            climo[yr1, yr2] = Era(
                *(
                    [(yr1, yr2)] + [
                        sum(getattr(self.season[s], attr)
                        for s in range(yr1, yr2+1))
                        for desc, attr in CSV_CLIMO_VARS[1:]
                    ]
                )
            )

        with open(ofn, "w", newline="") as w:
            out = csv.writer(w)
            out.writerow([desc for desc, attr in CSV_CLIMO_VARS])
            for clmt in climo.values():
                out.writerow(
                    ["{}-{}".format(*clmt.era)] \
                  + [getattr(clmt, attr) for desc, attr in CSV_CLIMO_VARS[1:]]
                )

    def output_seasons_csv(self):
        """Output a csv of season-based stats from the record. In general, this
        method really only has need to be called once. The primary exception to
        this suggestion would only occur upon official annual release of the
        HURDAT2 record.
        """
        ofn = "{}_HURDAT2_seasons_summary.csv".format(
            "".join(self.basin_abbr())
        )
        with open(ofn, "w", newline="") as w:
            out = csv.writer(w)
            out.writerow([desc for desc, attr in CSV_SEASON_VARS])
            for y in self.season.values():
                out.writerow(
                    [getattr(y, attr) for desc, attr in CSV_SEASON_VARS]
                )

    def output_storms_csv(self):
        """Output a csv of individual storm-based stats from the record. In
        general, this method really only has need to be called once. The
        primary exception to this suggestion would only occur upon official
        annual release of the HURDAT2 record.
        """
        ofn = "{}_HURDAT2_storms_summary.csv".format(
            "".join(self.basin_abbr())
        )
        with open(ofn, "w", newline="") as w:
            out = csv.writer(w)
            out.writerow([desc for desc, attr in CSV_TC_VARS])
            for tc in self.tc.values():
                out.writerow(
                    [getattr(tc, attr) for desc, attr in CSV_TC_VARS]
                )

    def climograph(self, attr, climatology=30, increment=5, **kw):
        """Returns a basic climatological graph.

        Args:
            attr: the attribute wanted to graph

        Default Keyword Arguments:
            climatology (30): the length in years that a climatology should be
                assessed.
            increment (5): The temporal frequency of assessment of a
                climatology (in years).

        Keyword Arguments:
            year1: the start year for assessment
            year2: the end year for assessment
        """
        _w, _h = _figure.figaspect(kw.get("aspect_ratio", 3/5))
        fig = plt.figure(
            figsize = (_w, _h),
            layout = "tight",
        )
        plt.get_current_fig_manager().set_window_title(
            "{} {} Climatological Tendency, {}".format(
                attr,
                "{}yr / {}yr incremented".format(
                    climatology,
                    increment
                ),
                self.basin()
            )
        )
        fig.suptitle(
            "{} {} Climatological Tendency\n{}".format(
                attr,
                "{}yr / {}yr Incremented".format(
                    climatology,
                    increment
                ),
                self.basin()
            )
        )
        ax = plt.axes(
            xlabel = "Climate Era",
            ylabel = attr
        )
        ax.plot(
            [
                "{}-{}".format(y, y+climatology-1) \
                for y in range(
                    kw.get("year1", self.record_range[0]),
                    kw.get("year2", self.record_range[1]) + 1 - climatology,
                ) if (y+climatology-1) % increment == 0
            ],
            [
                sum(
                    getattr(self.season[s], attr) \
                    for s in range(
                        y,
                        y+climatology
                    )
                ) for y in range(
                    kw.get("year1", self.record_range[0]),
                    kw.get("year2", self.record_range[1]) + 1 - climatology,
                ) if (y+climatology-1) % increment == 0
            ]
        )

        ax.xaxis.set_tick_params(
            rotation = 90
        )
        plt.grid(True)
        plt.show(block=False)

class SeasonReports:

    def output_shp(self):
        """Uses the shapefile module to output a GIS-compatible shapefile of
        the tracks of all storms documented during a particular season. It is
        output to the current directory.
        """
        ofn = "{}_{}_tracks".format(
            self.year,
            "".join(self._hd2.basin_abbr())
        )
        with shapefile.Writer(ofn,shapeType=3) as gis:
            gis.field("ATCFID","C","8")
            gis.field("NAME","C","10")
            gis.field("START","C","16")
            gis.field("END","C","16")
            gis.field("MAXWIND","N","3")
            gis.field("MINMSLP","N","4")
            gis.field("ACE (x10^4)","N","12",3)
            gis.field("HDP (x10^4)","N","12",3)
            gis.field("MHDP (x10^4)","N","12",3)
            gis.field("TRK_DIST_NMI","N","22",1)
            gis.field("TRK_DIST_TC_NMI","N","22",1)
            gis.field("TRK_DIST_TS_NMI","N","22",1)
            gis.field("TRK_DIST_HU_NMI","N","22",1)
            gis.field("TRK_DIST_MHU_NMI","N","22",1)
            for trop in self.tc:
                gis.record(
                    self.tc[trop].atcfid,
                    self.tc[trop].name,
                    self.tc[trop].entry[0].entrytime.isoformat(),
                    self.tc[trop].entry[-1].entrytime.isoformat(),
                    self.tc[trop].maxwind,
                    self.tc[trop].minmslp if self.tc[trop].minmslp != None else 9999,
                    self.tc[trop].ACE * math.pow(10,-4),
                    self.tc[trop].HDP * math.pow(10,-4),
                    self.tc[trop].MHDP * math.pow(10,-4),
                    self.tc[trop].track_distance,
                    self.tc[trop].track_distance_TC,
                    self.tc[trop].track_distance_TS,
                    self.tc[trop].track_distance_HU,
                    self.tc[trop].track_distance_MHU
                )
                entiretrack = [self.tc[trop].entry[trk].location_reversed for trk in range(len(self.tc[trop].entry))]
                gis.line([entiretrack])

    def output_shp_segmented(self):
        """Uses the shapefile module to output a GIS-compatible shapefile of
        individual segments (as separate geometries) of each system from the
        season. Use this if you'd like the idea of coloring the tracks by
        saffir-simpson strength controlled by the segments.
        """
        ofn = "{}_{}_tracks_segmented".format(
            self.year,
            "".join(self._hd2.basin_abbr())
        )
        c = itertools.count(0)
        with shapefile.Writer(ofn,shapeType=3) as gis:
            gis.field("ID","N","3")
            gis.field("ATCFID","C","8")
            gis.field("ENTRY_INDEX","N")
            gis.field("NAME","C","10")
            gis.field("ENTRY_TIME","C","16")
            gis.field("NEXT_ENTRY_TIME","C","16")
            gis.field("LAT","N",decimal=1)
            gis.field("LON","N",decimal=1)
            gis.field("NEXT_ENTRY_LAT","N",decimal=1)
            gis.field("NEXT_ENTRY_LON","N",decimal=1)
            gis.field("STATUS","C","3")
            gis.field("PEAK_WIND","N","3")
            gis.field("MIN_MSLP","N","4")
            for TC in [t[1] for t in self.tc.items()]:
                for track in range(len(TC.entry)):
                    gis.record(
                        next(c),
                        TC.atcfid,
                        track,
                        TC.name,
                        TC.entry[track].entrytime.isoformat(),
                        TC.entry[track+1].entrytime.isoformat() if track != len(TC.entry)-1 else None,
                        TC.entry[track].location[0],
                        TC.entry[track].location[1],
                        TC.entry[track+1].location[0] if track != len(TC.entry)-1 else None,
                        TC.entry[track+1].location[1] if track != len(TC.entry)-1 else None,
                        TC.entry[track].status,
                        TC.entry[track].wind if TC.entry[track].wind > 0 else "",
                        TC.entry[track].mslp if TC.entry[track].mslp != None else ""
                    )
                    if track != len(TC.entry)-1:
                        gis.line([[TC.entry[track].location_reversed,TC.entry[track+1].location_reversed]])
                    else:
                        gis.null()

    def output_geojson(self, INDENT=2):
        """Uses the geojson module to output a GIS-compatible geojson of the
        tracks of all storms documented during a particular season. It is
        output to the current directory.

        Default Argument:
            INDENT = 2; used to provide indention to the output. Though it
                makes the output prettier and easier to read, it increases the
                file size.
        """
        ofn = "{}_{}_tracks.geojson".format(
            self.year,
            "".join(self._hd2.basin_abbr())
        )
        # Ensure indention is an int
        INDENT = int(INDENT)

        feats = []
        stormnum = itertools.count(1)
        for TC in [tc[1] for tc in self.tc.items()]:
            ls = geojson.LineString([(trk.lon,trk.lat) for trk in TC.entry])
            prp = {
                "ID": next(stormnum),
                "ATCFID": TC.atcfid,
                "NAME": TC.name,
                "START": TC.entry[0].entrytime.isoformat(),
                "END": TC.entry[-1].entrytime.isoformat(),
                "MAXWIND": TC.maxwind,
                "MINMSLP": TC.minmslp,
                "ACE (x10^4)": round(TC.ACE * math.pow(10,-4), 3),
                "HDP (x10^4)": round(TC.HDP * math.pow(10,-4), 3),
                "MHDP (x10^4)": round(TC.MHDP * math.pow(10,-4), 3),
                "TRK_DIST_NMI": round(TC.track_distance, 1),
                "TRK_DIST_TC_NMI": round(TC.track_distance_TC, 1),
                "TRK_DIST_TS_NMI": round(TC.track_distance_TS, 1),
                "TRK_DIST_HU_NMI": round(TC.track_distance_HU, 1),
                "TRK_DIST_MHU_NMI": round(TC.track_distance_MHU, 1)
            }
            feats.append(geojson.Feature(geometry=ls, properties=prp))
        gjs = geojson.FeatureCollection(feats)
        with open(ofn,"w") as w:
            w.write(geojson.dumps(gjs, indent=INDENT))

    def output_geojson_segmented(self, INDENT=2):
        """Uses the geojson module to output a GIS-compatible geojson of
        individual segments (as separate geometries) of each system from the
        season. Use this if you'd like the idea of coloring the tracks by
        saffir-simpson strength controlled by the segments.

        Default Argument:
            INDENT = 2; used to provide indention to the output. Though it
                makes the output prettier and easier to read, it increases the
                file size.
        """
        ofn = "{}_{}_tracks_segmented.geojson".format(
            self.year,
            "".join(self._hd2.basin_abbr())
        )

        # Ensure indention is an int
        INDENT = int(INDENT)

        feats = []
        for TC in [tc[1] for tc in self.tc.items()]:
            for trk in range(len(TC.entry)):
                ls = geojson.LineString([
                    (TC.entry[trk].lon,TC.entry[trk].lat),
                    (TC.entry[trk+1].lon,TC.entry[trk+1].lat),
                ]) if trk != len(TC.entry)-1 else geojson.LineString([])
                prp = {
                    "ENTRY_ID": trk,
                    "ATCFID": TC.atcfid,
                    "NAME": TC.name,
                    "ENTRY_TIME": TC.entry[trk].entrytime.isoformat(),
                    "LAT": TC.entry[trk].lat,
                    "LON": TC.entry[trk].lon,
                    "STATUS": TC.entry[trk].status,
                    "PEAK_WIND": TC.entry[trk].wind if TC.entry[trk].wind > 0 else None,
                    "MSLP": TC.entry[trk].mslp
                }
                feats.append(geojson.Feature(geometry=ls, properties=prp))
        gjs = geojson.FeatureCollection(feats)
        with open(ofn,"w") as w:
            w.write(geojson.dumps(gjs, indent=INDENT))

class TropicalCycloneReports:

    def output_shp(self):
        """Uses the shapefile module to output a shapefile of the Tropical
        Cyclone/System.
        """
        ofn = "{}_{}_tracks".format(self.atcfid,self.name)
        with shapefile.Writer(ofn,shapeType=3) as gis:
            gis.field("ENTRY_INDEX","N","3")
            gis.field("ATCFID","C","8")
            gis.field("NAME","C","10")
            gis.field("ENTRY_TIME","C","16")
            gis.field("LAT","N",decimal=1)
            gis.field("LON","N",decimal=1)
            gis.field("STATUS","C","3")
            gis.field("PEAK_WIND","N","3")
            gis.field("MIN_MSLP","N","4")
            for track in range(len(self.entry)):
                gis.record(
                    track,
                    self.atcfid,
                    self.name,
                    self.entry[track].entrytime.isoformat(),
                    self.entry[track].lat,
                    self.entry[track].lon,
                    self.entry[track].status,
                    self.entry[track].wind if self.entry[track].wind > 0 else None,
                    self.entry[track].mslp)
                if track != len(self.entry)-1:
                    gis.line([[self.entry[track].location_reversed,self.entry[track+1].location_reversed]])
                else: gis.null()

    def output_geojson(self, INDENT=2, feature_type="line"):
        """Uses the geojson module to output a geojson file of the tropical
        cyclone.

        Default Arguments:
            INDENT = 2; used to provide indention to the output. Though it
                makes the output prettier and easier to read, it increases the
                file size.
            feature_type = "line"; determines the type of feature used in
                compiling the geoJSON file. "line" (default) indicates a
                geoJSON ``LineString`` while "point" indicates a geoJSON
                ``Point``.
        """
        if feature_type.lower() not in ["point", "line"]:
            raise TypeError("param feature_type must be either 'point' or 'line'.")

        ofn = "{}_{}_tracks_{}.geojson".format(self.atcfid, self.name, feature_type)

        # Ensure indention is an int
        INDENT = int(INDENT)

        feats = []
        for trk in range(len(self.entry)):
            # Point feature
            if feature_type.lower() == "point":
                ls = geojson.Point(
                    (self.entry[trk].lon, self.entry[trk].lat)
                )
            # Polyline Feature
            elif feature_type.lower() == "line":
                ls = geojson.LineString([
                    (self.entry[trk].lon,self.entry[trk].lat),
                    (self.entry[trk+1].lon,self.entry[trk+1].lat),
                ]) if trk != len(self.entry)-1 else geojson.LineString([])
            prp = {
                "ENTRY_ID": trk,
                "ATCFID": self.atcfid,
                "NAME": self.name,
                "ENTRY_TIME": self.entry[trk].entrytime.isoformat(),
                "LAT": self.entry[trk].lat,
                "LON": self.entry[trk].lon,
                "STATUS": self.entry[trk].status,
                "PEAK_WIND": self.entry[trk].wind if self.entry[trk].wind > 0 else None,
                "MSLP": self.entry[trk].mslp
            }
            feats.append(geojson.Feature(geometry=ls, properties=prp))
        gjs = geojson.FeatureCollection(feats)
        with open(ofn,"w") as w:
            w.write(geojson.dumps(gjs, indent=INDENT))

    def track_map(self, **kw):
        """Return a map of the tropical-cyclone's track via matplotlib
        (referred further as "mpl"). Each track will be color-coded based on
        associated wind-speed and storm-status. Colors are controlled by
        saffir-simpson scale equivalent winds. When a system is not a
        designated tropical cyclone, its track will be represented as a dotted
        (rather than solid) line.

        Keyboard Shortcuts
        ------------------
            Zoom: <SHIFT> + arrows
            Pan: <CTRL> + arrows
            Toggle Legend: N

        * Clicking on a track segment will reveal basic information about the
        <TCRecordEntry> that sources the segment. Clicking on an empty part of
        the map will remove the label

        * Map feature coordinate data from Natural Earth (naturalearthdata.com)

        Accepted Keyword Arguments:
        -----------------------------------
            block (True): bool that applies to the "block" kw of the mpl pyplot
                show method. The default value of True reflects the same of mpl.
                A value of False allows one to display multiple track-map
                instances at a time.
            width (None): the desired figure width in inches (will be further
                altered if using non-default dpi)
            height (None): the desired figure height in inches (will be further
                altered if using non-default dpi)
            dpi (None): affects the dpi of the figure. Generally speaking, a
                smaller dpi -> smaller figure. larger dpi -> larger figure  If
                <None>, the matplotlib default (100) is used.
            ocean (mpl-compatible color): the requested color for the
                ocean (the background); defaults to 'lightblue'.
            land (mpl-compatible color): the requested color for land-
                masses; defaults to 'lightseagreen'.
            padding (2): how much extra space (in degrees) to place on the
                focused system track. The larger this value the more map
                (zoomed out) the display will be. Negative values work too.
            labels (bool): toggle for temporal labels for entries; defaults to
                True.
            linewidth (float): the line-width of the track; defaults to 1.5.
            markersize (float): the entry-marker size; defaults to 3.
            legend (bool): whether or not you want to display a legend (default
                is True).
            draggable (False): do you want the displayed legend to be
                interactive?
            extents (bool): if True, and the data is available for a cyclone,
                tropical storm, 50kt, and hurricane-force wind-extents will be
                plotted. This defaults to False.
            saveonly (False): if True,  the method will silently save an image
                without generating a visible plot
            backend (None): what mpl backend to request using
        """

        # matplotlib.rcParams['path.simplify_threshold'] = 1

        if kw.get("backend"):
            matplotlib.use(kw.get("backend"))

        fig = plt.figure(
            num = "{} - {} Tracks".format(
                self.atcfid,
                self.name
            ),
            figsize = (
                matplotlib.rcParams["figure.figsize"][0]
                    if not kw.get("width") else kw.get("width"),
                matplotlib.rcParams["figure.figsize"][1]
                    if not kw.get("height") else kw.get("height"),
            ),
            
            layout = "constrained",
            dpi = kw.get("dpi", matplotlib.rcParams["figure.dpi"])
        )
        plt.ion()

        # declared outside of the inner function on purpose;
        # will represent mpl Artist text that gives info on TCRecordEntry
        entryinfo = None
        def canvas_click(event):
            # The purpose of this is to capture and process pick events when
            #     in zoom or pan mode otherwise, I wouldn't need it.
            nonlocal entryinfo

            if event.inaxes:
                try:
                    entryinfo.remove()
                except Exception as e:
                    pass
                # left click
                if event.button.value == 1:
                    ax.pick(event)

        def show_entry_info(event):
            nonlocal entryinfo
            if hasattr(event, "artist") and hasattr(event.artist, "tcentry"):
                try:
                    entryinfo.remove()
                except Exception as e:
                    pass
                entryinfo = plt.figtext(
                    0.005,
                    0.01,
                    "{:%Y-%m-%d %H:%MZ} - {}; {}kts; {}".format(
                        event.artist.tcentry.entrytime,
                        event.artist.tcentry.status,
                        event.artist.tcentry.wind,
                        "{}mb".format(event.artist.tcentry.mslp)
                        if event.artist.tcentry.mslp is not None
                        else "N/A",
                    ),
                    fontsize = "small",
                    fontweight = "bold",
                    color = "blue",
                    ha="left",
                )

        def kb_zoom_pan(event):
            # kb shortcuts for panning and zooming

            try:
                # add home view if not already appended
                if len(fig.canvas.toolbar._nav_stack) == 0:
                    fig.canvas.toolbar.push_current()
            except:
                pass
            
            ar = abs(operator.sub(*ax.get_ylim()) / operator.sub(*ax.get_xlim()))

            if event.key.lower() == "n":
                legend.set_visible(
                    not legend.get_visible()
                )

            # Zoom in (shift + up or right)
            if event.key in [
                "shift+" + arrow for arrow in ("up","right")
            ]:
                min_span = 4
                # ensure valid zoom in to avoid folding
                new_xlim = (
                    ax.get_xlim()[0] + 3 * (ar if ar >= 1 else 1),
                    ax.get_xlim()[1] - 3 * (ar if ar >= 1 else 1)
                )
                new_ylim = (
                    ax.get_ylim()[0] + 3 * (ar if ar < 1 else 1),
                    ax.get_ylim()[1] - 3 * (ar if ar < 1 else 1)
                )
                # only zoom in if no folding will occur (west extent > east extent)
                # and if the zoom-in won't be too much
                if operator.le(*new_xlim) and operator.le(*new_ylim) \
                and abs(operator.sub(*new_xlim)) > min_span \
                and abs(operator.sub(*new_ylim)) > min_span:
                    ax.set_xlim(
                        ax.get_xlim()[0] + 3 * (ar if ar >= 1 else 1),
                        ax.get_xlim()[1] - 3 * (ar if ar >= 1 else 1),
                    )
                    ax.set_ylim(
                        ax.get_ylim()[0] + 3 * (ar if ar < 1 else 1),
                        ax.get_ylim()[1] - 3 * (ar if ar < 1 else 1),
                    )
                    # Record the new view in the navigation stack (so home/back/forward will work)
                    try:
                        fig.canvas.toolbar.push_current()
                    except:
                        pass
                # if it would zoom in too much, but the extents wouldn't fold,
                #   zoom in, but do so at a minimum
                elif operator.le(*new_xlim) and operator.le(*new_ylim):
                    ax.set_xlim(
                        statistics.mean(new_xlim) - 2,
                        statistics.mean(new_xlim) + 2,
                    )
                    ax.set_ylim(
                        statistics.mean(new_ylim) - 2,
                        statistics.mean(new_ylim) + 2,
                    )
                    # Record the new view in the navigation stack (so home/back/forward will work)
                    try:
                        fig.canvas.toolbar.push_current()
                    except:
                        pass
            # Zoom out (shift + up or right)
            if event.key in [
                "shift+" + arrow for arrow in ("down","left")
            ]:
                ax.set_xlim(
                    ax.get_xlim()[0] - 3 * (ar if ar >= 1 else 1),
                    ax.get_xlim()[1] + 3 * (ar if ar >= 1 else 1),
                )
                # Record the new view in the navigation stack (so home/back/forward will work)
                try:
                    fig.canvas.toolbar.push_current()
                except:
                    pass

            # pan (ctrl+arrows)
            if event.key in [
                "ctrl+" + arrow for arrow in ("up","down","left","right")
            ]:
                everybody_move = min(
                    abs(operator.sub(*ax.get_ylim())) / 5,
                    abs(operator.sub(*ax.get_xlim())) / 5,
                )
                ax.set_xlim(
                    ax.get_xlim()[0] + (
                        everybody_move if "right" in event.key else
                        everybody_move * -1 if "left" in event.key else
                        0
                    ),
                    ax.get_xlim()[1] + (
                        everybody_move if "right" in event.key else
                        everybody_move * -1 if "left" in event.key else
                        0
                    ),
                )
                ax.set_ylim(
                    ax.get_ylim()[0] + (
                        everybody_move if "up" in event.key else
                        everybody_move * -1 if "down" in event.key else
                        0
                    ),
                    ax.get_ylim()[1] + (
                        everybody_move if "up" in event.key else
                        everybody_move * -1 if "down" in event.key else
                        0
                    ),
                )
                # Record the new view in the navigation stack (so home/back/forward will work)
                try:
                    fig.canvas.toolbar.push_current()
                except Exception as e:
                    pass
            # plt.ioff()

        fig.canvas.mpl_connect("button_release_event", canvas_click)
        fig.canvas.mpl_connect("pick_event", show_entry_info)
        fig.canvas.mpl_connect("key_release_event", kb_zoom_pan)

        figman = plt.get_current_fig_manager()
        figman.set_window_title(fig._label)

        fig.suptitle("Tracks for {} - {}".format(
            "{} {} ({})".format(
                self.status_highest,
                self.name.title(),
                self.atcfid
            ) if self.name != "UNNAMED" else \
            "{} - {}".format(
                self.atcfid,
                self.status_highest
            ),
            "{:%b %d}-{:{MD2}}, {}".format(
                self.entry[0].time,
                self.entry[-1].time,
                self.entry[0].time.year,
                MD2 = "%d" \
                    if self.entry[0].time.month == self.entry[-1].time.month \
                    else "%b %d"
            ) if self.entry[0].time.year == self.entry[-1].time.year else \
            "{:%Y-%m-%d} - {:%Y-%m-%d}".format(
                self.entry[0].time,
                self.entry[-1].time
            )
        ))


        # this is used in code below
        rc = matplotlib.rcParams

        ax = plt.axes(
            facecolor = kw.get("ocean", "lightblue"),
            aspect="equal",
            adjustable="datalim",   # aspect: equal and adj: datalim allows 1:1 in data-coordinates!
        )
        # self._hd2.fig = fig

        # Set the axis labels
        ax.set_ylabel("Latitude")
        ax.set_xlabel("Longitude")
        ax.yaxis.set_major_locator(_ticker.MultipleLocator(5))
        ax.yaxis.set_minor_locator(_ticker.MultipleLocator(1))
        ax.xaxis.set_major_locator(_ticker.MultipleLocator(5))
        ax.xaxis.set_minor_locator(_ticker.MultipleLocator(1))
        labelrot = 0    # initialization for label rotation

        #Legend Objects list
        legend_objects = []

        for indx, entry in enumerate(self.entry):
            # for angle comparison and label angle determination
            if entry.previous_entry is not None:
                prev_entry_angle = math.degrees(
                    math.atan2(
                        entry.lat - entry.previous_entry.lat,
                        entry.lon - entry.previous_entry.lon
                    )
                )
                prev_entry_angle += 360 if prev_entry_angle < 0 else 0
            else:
                prev_entry_angle = None

            # if entry != self.entry[-1]:
            if entry.next_entry is not None:
                # q1    0   th  90
                # q2    90  th  180
                # q3    -179.999 <= th <= -90
                # q4   -90 th  0
                entry_angle = math.degrees(
                    math.atan2(
                        entry.next_entry.lat - entry.lat,
                        entry.next_entry.lon - entry.lon
                    )
                )
                entry_angle += 360 if entry_angle < 0 else 0

                if prev_entry_angle is not None:
                    avg_entry_angle = statistics.mean([entry_angle, prev_entry_angle])
                else:
                    avg_entry_angle = None

                # labelrot = 45 if 135 <= entry_angle <= 190 else \
                          # -45 if 190 < entry_angle <= 270 else \
                          # (entry_angle - 90 + (360 if entry_angle - 90 < 0 else 0))
                # labelrot = 45 if 90 <= entry_angle < 135 else \
                           # entry_angle - 80 if 135 <= entry_angle <= 190 else \
                           # -45 if 190 < entry_angle <= 270 else \
                           # (entry_angle - 90 + (360 if entry_angle - 90 < 0 else 0))
                labelrot = avg_entry_angle - 90 + (
                        360 if avg_entry_angle -90 < 0 else 0
                    ) if avg_entry_angle is not None else \
                    45 if 90 <= entry_angle < 135 else \
                    entry_angle - 80 if 135 <= entry_angle <= 190 else \
                    -45 if 190 < entry_angle <= 270 else \
                    (entry_angle - 90 + (360 if entry_angle - 90 < 0 else 0))
                    
                halign = "left" if labelrot <= 270 else "right"
                if halign == "left" and labelrot > 120:
                    labelrot -= 180
                # print(
                    # "{:%Y-%m-%d %Hz}".format(entry.time),
                    # round(prev_entry_angle,1) if prev_entry_angle is not None else None,
                    # round(entry_angle,1),
                    # round(avg_entry_angle,1) if avg_entry_angle is not None else None,
                    # round(labelrot,1),
                    # halign
                # )
                # offset ? =  - 180 + (360 if entry.lon - 180 < -180 else 0)
                # offset ? =  360 if entry.lon < 0 else 0
                line2dobj_list = ax.plot(
                    [
                        entry.lon,
                        entry.next_entry.lon
                    ],
                    [entry.lat, entry.next_entry.lat],
                    color = "#FF38A5" if entry.saffir_simpson == 5 else
                         "purple" if entry.saffir_simpson == 4 else
                         "red" if entry.saffir_simpson == 3 else
                         "orange" if entry.saffir_simpson == 2 else
                         "yellow" if entry.saffir_simpson == 1 else
                         "green" if entry.saffir_simpson == 0 else
                         "black",
                    marker = ".",
                    markersize = kw.get("markersize", 3),
                    markeredgecolor = "black",
                    markerfacecolor = "black",
                    linestyle = "-" if entry.status in ["HU", "TS", "TD"]
                        else (0, (3,1,1,1)) if entry.status in ["SS", "SD"]
                        else ":",
                    linewidth = kw.get("linewidth", rc["lines.linewidth"])
                        if kw.get("extents", False) else
                        kw.get("linewidth", rc["lines.linewidth"]) + 1
                        if entry.is_TC and entry.saffir_simpson >= 3 else
                        kw.get("linewidth", rc["lines.linewidth"])
                        if entry.is_TC and entry.saffir_simpson >= 0 else
                        kw.get("linewidth", rc["lines.linewidth"]) - 0.25,
                    label = "Category {}".format(entry.saffir_simpson)
                        if entry.status == "HU"
                        else entry._status_desc if entry.is_TC
                        else "Post/Potential Tropical Cyclone"
                )
                # 'mouseover' stuff
                point = line2dobj_list[0]
                point.tcentry = entry
                point.set_picker(True)
                point.set_pickradius(5)
                # line2dobj_list[0].mouseover = True
                # line2dobj_list[0].format_cursor_data("TESTING");
                # print(line2dobj_list[0].get_cursor_data(None))

                # Add a label to the legend if one doesn't exist already
                if point.get_label() not in [
                    pt.get_label() for pt in legend_objects
                ]:
                    point.order_value = entry.saffir_simpson \
                        if point.tcentry.is_TC else -2
                    
                    legend_objects.append(point)

            if kw.get("labels", True):
                if entry.record_identifier == "L":
                    ax.annotate(
                        "  L        ",
                        (entry.lon, entry.lat),
                        fontsize = 10,
                        fontweight = "bold",
                        rotation = labelrot,
                        rotation_mode = "anchor",
                        horizontalalignment = halign,
                        verticalalignment = "center_baseline",
                        clip_on = True,
                    )
                # labels for each point will show if extents are not shown
                # or if they are, 00Z entry-indication will be shown
                # or if it is a landfall entry
                if kw.get("extents", False) is False \
                or entry.hour == 0 \
                or entry.record_identifier == "L":
                    ax.annotate(
                        "  {}{:{YMD}{HM}Z}  ".format(
                            "    " if entry.record_identifier == "L" else "",
                            entry.time,
                            YMD = "%m-%d "
                                if (entry.hour, entry.minute) == (0,0)
                                else "",
                            HM = "%H%M" if entry.minute != 0 else "%H"
                        ),
                        (entry.lon, entry.lat),
                        fontsize = 7
                            if (entry.hour, entry.minute) == (0,0)
                            or entry.record_identifier == "L"
                            else 6,
                        color = "black"
                            if (entry.hour, entry.minute) == (0,0)
                            or entry.record_identifier == "L"
                            else (0.3,0.3,0.3),
                        rotation = labelrot,
                        rotation_mode = "anchor",
                        horizontalalignment = halign,
                        verticalalignment = "center_baseline",
                        clip_on = True,
                    )

        # Reorder legend labels now as it currently is only categories
        legend_objects = sorted(
            legend_objects,
            key=lambda l: l.order_value
        )

        ax.grid(True, color=(0.3, 0.3, 0.3))
        ax.grid(True, which="minor", color=(0.6, 0.6, 0.6), linestyle=":")

        # set focus to the TC entries
        # This setting is persistent
        ax.set_xlim([
            min(en.lon for en in self.tc_entries) - kw.get("padding", 2),
            max(en.lon for en in self.tc_entries) + kw.get("padding", 2),
        ])
        ax.set_ylim([
            min(en.lat for en in self.tc_entries) - kw.get("padding", 2),
            max(en.lat for en in self.tc_entries) + kw.get("padding", 2),
        ])

        # Draw Map
        for postal, geo in _maps._polygons:
            for polygon in geo:
                ax.fill(
                    [lon for lon, lat in polygon],
                    [lat for lon, lat in polygon],
                    color = kw.get("land", "lightseagreen"),
                    # edgecolor = "black",
                    linewidth = 0.5,
                    zorder = 1,
                )
                ax.fill(
                    [lon for lon, lat in polygon],
                    [lat for lon, lat in polygon],
                    color = (0,0,0,0),
                    edgecolor = "black",
                    linewidth = 0.5,
                    zorder = 1.1,
                )
        for lake, geo in _maps._lakes:
            for polygon in geo:
                ax.fill(
                    [lon for lon, lat in polygon],
                    [lat for lon, lat in polygon],
                    color = kw.get("ocean", "lightblue"),
                    edgecolor = "black",
                    linewidth = 0.3,
                )

        # TESTING
        if kw.get("extents", False):
            for extent, extcolor, extlabel in [
                ("ts", "green", "TS-Force"),
                ("ts50", "limegreen", "50kt"),
                ("hu", "gold", "Hurricane-Force")
            ]:
                # legend
                if kw.get("legend", True):
                    legend_color_block = _patches.Rectangle(
                        (0,0),
                        1,
                        1,
                        facecolor = extcolor,
                        edgecolor = "black",
                        label = extlabel,
                        alpha = 0.8 if extent != "ts" else 0.6,
                    )
                    legend_objects.append(legend_color_block)

                for en in self.entry:
                    for quad in ["NE", "SE", "SW", "NW"]:
                        if getattr(en, "{}{}".format(extent,quad)) not in [0, None]:
                            h = _calculations.distance_from_coordinates(
                                en.lat,
                                en.lon,
                                getattr(en, "{}{}".format(extent,quad)),
                                quad[-1]
                            )
                            z = _calculations.distance_from_coordinates(
                                en.lat,
                                en.lon,
                                getattr(en, "{}{}".format(extent,quad)),
                                quad[0]
                            )

                            ell = Ellipsoid(
                                (en.lon, en.lat),
                                abs(h[1] - en.location[1]),
                                abs(z[0] - en.location[0]),
                            )

                            ax.fill(
                                [x for x,y in getattr(ell, "slice_{}".format(quad.lower()))],
                                [y for x,y in getattr(ell, "slice_{}".format(quad.lower()))],
                                color = extcolor,
                                linewidth = 0.5,
                                # edgecolor = "black" if extcolor != "green" else None,
                                edgecolor = None,
                                picker = False,
                                alpha = 0.8 if extent != "ts" else 0.6,
                            )

        # Legend
        legend = plt.legend(
            legend_objects,
            [line2dobj.get_label() for line2dobj in legend_objects],
            loc = "upper right",
        )
        legend.set_visible(kw.get("legend", True))
        legend.set_draggable(
            bool(kw.get("draggable"))
        )

        # Map credits
        plt.text(
            0.995,
            0.01,
            "Map Data: Made with Natural Earth",
            ha = "right",
            fontsize = "x-small",
            bbox = dict(
                boxstyle = "Square, pad=0.1",
                # edgecolor = (1,1,1,0),
                facecolor = (1,1,1,0.6),
                linewidth = 0,
            ),
            transform = ax.transAxes,
        )

        mplstyle.use("fast")

        # Save the figure only
        if kw.get("saveonly", False):
            # ax.set_adjustable("box")
            plt.savefig(
                "{}_{}_tracks".format(
                    self.atcfid,
                    self.name,
                ),
                dpi=kw.get("dpi", matplotlib.rcParams["figure.dpi"])
            )
            # This is necessary to "flush" to presence of figures as "savefig" does not
            # Other wise, subsequent calls would bring up the figure that was saved (but
            # not originally shown).
            orig_backend = matplotlib.rcParams["backend"]
            matplotlib.use("Agg")   # so the plt.show() command won't show anything
            plt.show() # this will flush the figure
            matplotlib.use(orig_backend) # change back to original backend
        # See the figure (the default)
        else:
            plt.show(
                block = kw.get("block", True)
            )
        # Turn back on xscale / yscale kb keys if not using jupyter notebook
        # if kw.get("backend") != "nbAgg":
            # matplotlib.rcParams['keymap.yscale'] = orig_keymap_yscale
            # matplotlib.rcParams['keymap.xscale'] = orig_keymap_xscale
