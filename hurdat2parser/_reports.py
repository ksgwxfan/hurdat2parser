import operator
import json
import statistics
import math
import os
import re
import csv
import itertools
import collections

try:
    import shapefile
except:
    print("* Error attempting to import shapefile")

try:
    import geojson
except:
    print("* Error attempting to import geojson")

from . import _calculations
from . import _maps

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
    def __init__(self, **kw):
        self.__dict__.update(**kw)

class Hurdat2Reports:

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
            tight_layout = True,
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
        """EXPERIMENTAL! Return a map of the tropical-cyclone's track (via 
        matplotlib). Each track will be color-coded based on associated wind-
        speed and storm-status. Colors are controlled by saffir-simpson scale 
        equivalent winds. When a storm in not objectively designated as a 
        tropical-cyclone, its track will be represented as a dotted (rather
        than solid) line.

        * Basins that traverse 180 Longitude have not been accounted for in
        preparation of the maps.

        * Map feature coordinate data from Natural Earth (naturalearthdata.com)

        Keyword Arguments:
            aspect_ratio (float): the desired aspect-ratio of the figure;
                defaults to 0.75 (4:3, the matplotlib default).
            ocean (matplotlib-compatible color): the requested color for the
                ocean (the background); defaults to 'lightblue'.
            land (matplotlib-compatible color): the requested color for land-
                masses; defaults to 'lightseagreen'.
            labels (bool): toggle for temporal labels for entries; defaults to
                True.
            linewidth (float): the line-width of the track; defaults to 1.5.
            markersize (float): the entry-marker size; defaults to 3.
            legend (bool): whether or not you want to display a legend (default
                is True).
        """
        matplotlib.rcParams['path.simplify_threshold'] = 1
        # _w, _h = _figure.figaspect(kw.get("aspect_ratio", 3/4))
        fig = plt.figure(
            # figsize = (_w, _h),
            constrained_layout = True,
        )
        figman = plt.get_current_fig_manager()
        figman.set_window_title(
            "{} - {} Tracks".format(
                self.atcfid,
                self.name
            )
        )
        MIN_SCREEN_DIM = "height" \
            if figman.window.winfo_screenheight() < figman.window.winfo_screenwidth() \
            else "width"

        # set figure dimensions with a 4:3 aspect ratio
        if MIN_SCREEN_DIM == "height":
            fig.set_figheight(
                figman.window.winfo_screenmmheight() / 25.4 - 2
            )
            fig.set_figwidth(
                fig.get_figheight() * 1 / kw.get("aspect_ratio", 3/4)
            )
        else:
            fig.set_figwidth(
                figman.window.winfo_screenmmwidth() / 25.4 - 2
            )
            fig.set_figheight(
                fig.get_figwidth() * kw.get("aspect_ratio", 3/4)
            )

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


        rc = matplotlib.rcParams
        ax = plt.axes(
            facecolor = kw.get("ocean", "lightblue")
        )
        self._hd2.fig = fig

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
            if entry != self.entry[-1]:
                labelangle = math.degrees(
                    math.atan2(
                        self.entry[indx+1].lat - entry.lat,
                        self.entry[indx+1].lon - entry.lon
                    )
                )
                # labelrot = 45 if 150 <= labelangle <= 180 else \
                    # (-45 if -180 <= labelangle <= -150 else 0)
                labelrot = 45 \
                    if (135 <= labelangle <= 180 or labelangle <= -170) else \
                       (-45 if -170 < labelangle <= -135 else labelangle - 90)
                halign = "left" if 0 <= labelrot <= 90 else "right"
                # print(entry.time, labelangle, labelrot, halign)
                line2dobj_list = ax.plot(
                    [entry.lon, self.entry[indx + 1].lon],
                    [entry.lat, self.entry[indx +1].lat],
                    "-" if entry.is_TC else ":",
                    color = "hotpink" if entry.saffir_simpson == 5 else \
                         "purple" if entry.saffir_simpson == 4 else \
                         "red" if entry.saffir_simpson == 3 else \
                         "orange" if entry.saffir_simpson == 2 else \
                         "yellow" if entry.saffir_simpson == 1 else \
                         "green" if entry.saffir_simpson == 0 else \
                         "black",
                    marker = ".",
                    markersize = kw.get("markersize", 3),
                    markeredgecolor = "black",
                    markerfacecolor = "black",
                    linewidth = kw.get("linewidth", rc["lines.linewidth"]),
                    label = "Category {}".format(entry.saffir_simpson) \
                        if entry.saffir_simpson > 0 and entry.status == "HU" else \
                        "Tropical Storm" \
                        if entry.saffir_simpson == 0 and entry.status in ["SS", "TS"] else \
                        "Tropical Depression" \
                        if entry.saffir_simpson < 0 and entry.status in ["SD", "TD"] else \
                        "Non-Tropical Cyclone",
                )
                # Add a label to the legend if one doesn't exist already
                if any(line2dobj_list[0].get_label() == line2dobj.get_label() for line2dobj in legend_objects) is False:
                    legend_objects.extend(line2dobj_list)
            # from ._calculations import distance_from_coordinates
            # TS Radius
            # w = _patches.Wedge(
                # entry.location_reversed,
                
            # )
            # ax.fill(
                # [
                    # entry.longitude,
                    # distance_from_coordinates(*entry.location, entry.tsNE, "N")[1],
                    # distance_from_coordinates(*entry.location, entry.tsNE, "E")[1],
                # ],
                # [
                    # entry.latitude,
                    # distance_from_coordinates(*entry.location, entry.tsNE, "N")[0],
                    # distance_from_coordinates(*entry.location, entry.tsNE, "E")[0],
                # ],
                # zorder=10
            # )

            if kw.get("labels", True):
                if entry.record_identifier == "L":
                    ax.annotate(
                        "L     ",
                        (entry.lon, entry.lat),
                        fontsize = 10,
                        fontweight = "bold",
                        rotation = labelrot,
                        horizontalalignment = halign
                    )
                    ax.annotate(
                        "     {:{YMD}{HM}Z}".format(
                            entry.time,
                            YMD = "%y/%m%d " \
                                if (entry.hour, entry.minute) == (0,0) else "",
                            HM = "%H%M" if entry.minute != 0 else "%H"
                        ),
                        (entry.lon, entry.lat),
                        fontsize = 6,
                        rotation = labelrot,
                        horizontalalignment = halign
                    )
                else:
                    ax.annotate(
                        " {:{YMD}%HZ}".format(
                            entry.time,
                            YMD = "%y/%m%d " \
                                if (entry.hour, entry.minute) == (0,0) else ""
                        ),
                        (entry.lon, entry.lat),
                        fontsize = 6,
                        color = "black" if (entry.hour, entry.minute) == (0,0) \
                            else (0.5,0.5,0.5),
                        rotation = labelrot,
                        horizontalalignment = halign
                    )
        ax.grid(True, color=(0.3, 0.3, 0.3))
        ax.grid(True, which="minor", color=(0.6, 0.6, 0.6), linestyle=":")

        # set focus to the TC entries
        ax.set_xlim([
            min(en.lon for en in self.tc_entries) - 2,
            max(en.lon for en in self.tc_entries) + 2,
        ])
        ax.set_ylim([
            min(en.lat for en in self.tc_entries) - 2,
            max(en.lat for en in self.tc_entries) + 2,
        ])

        # Set view-limits to be equal.
        # *** THIS NEEDS TO BE DONE before maps are added. Once maps are added,
        #     it places new limits. So to focus the end-result on the track,
        #     the points are needed to be determined before any map is placed
        # maxaxis == xaxis if longitudinal span >= latitudinal span, else yaxis

        maxaxis = ax.xaxis \
            if abs(operator.sub(*ax.get_xlim())) >= \
            abs(operator.sub(*ax.get_ylim())) else ax.yaxis
        # multiply the span * the aspect-ratio
        maxaxis_diff = abs(operator.sub(*maxaxis.get_view_interval())) * (
            kw.get("aspect_ratio", 3/4) \
            if ax.xaxis == maxaxis \
            else (1 / kw.get("aspect_ratio", 3/4))
        )
        # the final maxaxis interval
        maxaxis_interval = maxaxis.get_view_interval()

        # minaxis == xaxis if longitudinal span < latitudinal span, else yaxis
        minaxis = ax.xaxis \
            if abs(operator.sub(*ax.get_xlim())) < \
            abs(operator.sub(*ax.get_ylim())) else ax.yaxis
        # minaxis_diff = abs(operator.sub(*minaxis.get_view_interval()))

        # the final minaxis interval
        # from the mid-point of the minaxis, add(subtract) half of the maxaxis_diff
        # this will ensure "equidistant" nice layout of map
        minaxis_interval = [
            (statistics.mean(minaxis.get_view_interval()) + maxaxis_diff / 2),
            (statistics.mean(minaxis.get_view_interval()) - maxaxis_diff / 2)
        ]

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

        # Reset Intervals to the TC Track
        maxaxis.set_view_interval(
            min(maxaxis_interval),
            max(maxaxis_interval),
            ignore=True
        )
        minaxis.set_view_interval(
            min(minaxis_interval),
            max(minaxis_interval),
            ignore=True
        )

        # Legend
        if kw.get("legend", True):
            legend = plt.legend(
                legend_objects,
                [line2dobj.get_label() for line2dobj in legend_objects],
                loc = "upper right",
            )
            legend.set_draggable(True)
        mplstyle.use("fast")
        plt.show(block=False)
