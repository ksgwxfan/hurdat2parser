import operator
import json
import shapefile
import geojson
import statistics
import math
import os
import csv
import itertools
import collections

from . import _calculations
from . import _maps

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as _ticker
import matplotlib.dates as _dates
import matplotlib.figure as _figure
import matplotlib.patches as _patches

class Hurdat2Reports:

    def output_climo(self, climo_len=30):
        """Output a csv of stats from all climatological eras from the record
        of specifiable era-spans. Temporal separations of 1-year increments
        will be used.

        Default Arguments:
            climo_len (30): The length of time in years each climate era will
                be assessed.
        """
        class LAMBDA_CLASS:
            def __init__(self, **kw):
                self.__dict__ = kw

        ofn = "{}_HURDAT2_{}-yr_climatology.csv".format(
            "ATL" if list(self.tc.keys())[0][:2] == "AL" else "PAC",
            climo_len
        )
        
        if os.path.exists(ofn):
            choice = input(
                "* A file named '{}' already exists.".format(ofn) \
                + "Continue? (y/n): "
            )
            if choice.lower()[0] != "y": return None
        print("** PLEASE WAIT; THIS MAY TAKE A MOMENT **")
        # climo = self.rank_climo(10,"tracks",climatology=climo_len,increment=1,op=True)

        # ---------------------
        Era = collections.namedtuple(
            "Era",
            [
                "era", "tracks", "landfalls", "landfall_TC", "landfall_TD",
                "landfall_TS", "landfall_HU", "landfall_MHU", "TSreach",
                "TSonly", "HUreach", "HUonly", "MHUreach", "cat45reach",
                "cat5reach", "track_distance", "track_distance_TC",
                "track_distance_TS", "track_distance_HU", "track_distance_MHU",
                "ACE", "HDP", "MHDP"
            ]
        )

        year1 = self.record_range[0]
        year2 = self.record_range[1]
        climo = {}
        for yr1, yr2 in [(y, y+climo_len-1) \
                for y in range(year1, year2+1) \
                if year1 <= y <= year2 \
                and year1 <= y+climo_len-1 <= year2]:
            climo[yr1, yr2] = Era(
                (yr1, yr2),
                sum(self.season[s].tracks for s in range(yr1, yr2+1)),
                sum(self.season[s].landfalls for s in range(yr1, yr2+1)),
                sum(self.season[s].landfall_TC for s in range(yr1, yr2+1)),
                sum(self.season[s].landfall_TD for s in range(yr1, yr2+1)),
                sum(self.season[s].landfall_TS for s in range(yr1, yr2+1)),
                sum(self.season[s].landfall_HU for s in range(yr1, yr2+1)),
                sum(self.season[s].landfall_MHU for s in range(yr1, yr2+1)),
                sum(self.season[s].TSreach for s in range(yr1, yr2+1)),
                sum(self.season[s].TSonly for s in range(yr1, yr2+1)),
                sum(self.season[s].HUreach for s in range(yr1, yr2+1)),
                sum(self.season[s].HUonly for s in range(yr1, yr2+1)),
                sum(self.season[s].MHUreach for s in range(yr1, yr2+1)),
                sum(self.season[s].cat45reach for s in range(yr1, yr2+1)),
                sum(self.season[s].cat5reach for s in range(yr1, yr2+1)),
                sum(self.season[s].track_distance for s in range(yr1, yr2+1)),
                sum(self.season[s].track_distance_TC for s in range(yr1, yr2+1)),
                sum(self.season[s].track_distance_TS for s in range(yr1, yr2+1)),
                sum(self.season[s].track_distance_HU for s in range(yr1, yr2+1)),
                sum(self.season[s].track_distance_MHU for s in range(yr1, yr2+1)),
                sum(self.season[s].ACE for s in range(yr1, yr2+1)),
                sum(self.season[s].HDP for s in range(yr1, yr2+1)),
                sum(self.season[s].MHDP for s in range(yr1, yr2+1))
            )

        # --------------------------------

        with open(ofn, "w", newline="") as w:
            out = csv.writer(w)
            out.writerow([
                "Climatology", "TC Qty", "Trk Dist", "Landfalls (Acc.)",
                "TC Landfall", "TS Landfall", "HU Landfall", "MHU Landfall",
                "TC Trk Dist", "TS", "ACE", "TS Trk Dist", "TS-Excl", "HU",
                "HDP", "HU Trk Dist", "HU-1and2", "MHU", "Cat 4 and 5 Qty",
                "Cat 5 Qty", "MHDP", "MHU Trk Dist"
            ])
            for clmt in climo.values():
                out.writerow([
                    "{}-{}".format(
                        clmt.era[0],
                        clmt.era[1]
                    ),
                    clmt.tracks,
                    clmt.track_distance,
                    clmt.landfalls,
                    clmt.landfall_TC,
                    clmt.landfall_TS,
                    clmt.landfall_HU,
                    clmt.landfall_MHU,
                    clmt.track_distance_TC,
                    clmt.TSreach,
                    clmt.ACE,
                    clmt.track_distance_TS,
                    clmt.TSonly,
                    clmt.HUreach,
                    clmt.HDP,
                    clmt.track_distance_HU,
                    clmt.HUonly,
                    clmt.MHUreach,
                    clmt.cat45reach,
                    clmt.cat5reach,
                    clmt.MHDP,
                    clmt.track_distance_MHU
                ])

    def output_seasons_csv(self):
        """Output a csv of season-based stats from the record. In general, this
        method really only has need to be called once. The primary exception to
        this suggestion would only occur upon official annual release of the
        HURDAT2 record.
        """
        ofn = "{}_HURDAT2_seasons_summary.csv".format(
            "ATL" if list(self.tc.keys())[0][:2] == "AL" else "PAC"
        )
        with open(ofn, "w", newline="") as w:
            out = csv.writer(w)
            out.writerow([
                "Year", "TC Qty", "Trk Dist", "Landfalls (Acc.)",
                "TC Landfall", "TS Landfall", "HU Landfall", "MHU Landfall",
                "TC Trk Dist", "TS", "ACE", "TS Trk Dist", "TS-Excl", "HU",
                "HDP", "HU Trk Dist", "HU-1and2", "MHU", "MHDP", "MHU Trk Dist"
            ])
            for y in [YR[1] for YR in self.season.items()]:
                out.writerow([
                    y.year,
                    y.tracks,
                    y.track_distance,
                    y.landfalls,
                    y.landfall_TC,
                    y.landfall_TS,
                    y.landfall_HU,
                    y.landfall_MHU,
                    y.track_distance_TC,
                    y.TSreach,
                    y.ACE,
                    y.track_distance_TS,
                    y.TSonly,
                    y.HUreach,
                    y.HDP,
                    y.track_distance_HU,
                    y.HUonly,
                    y.MHUreach,
                    y.MHDP,
                    y.track_distance_MHU
                ])

    def output_storms_csv(self):
        """Output a csv of individual storm-based stats from the record. In
        general, this method really only has need to be called once. The
        primary exception to this suggestion would only occur upon official
        annual release of the HURDAT2 record.
        """
        ofn = "{}_HURDAT2_storms_summary.csv".format(
            "ATL" if list(self.tc.keys())[0][:2] == "AL" else "PAC"
        )
        with open(ofn, "w", newline="") as w:
            out = csv.writer(w)
            out.writerow([
                "Year", "ATCF Num", "ATCF ID", "Name", "Start Time",
                "End Time", "HD2 Entries", "Min MSLP", "Max Wind", "Trk Dist",
                "(Qty) Landfalls", "TD Landfall", "TS Landfall", "HU Landfall", 
                "MHU Landfall", "Statuses", "TC Trk Dist", "TS Trk Dist",
                "ACE", "TS Date", "HU Trk Dist", "HDP", "HU Date",
                "MHU Trk Dist", "MHDP", "MHU Date"
            ])
            for TC in [tc[1] for tc in self.tc.items()]:
                out.writerow([
                    TC.year,
                    int(TC.atcfid[2:4]),
                    TC.atcfid,
                    TC.name,
                    TC.entry[0].entrytime,
                    TC.entry[-1].entrytime,
                    len(TC.entry),
                    TC.minmslp,
                    TC.maxwind if TC.maxwind > 0 else None,
                    TC.track_distance,
                    TC.landfalls,
                    1 if TC.landfall_TD is True else 0,
                    1 if TC.landfall_TS is True else 0,
                    1 if TC.landfall_HU is True else 0,
                    1 if TC.landfall_MHU is True else 0,
                    ", ".join(TC.statuses_reached),
                    TC.track_distance_TC,
                    TC.track_distance_TS,
                    TC.ACE,
                    min([en.entrytime for en in TC.entry if en.status in ("SS","TS","HU")], default=None),
                    TC.track_distance_HU,
                    TC.HDP,
                    min([en.entrytime for en in TC.entry if en.status in ("HU")], default=None),
                    TC.track_distance_MHU,
                    TC.MHDP,
                    min([en.entrytime for en in TC.entry if en.status in ("HU") and en.wind >= 96], default=None)
                ])

    def climograph(self, attr, climatology=30, increment=5, **kw):
        """zxcv
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
                self.basin
            )
        )
        fig.suptitle(
            "{} {} Climatological Tendency\n{}".format(
                attr,
                "{}yr / {}yr Incremented".format(
                    climatology,
                    increment
                ),
                self.basin
            )
        )
        ax = plt.axes(
            
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

        self.rc = matplotlib.rcParams
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
            "ATL" if list(self.tc.keys())[0][:2] == "AL" else "PAC"
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
            "ATL" if list(self.tc.keys())[0][:2] == "AL" else "PAC"
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
            "ATL" if list(self.tc.keys())[0][:2] == "AL" else "PAC"
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
            "ATL" if list(self.tc.keys())[0][:2] == "AL" else "PAC"
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
            markersize (float): the entry-marker size; defaults to 2.
        """
        _w, _h = _figure.figaspect(kw.get("aspect_ratio", 3/4))
        fig = plt.figure(
            figsize = (_w, _h),
            constrained_layout = True,
        )
        plt.get_current_fig_manager().set_window_title(
            "{} - {} Tracks".format(
                self.atcfid,
                self.name
            )
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
                ax.plot(
                    [entry.lon, self.entry[indx + 1].lon],
                    [entry.lat, self.entry[indx +1].lat],
                    "-" if entry.status in ["SD", "TD", "SS", "TS", "HU"] else ":",
                    color = "hotpink" if entry.saffir_simpson == 5 else \
                         ("purple" if entry.saffir_simpson == 4 else \
                         ("red" if entry.saffir_simpson == 3 else \
                         ("orange" if entry.saffir_simpson == 2 else \
                         ("yellow" if entry.saffir_simpson == 1 else \
                         ("green" if entry.saffir_simpson == 0 else "black"))))),
                    linewidth = kw.get("linewidth", rc["lines.linewidth"]),
                )
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

            # Status points
            ax.plot(
                entry.lon,
                entry.lat,
                "o",
                color = "black",
                markersize = kw.get("markersize", 2),
            )
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
        # print(ax.get_ylim(), ax.get_xlim())

        # Set view-limits to be equal
        maxaxis = ax.xaxis \
            if abs(operator.sub(*ax.get_xlim())) >= \
            abs(operator.sub(*ax.get_ylim())) else ax.yaxis
        maxaxis_diff = abs(operator.sub(*maxaxis.get_view_interval())) * (
            kw.get("aspect_ratio", 3/4) \
            if ax.xaxis == maxaxis \
            else (1 / kw.get("aspect_ratio", 3/4))
        )
        maxaxis_interval = maxaxis.get_view_interval()

        minaxis = ax.xaxis \
            if abs(operator.sub(*ax.get_xlim())) < \
            abs(operator.sub(*ax.get_ylim())) else ax.yaxis
        # minaxis_diff = abs(operator.sub(*minaxis.get_view_interval()))
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
        # for file in [
            # "countrydb_all_land_minus_americas.json",
            # "countrydb_centamerica.json",
            # "countrydb_usafull.json",
            # "countrydb_islands.json"
        # ]:
            # with open(file) as r:
                # countrydata = json.loads(r.read())
            # for country in countrydata:
                # for polygon in country[1:]:
                    # ax.fill(
                        # [lon for lon, lat in polygon],
                        # [lat for lon, lat in polygon],
                        # color = kw.get("land", "lightseagreen"),
                        # edgecolor = "black",
                        # linewidth = 0.5,
                    # )

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

        plt.show(block=False)

def ___blah():
    pass