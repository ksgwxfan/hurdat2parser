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

import statistics
import math
import operator
import secrets

from . import _maps
from . import _calculations

import matplotlib
import matplotlib.style as mplstyle
import matplotlib.pyplot as plt
import matplotlib.ticker as _ticker
import matplotlib.dates as _dates
import matplotlib.figure as _figure
import matplotlib.patches as _patches

class Hurdat2:
    def draw_ellipse_quadrants(self, xy, width, height, angle=0, **kwargs):
        e = Ellipsoid(xy, width, height, angle, **kwargs)

        a = plt.axes(aspect="equal", adjustable="datalim")
        a.fill([x for x,y in e.slice_ne], [y for x,y in e.slice_ne], color="blue")
        a.fill([x for x,y in e.slice_se], [y for x,y in e.slice_se], color="red")
        a.fill([x for x,y in e.slice_sw], [y for x,y in e.slice_sw], color="green")
        a.fill([x for x,y in e.slice_nw], [y for x,y in e.slice_nw], color="yellow")
        a.autoscale()
        plt.show(block=False)

    def random(self, year1=None, year2=None, **kw):
        """
        *** ONLY positional keywords (year1 and year2) recognized right now ***

        Returns a random <TropicalCyclone> object from the database, optionally
        based upon various criteria.

        Required Keyword Arguments
        -------------------------
            year1 (None): the start year; defaults to beginning year of the
                database.
            year2 (None): the end year; defaults to the end of the database.

        Other criteria
        --------------
            * All other keyword arguments can be valid <TropicalCyclone>
            properties/attributes. Their values can be tuples of a stringified
            comparison operator and a value or just a value (the "==" operator
            will be implied)

            Examples:
            =========
                atl.random(saffir_simpson = 5) -> A TCyc where winds reached
                    category 5 strength
                atl.random(minmslp=("<=", 920), ace=(">=", 30)) -> minimum mslp
                    was less-than-or-equal to 920mb and ACE >= 30*10^-4
                atl.random(1967, duration_TC=(">=", 10)) -> a TCyc occurring no
                    sooner than 1967 that persisted for an accumulated 10+ days
                    as a designated tropical cyclone.
        """

        year1 = self.record_range[0] if year1 is None \
            or year1 < self.record_range[0] else year1
        year2 = self.record_range[1] if year2 is None \
            or year2 > self.record_range[1] else year2

        return secrets.choice([
            tcyc for tcyc in self.tc.values()
            if year1 <= tcyc.year <= year2
        ])

