import statistics
import math
import operator

from . import _maps
from . import _calculations

try:
    import matplotlib
    import matplotlib.style as mplstyle
    import matplotlib.pyplot as plt
    import matplotlib.ticker as _ticker
    import matplotlib.dates as _dates
    import matplotlib.figure as _figure
    import matplotlib.patches as _patches
except Exception as e:
    print("* Error attempting to import matplotlib: {}".format(e))

class Hurdat2:
    pass

class Season:

    def track_map(self, **kw):
        fig = plt.figure(
            # figsize = (_w, _h),
            constrained_layout = True,
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
        # Draw Map
        for atlas in [
            _maps.all_land,
            _maps.usa,
            _maps.centam,
            _maps.islands,
        ]:
            for country in atlas:
                for polygon in country[1:]:
                    ax.fill(
                        [lon for lon, lat in polygon],
                        [lat for lon, lat in polygon],
                        color = kw.get("land", "lightseagreen"),
                        edgecolor = "black",
                        linewidth = 0.5,
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
            constrained_layout = True,
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
            constrained_layout = True,
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