class Season:

    def track_map(self, **kw):
        fig = plt.figure(
            # figsize = (_w, _h),
            layout = "constrained",
        )
        figman = plt.get_current_fig_manager()
        # figman.set_window_title(
            # "{} - {} Tracks".format(
                # self.atcfid,
                # self.name
            # )
        # )
        rc = matplotlib.rcParams
        ax = plt.axes(
            facecolor = kw.get("ocean", "lightblue")
        )
        
        for tc in self.tc.values():
            ax.plot(
                [entry.lon for entry in tc.entry],
                [entry.lat for entry in tc.entry],
                color =  "hotpink" if _calculations.saffir_simpson_scale(tc.maxwind) == 5 else \
                         "purple" if _calculations.saffir_simpson_scale(tc.maxwind) == 4 else \
                         "red" if _calculations.saffir_simpson_scale(tc.maxwind) == 3 else \
                         "orange" if _calculations.saffir_simpson_scale(tc.maxwind) == 2 else \
                         "yellow" if _calculations.saffir_simpson_scale(tc.maxwind) == 1 else \
                         "green" if _calculations.saffir_simpson_scale(tc.maxwind) == 0 else \
                         "black",
            )
            ax.text(
                tc.entry[0].lon,
                tc.entry[0].lat,
                "{}{}".format(
                    tc.name if tc.name != "UNNAMED" else "",
                    "{}{}{}".format(
                        " (" if tc.name != "UNNAMED" else "",
                        tc.atcfid,
                        ")" if tc.name != "UNNAMED" else "",
                    )
                )
            )
        # Draw Map
        for postal, geo in _maps._polygons:
            for polygon in geo:
                ax.fill(
                    [lon for lon, lat in polygon],
                    [lat for lon, lat in polygon],
                    color = kw.get("land", "lightseagreen"),
                    edgecolor = "black",
                    linewidth = 0.5,
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

        ax.set_xlim(
            int(min(entry.lon for tc in self.tc.values() for entry in tc.entry))-5,
            int(max(entry.lon for tc in self.tc.values() for entry in tc.entry))+5,
        )
        ax.set_ylim(
            int(min(entry.lat for tc in self.tc.values() for entry in tc.entry))-5,
            int(max(entry.lat for tc in self.tc.values() for entry in tc.entry))+5,
        )

        plt.show()

    @property
    def wind_volume_TSstrength(self):
        """
        Returns the seasonal aggregated tropical storm-strength wind volume, an
        integration of areal tropical-storm wind extent over distance.

        Units are nmi^3.

        README.md write-up:   - `wind_volume_<SUFFIX>`
    - Wind Volumes: integrated areal-extents over distances. The goal of including these variables are to complement energy indices through representing wind-field areal expanse.
	- `<SUFFIX>` can be `TSstrength`, `TS`, `TS50strength`, `TS50`, `HUstrength`, or `HU`.
	- Of note, quadrant-based wind-field extents have only been recorded in the atlantic and pacific Hurdat2 databases since 2004. So this variable will have no use for prior years to that time.
        attributes/methods table entry: `wind_volume_<SUFFIX>`<br />*\*&lt;SUFFIX&gt; can be TSstrength, TS, TS50strength, TS50, HUstrength, or HU.* | An integration of wind-field expanse over distance | `atl[2019,13].wind_volume_HU`
        """
        return sum(tcyc.wind_volume_TSstrength for tcyc in self.tc.values())

    @property
    def wind_volume_TS(self):
        """
        Returns the seasonal aggregated tropical storm wind volume, an
        integration of areal tropical-storm wind extent over distance while the
        storm acquired the objective designation of at-least Tropical Storm
        (SS, TS, HU).

        Units are nmi^3.
        """
        return sum(tcyc.wind_volume_TS for tcyc in self.tc.values())

    @property
    def wind_volume_TS50strength(self):
        """
        Returns the seasonal aggregated gale-force wind volume, an integration
        of areal gale-force wind extent (>= 50kts) over distance.

        Units are nmi^3.
        """
        return sum(tcyc.wind_volume_TS50strength for tcyc in self.tc.values())

    @property
    def wind_volume_TS50(self):
        """
        Returns the seasonal aggregated gale-force wind volume, an integration
        of areal gale-force wind extent (>= 50kts) over distance, while the
        storm acquired the objective designation of at-least Tropical Storm
        (SS, TS, HU).

        Units are nmi^3
        """
        return sum(tcyc.wind_volume_TS50 for tcyc in self.tc.values())


    @property
    def wind_volume_HUstrength(self):
        """
        Returns the seasonal aggregated hurricane-strength wind volume, an
        integration of areal hurricane wind extent over distance.

        Units are nmi^3.
        """
        return sum(tcyc.wind_volume_HUstrength for tcyc in self.tc.values())

    @property
    def wind_volume_HU(self):
        """
        Returns the seasonal aggregated hurricane wind volume, an integration
        of areal hurricane wind extent over distance, while the storm acquired
        the objective designation of Hurricane (HU).

        Units are nmi^3.
        """
        return sum(tcyc.wind_volume_HU for tcyc in self.tc.values())

class TropicalCyclone:

    def stats_graph(self):
        fig = plt.figure(
            layout = "constrained",
        )

        ax = plt.axes(
        
        )
        ax2 = ax.twinx(
        
        )
        self._hd2.ax = ax
        self._hd2.ax2 = ax2
        # Primary
        ax.plot_date(
            [entry.entrytime for entry in self.entry],
            [entry.wind for entry in self.entry],
            "-",
            color = "red",
        )
        ax.xaxis.set_major_locator(_dates.DayLocator())
        ax.tick_params("x", labelrotation=90)
        ax.yaxis.set_major_locator(
            _ticker.MaxNLocator(
                nbins = 11,
                steps = [5,10],
                integer = True,
                min_n_ticks = 5
            )
        )
        ax.set_xlabel("Date")
        ax.set_ylabel("Max Wind")
        # Secondary
        ax2.plot_date(
            [entry.entrytime for entry in self.entry],
            [
                entry.mslp if entry.mslp is not None else 1013
                for entry in self.entry
            ],
            "--",
            color = "blue",
        )
        ax2.set_ylabel("MSLP (hPa)")
        # ax2.yaxis.set_major_locator(
            # _ticker.MaxNLocator(
                # nbins = 11,
                # steps = [5,10],
                # integer = True,
                # min_n_ticks = 5
            # )
        # )
        # 917.5 
        # Make graph even
        ax.set_ylim(
            math.floor(ax.get_ylim()[0]) - math.floor(ax.get_ylim()[0]) % 10,
            math.ceil(ax.get_ylim()[1]) + math.ceil(ax.get_ylim()[1]) % 10
        )
        # ax2.set_ylim(bottom=math.floor(ax2.get_ylim()[0]) - math.floor(ax2.get_ylim()[0]) % 10)
        ax2.set_ylim(
            math.floor(ax2.get_ylim()[0]) - math.floor(ax2.get_ylim()[0]) % 10,
            math.ceil(ax2.get_ylim()[1]) + math.ceil(ax2.get_ylim()[1]) % 10
        )
        while operator.sub(*(list(reversed(ax2.get_ylim())))) % len(ax.get_yticks()) != 0:
            if (ax2.get_ylim()[1]-ax2.get_ylim()[0]) % 10 != 0:
                ax2.set_ylim(bottom=ax2.get_ylim()[0] - 1)
            else:
                ax2.set_ylim(top=ax2.get_ylim()[1] + 1)
        ax2.yaxis.set_major_locator(
            _ticker.LinearLocator(
                len(ax.get_yticks())
            )
        )

        ax.grid(True)
        ax2.grid(True)
        plt.show(block=False)

    @property
    def wind_volume_TSstrength(self):
        """
        Returns the tropical storm-strength wind volume, an integration of
        areal tropical-storm wind extent over distance. Resultant units of
        integration are nmi^3, hence the variable name.

        *Important Note: As recorded wind-extents aren't dependent on tropical-
        cyclone status, this variable is also non-discriminatory of status. For
        a status-based wind-volume, use one of the following suffixes: TS,
        TS50, or HU.
        """
        return sum(
            1 / 2 * (en.areal_extent_TS + en.previous_entry.areal_extent_TS)
            * haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
        )

    @property
    def wind_volume_TS(self):
        """
        Returns the tropical storm wind volume, an integration of areal
        tropical-storm wind extent over distance while the storm acquired the
        objective designation of at-least Tropical Storm (SS, TS, HU).
        Resultant units of integration are nmi^3, hence the variable name.
        """
        return sum(
            1 / 2 * (en.areal_extent_TS + en.previous_entry.areal_extent_TS)
            * haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
            and en.previous_entry.status in ("SS", "TS", "HU")
        )

    @property
    def wind_volume_TS50strength(self):
        """
        Returns the gale-force-strength wind volume, an integration of areal
        gale-force wind extent (>=50kts) over distance. Resultant units of
        integration are nmi^3, hence the variable name.

        *Important Note: As recorded wind-extents aren't dependent on tropical-
        cyclone status, this variable is also non-discriminatory of status. For
        a status-based wind-volume, use one of the following suffixes: TS,
        TS50, or HU.
        """
        return sum(
            1 / 2 * (en.areal_extent_TS50 + en.previous_entry.areal_extent_TS50)
            * haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
        )

    @property
    def wind_volume_TS50(self):
        """
        Returns the gale-force tropical storm wind volume, an integration of
        areal tropical-storm wind extent over distance while the storm acquired
        the objective designation of at-least Tropical Storm (SS, TS, HU).
        Resultant units of integration are nmi^3, hence the variable name.
        """
        return sum(
            1 / 2 * (en.areal_extent_TS50 + en.previous_entry.areal_extent_TS50)
            * haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
            and en.previous_entry.status in ("SS", "TS", "HU")
        )

    @property
    def wind_volume_HUstrength(self):
        """
        Returns the hurricane-strength wind volume, an integration of areal
        hurricane wind extent over distance. Resultant units of integration are
        nmi^3, hence the variable name.

        *Important Note: As recorded wind-extents aren't dependent on tropical-
        cyclone status, this variable is also non-discriminatory of status. For
        a status-based wind-volume, use one of the following suffixes: TS,
        TS50, or HU.
        """
        return sum(
            1 / 2 * (en.areal_extent_HU + en.previous_entry.areal_extent_HU)
            * haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
        )


    @property
    def wind_volume_HU(self):
        """
        Returns the hurricane wind volume, an integration of areal hurricane
        wind extent over distance while the storm acquired the objective
        designation of Hurricane (HU). Resultant units of integration are
        nmi^3, hence the variable name.
        """
        return sum(
            1 / 2 * (en.areal_extent_HU + en.previous_entry.areal_extent_HU)
            * haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
            and en.previous_entry.status == "HU"
        )

    def areal_extent_graph(self):
        fig = plt.figure(
            # figsize = (_w, _h),
            layout = "constrained",
        )
        # tropical storm extent
        plt.fill_between(
            [
                en.track_distance
                for en in self.entry
                if any(
                    direction is not None
                    for direction in en.extent_TS
                )
            ],
            [
                en.areal_extent_TS
                for en in self.entry
                if any(
                    direction is not None
                    for direction in en.extent_TS
                )
            ],
            color = "green",
        )
        # ts extent - outline
        # plt.plot(
            # [
                # en.track_distance
                # for en in self.entry
                # if any(
                    # direction is not None
                    # for direction in en.extent_TS
                # )
            # ],
            # [
                # en.areal_extent_TS
                # for en in self.entry
                # if any(
                    # direction is not None
                    # for direction in en.extent_TS
                # )
            # ],
            # color="black",
            # linewidth=1,
        # )

        # gale extent (ts50)
        plt.fill_between(
            [en.track_distance for en in self.entry],
            [en.areal_extent_TS50 for en in self.entry],
            color = (0, 1, 0.5),
        )

        # hu extent
        plt.fill_between(
            [en.track_distance for en in self.entry],
            [en.areal_extent_HU for en in self.entry],
            color = (1, 1, 0),
        )

        plt.ylabel("Area (sq. nautical miles)")
        plt.xlabel("Track Distance (nautical miles)")
        plt.grid(True, "both", color="black", linestyle=":")
        plt.show(block=False)

class TCRecordEntry:
    pass

class blah:
    pass