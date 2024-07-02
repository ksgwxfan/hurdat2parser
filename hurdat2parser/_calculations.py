"""
hurdat2parser 2.2.3.1, Copyright (c) 2023, Kyle S. Gentry

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
import textwrap
import datetime
import calendar
import collections

blah = dict(
    tracks = 0, landfalls=0, landfall_TC = 0, landfall_TD = 0,
    landfall_TS = 0, landfall_HU = 0, landfall_MHU = 0,
    TSreach = 0, HUreach = 0, MHUreach = 0, track_distance = 0,
    track_distance_TC = 0, track_distance_TS = 0,
    track_distance_HU = 0, track_distance_MHU = 0,
    ACE = 0, HDP = 0, MHDP = 0, cat45reach = 0, cat5reach = 0
)

class Hurdat2Calculations:

    def rank_seasons(self, quantity, stattr, year1=None, year2=None, descending=True, **kw):
        """Rank and compare full tropical cyclone seasons to one another.

        Required Arguments:
            quantity: how long of a list of ranks do you want; an integer.
            stattr: the storm attribute that you'd like to rank seasons by.
            
                * Storm Attributes: 
                    "tracks", "landfall_TC", "TSreach", "HUreach", "MHUreach",
                    "track_distance_TC", "ACE", "track_distance_TS", "HDP",
                    "track_distance_HU", "MHDP", "track_distance_MHU"

                * Note: Though attributes "track_distance", "landfalls", 
                    "landfall_TD", "landfall_TS", "landfall_HU",
                    "landfall_MHU", "TDonly", "TSonly", "HUonly", "cat45reach",
                    and "cat5reach" are valid storm attributes to rank by,
                    their quantities will not be visible in the ranking output.

        Default Arguments:
            year1 (None): begin year. If included, the indicated year will
                represent the low-end of years to assess. In the absence of
                the end-year, all years from this begin year to the end of the
                record-range will be used in ranking.
            year2 (None): end year. If included, the indicated year will
                represent the upper-end of years to assess. In the absence of
                the begin-year, all years from the start of the record-range
                to this indicated year will be used in ranking.
            descending (True): bool to indicate sorting seasons in descending
                (higher-to-lower) or not. The default of True implies seasons
                will be ranked from higher-to-lower.

        Examples:
        ---------
        <Hurdat2>.rank_seasons(10,"ACE"): Retrieve a report of tropical
                cyclone seasons sorted by the top-10 Accumulated Cyclone
                Energy values.
        <Hurdat2>.rank_seasons(15,"HDP",1967): Retrieve a report of tropical
                cyclone seasons sorted by the top-15 Hurricane Destruction
                Potential values occurring since 1967 (the beginning of the
                satellite era).
        <Hurdat2>.rank_seasons(5,"track_distance_TS",1951,2000,True):
                Retrieve a report of the bottom-5 seasons of distance
                traversed by, at-least, tropical storms, all between 1951 and
                2000.
        <Hurdat2>.rank_seasons(10,"HUreach",year2=2000): Retrieves a report 
                of the top-10 seasons with the most Hurricanes prior-to, and
                including the year 2000.
        """

        # --------------------
        year1 = abs(year1) \
            if type(year1) == int \
            and abs(year1) >= self.record_range[0] \
            else self.record_range[0]
        year2 = abs(year2) \
            if type(year2) == int \
            and abs(year2) <= self.record_range[1] \
            else self.record_range[1]

        year1, year2 = [
            min([year1, year2]),
            max([year1, year2])
        ]

        if len(range(year1, year2)) == 0:
            raise ValueError("The years given must be different!")

        # List seasons sorted by stattr
        sorted_seasons = sorted(
            [s for s in self.season.values() if year1 <= s.year <= year2],
            key=lambda czen: getattr(czen, stattr),
            reverse = descending
        )
        # Values sorted
        ranks = sorted(
            set([
                getattr(s, stattr) for s in sorted_seasons \
                    if descending is False \
                    or (getattr(s, stattr) > 0 and kw.get("info") is None) \
                    or kw.get("info") is not None
            ]),
            reverse = descending
        )[:quantity]

        # RETURN if _season_stats (via rank_seasons_thru) method called this method
        if kw.get("info", None) is not None:
            # insert years data if not included in original ranking
            if (year1 <= kw["info"] <= year2) is False:
                ranks = sorted(
                    ranks + [getattr(self.season[kw["info"]], stattr)],
                    reverse = descending
                )
            return {
                "seasonvalu": getattr(self.season[kw["info"]], stattr),
                "rank": ranks.index(getattr(self.season[kw["info"]], stattr)) + 1,
                "tied": len(["tie" for season in sorted_seasons if getattr(season, stattr) == getattr(self.season[kw["info"]], stattr)]) - 1,
                "outof": len(ranks)
            }
        # List that holds printed quantities
        printedqty = []
        
        print("")
        print("TOP {} SEASONS RANKED BY {}".format(
            len(ranks),
            stattr.upper()
        ).center(79))

        print("{}{}".format(
            str(self.basin()),
            ", {}-{}".format(year1, year2)
        ).center(79))
        print("-" * 79)

        print("{:4}  {:4}  {:^6}  {:^4}  {:^4}  {:^4} {:^3}  {:^7}  {:^25}".format(
            "","","","LAND","QTY","","","TC DIST",
            "STATUS-RELATED TRACK" if "track_distance" in stattr else "ENERGY INDICES"
        ))
        print("{:4}  {:4}  {:^6}  {:^4}  {:^4}  {:^4} {:^3}  {:^7}  {:^25}".format(
            "","","NUM OF","FALL","TRPC","QTY","QTY","TRAVRSD",
            "DISTANCES (in nmi)" if "track_distance" in stattr else "x10^4 kt^2"
        ))
        print("RANK  YEAR  {:^6}  {:^4}  {:^4}  {:^4} {:^3}  {:^7}  {:^7}  {:^7}  {:^7}".format(
            "TRACKS","TCs","STRM","HURR","MAJ","(nmi)",
            "TRPCSTM" if "track_distance" in stattr else "ACE",
            "HURRICN" if "track_distance" in stattr else "HDP",
            "MAJHURR" if "track_distance" in stattr else "MHDP"
        ))
        print("{:-^4}  {:-^4}  {:-^6}  {:-^4}  {:-^4}  {:-^4} {:-^3}  {:-^7}  {:-^7}  {:-^7}  {:-^7}".format(
            "","","","","","","","","","",""
        ))
        for season in sorted_seasons:
            try:
                current_rank = ranks.index(getattr(season, stattr)) + 1 \
                    if ranks.index(getattr(season, stattr)) + 1 \
                    not in printedqty else None
            except:
                break
            print("{:>3}{:1}  {:4}  {:^6}  {:^4}  {:^4}  {:^4} {:^3}  {:>7.1f}  {:>{ACELEN}f}  {:>{ACELEN}f}  {:>{ACELEN}f}".format(
                current_rank if current_rank is not None else "", 
                "." if current_rank is not None else "",
                season.year,
                season.tracks,
                season.landfall_TC,
                season.TSreach,
                season.HUreach,
                season.MHUreach,
                season.track_distance_TC,
                season.track_distance_TS if "track_distance" in stattr \
                    else season.ACE * math.pow(10,-4),
                season.track_distance_HU if "track_distance" in stattr \
                    else season.HDP * math.pow(10,-4),
                season.track_distance_MHU if "track_distance" in stattr \
                    else season.MHDP * math.pow(10,-4),
                ACELEN = 7.1 if "track_distance" in stattr else 7.3
            ))
            if current_rank is not None and current_rank not in printedqty:
                printedqty.append(current_rank)
        print("")

    def rank_seasons_thru(self, quantity, stattr, year1=None, year2=None, descending=True, **kw):
        """Rank and compare *partial* tropical cyclone seasons to one another.

        * Of note, if neither `start` or `thru` keywords are included, this
        function becomes a wrapper for <Hurdat2>.rank_seasons

        Required Arguments:
            quantity: how long of a list of ranks do you want; an integer.
            stattr: the storm attribute that you'd like to rank seasons by.
            
                * Storm Attributes: 
                    "tracks", "landfall_TC", "TSreach", "HUreach", "MHUreach",
                    "track_distance_TC", "ACE", "track_distance_TS", "HDP",
                    "track_distance_HU", "MHDP", "track_distance_MHU"

                * Note: Though attributes "track_distance", "landfalls", 
                    "landfall_TD", "landfall_TS", "landfall_HU",
                    "landfall_MHU", "TDonly", "TSonly", "HUonly", "cat45reach",
                    and "cat5reach" are valid storm attributes to rank by,
                    their quantities will not be visible in the ranking output.

        Default Arguments:
            year1 = None: begin year. If included, the indicated year will
                represent the low-end of years to assess. In the absence of
                the end-year, all years from this begin year to the end of the
                record-range will be used in ranking.
            year2 = None: end year. If included, the indicated year will
                represent the upper-end of years to assess. In the absence of
                the begin-year, all years from the start of the record-range
                to this indicated year will be used in ranking.
            descending = True: parallel bool used to determine reverse kw of
                sorted calls; whether results will be printed higher-to-lower
                or not.

        Keyword Arguments:
            start = (1, 1): list/tuple given to indicate the starting month and
                day wherein a season's calculations will be made.
            thru = (12,31): list/tuple representing the month and day that you
                want to assess the seasons through. If start != (1,1) but thru
                == (12,31), the stats reported will be through the Season's
                ending.

        Examples:
        ---------
        <Hurdat2>.rank_seasons_thru(10, "ACE", thru=[8,31]): Retrieve a report
            of tropical cyclone seasons sorted by the top-10 ACE values through
            August 31.
        <Hurdat2>.rank_seasons_thru(10, "TSreach", 1967, thru=[9,15]): Retrieve
            a report of tropical cyclone seasons sorted by the top-10 totals of
            tropical storms through September 15, since 1967 (the satellite
            era).
        <Hurdat2>.rank_seasons_thru(20, "track_distance_TC", start=[7,1], thru=(10,31)):
            Retrieve a report of the top-20 seasons of total distance traversed
            by storms while being designated as tropical cyclones, between July
            1st and the end of October.
        """

        year1 = self.record_range[0] if year1 is None \
            or year1 < self.record_range[0] else year1
        year2 = self.record_range[1] if year2 is None \
            or year2 > self.record_range[1] else year2

        # Partial-Season Bookened Month, Day Tuples
        start = kw.get("start", (1,1))
        thru = kw.get("thru", (12,31))

        # error if thru or start are not list/tuples
        if type(thru) not in [list,tuple]:
            return print("OOPS! Ensure thru is a list or tuple of (month,day)")
        if type(start) not in [list,tuple]:
            return print("OOPS! Ensure start is a list or tuple of (month,day)")

        # If the full year is being asked for, this is essentially just a
        #   wrapper for the regular rank_seasons method
        if start == (1,1) and thru == (12,31):
            result = self.rank_seasons(
                quantity,
                stattr,
                year1,
                year2,
                descending,
                info=kw.get("info")
            )
            return result

        rseason = {}
        for season in [s for s in self.season.values() \
                if year1 <= s.year <= year2 \
                or (kw.get("info") is not None \
                    and s.year == kw.get("info"))]:
            yr = season.year
            rseason[yr] = dict(
                tracks = 0, landfalls=0, landfall_TC = 0, landfall_TD = 0,
                landfall_TS = 0, landfall_HU = 0, landfall_MHU = 0,
                TSreach = 0, HUreach = 0, MHUreach = 0, track_distance = 0,
                track_distance_TC = 0, track_distance_TS = 0,
                track_distance_HU = 0, track_distance_MHU = 0,
                ACE = 0, HDP = 0, MHDP = 0, cat45reach = 0, cat5reach = 0
            )
            # account for a non-existant season being requested by stats method
            if kw.get("info") is not None and kw.get("info") not in self.season:
                rseason[kw.get("info")] = dict(
                tracks = 0, landfalls=0, landfall_TC = 0, landfall_TD = 0,
                landfall_TS = 0, landfall_HU = 0, landfall_MHU = 0,
                TSreach = 0, HUreach = 0, MHUreach = 0, track_distance = 0,
                track_distance_TC = 0, track_distance_TS = 0,
                track_distance_HU = 0, track_distance_MHU = 0,
                ACE = 0, HDP = 0, MHDP = 0, cat45reach = 0, cat5reach = 0
            )
            for tc in season.tc.values():
                track_added = False
                lndfls = False; lndfl_TC = False; lndfl_TD = False;
                lndfl_TS = False; lndfl_HU = False; lndfl_MHU = False;
                rTS = False; rHU = False; rMHU = False; r45 = False; r5 = False
                entries = [
                    trk for trk in tc.entry #\
                    # if start <= trk.month_day_tuple <= thru
                ]
                for INDX, ENTRY in enumerate(tc.entry):
                    # Handle Track Distance related vars;
                    # only need to check validity of INDX-1
                    # if INDX >= 1 and start <= tc.entry[INDX-1].month_day_tuple <= thru:
                    if INDX >= 1 \
                    and ((thru != (12,31) and start <= tc.entry[INDX-1].month_day_tuple <= thru) \
                    or (thru == (12,31) and datetime.date(tc.year, *start) <= tc.entry[INDX-1].entrytime.date())):
                        rseason[yr]["track_distance"] += haversine(
                            tc.entry[INDX-1].location,
                            tc.entry[INDX].location
                        )
                        rseason[yr]["track_distance_TC"] += haversine(
                            tc.entry[INDX-1].location,
                            tc.entry[INDX].location
                        ) if tc.entry[INDX-1].status in ("SD","TD","SS","TS","HU") else 0
                        rseason[yr]["track_distance_TS"] += haversine(
                            tc.entry[INDX-1].location,
                            tc.entry[INDX].location
                        ) if tc.entry[INDX-1].status in ("SS","TS","HU") else 0
                        rseason[yr]["track_distance_HU"] += haversine(
                            tc.entry[INDX-1].location,
                            tc.entry[INDX].location
                        ) if tc.entry[INDX-1].status == "HU" else 0
                        rseason[yr]["track_distance_MHU"] += haversine(
                            tc.entry[INDX-1].location,
                            tc.entry[INDX].location
                        ) if tc.entry[INDX-1].status == "HU" \
                          and tc.entry[INDX-1].wind >= 96 else 0
                    # Handle everything else
                    if (thru != (12,31) and start <= ENTRY.month_day_tuple <= thru) \
                    or (thru == (12,31) and datetime.date(tc.year, *start) <= ENTRY.entrytime.date()):
                    # if start <= ENTRY.month_day_tuple <= thru:
                        rseason[yr]["ACE"] += math.pow(ENTRY.wind,2) \
                            if ENTRY.wind >= 34 \
                            and ENTRY.status in ("SS","TS","HU") \
                            and ENTRY.is_synoptic \
                            else 0
                        rseason[yr]["HDP"] += math.pow(ENTRY.wind,2) \
                            if ENTRY.wind >= 64 \
                            and ENTRY.status == "HU" \
                            and ENTRY.is_synoptic \
                            else 0
                        rseason[yr]["MHDP"] += math.pow(ENTRY.wind,2) \
                            if ENTRY.wind >= 96 and ENTRY.status == "HU" \
                            and ENTRY.is_synoptic \
                            else 0
                        if track_added is False:
                            rseason[yr]["tracks"] += 1
                            track_added = True
                        if lndfls is False and ENTRY.record_identifier == "L":
                            rseason[yr]["landfalls"] += 1
                            lndfls = True
                        if lndfl_TC is False and ENTRY.record_identifier == "L" \
                                and ENTRY.is_TC:
                            rseason[yr]["landfall_TC"] += 1
                            lndfl_TC = True
                        if lndfl_TD is False and ENTRY.record_identifier == "L" \
                                and ENTRY.status in ["SD","TD"]:
                            rseason[yr]["landfall_TD"] += 1
                            lndfl_TD = True
                        if lndfl_TS is False and ENTRY.record_identifier == "L" \
                                and ENTRY.status in ["SS","TS","HU"]:
                            rseason[yr]["landfall_TS"] += 1
                            lndfl_TS = True
                        if lndfl_HU is False and ENTRY.record_identifier == "L" \
                                and ENTRY.status == "HU":
                            rseason[yr]["landfall_HU"] += 1
                            lndfl_HU = True
                        if lndfl_MHU is False and ENTRY.record_identifier == "L" \
                                and ENTRY.status == "HU" and ENTRY.wind >= 96:
                            rseason[yr]["landfall_MHU"] += 1
                            lndfl_MHU = True
                        if rTS is False and ENTRY.status in ["SS","TS","HU"]:
                            rseason[yr]["TSreach"] += 1
                            rTS = True
                        if rHU is False and ENTRY.status in ["HU"]:
                            rseason[yr]["HUreach"] += 1
                            rHU = True
                        if rMHU is False and ENTRY.wind >= 96:
                            rseason[yr]["MHUreach"] += 1
                            rMHU = True
                        if r45 is False and ENTRY.wind >= 114:
                            rseason[yr]["cat45reach"] += 1
                            r45 = True
                        if r5 is False and ENTRY.wind >= 136:
                            rseason[yr]["cat5reach"] += 1
                            r5 = True

        sorted_seasons = sorted(
            [s for s in self.season.values() if year1 <= s.year <= year2],
            key=lambda s: rseason[s.year][stattr],
            reverse = descending
        )
        # Values sorted
        ranks = sorted(
            set([
                rseason[s.year][stattr] for s in sorted_seasons \
                    if descending is False \
                    or (rseason[s.year][stattr] > 0 and kw.get("info") is None) \
                    or kw.get("info") is not None
            ]),
            reverse = descending
        )[:quantity]

        # RETURN if info method called this method
        if kw.get("info", None) is not None:
            if (year1 <= kw["info"] <= year2) is False:
                ranks = sorted(
                    set(ranks + [rseason[kw["info"]][stattr]]),
                    reverse = descending
                )
            return {
                "seasonvalu": rseason[kw["info"]][stattr],
                "rank": ranks.index(rseason[kw["info"]][stattr]) + 1,
                "tied": len(["tie" for season in rseason.values() if season[stattr] == rseason[kw["info"]][stattr]]) - 1,
                "outof": len(ranks)
            }

        # List that holds printed quantities
        printedqty = []

        print("")
        print("TOP {} SEASONS RANKED BY {}, {}".format(
                len(ranks),
                stattr.upper(),
                "{}through {}".format(
                    "from {} ".format(
                        "{} {}".format(
                            calendar.month_abbr[start[0]], start[1]
                        )
                    ) if "start" in kw else "",
                    "{} {}".format(
                        calendar.month_abbr[thru[0]], thru[1]
                    ) if thru != (12,31) else "End of Season"
                )
            ).center(79)
        )

        print("{}{}".format(
            str(self.basin()),
            ", {}-{}".format(year1, year2)
        ).center(79))
        print("-" * 79)

        print("{:4}  {:4}  {:^6}  {:^4}  {:^4} {:^4} {:^3}  {:^7}  {:^25}".format(
            "","","","LAND","QTY","","","TC DIST",
            "STATUS-RELATED TRACK" if "track_distance" in stattr else "ENERGY INDICES"
        ))
        print("{:4}  {:4}  {:^6}  {:^4}  {:^4} {:^4} {:^3}  {:^7}  {:^25}".format(
            "","","NUM OF","FALL","TRPC","QTY","QTY","TRAVRSD",
            "DISTANCES (nmi)" if "track_distance" in stattr else "x10^4 kt^2"
        ))
        print("RANK  YEAR  {:^6}  {:^4}  {:^4} {:^4} {:^3}  {:^7}  {:^7}  {:^7}  {:^7}".format(
            "TRACKS","TCs","STRM","HURR","MAJ","(nmi)",
            "TRPCSTM" if "track_distance" in stattr else "ACE",
            "HURRICN" if "track_distance" in stattr else "HDP",
            "MAJHURR" if "track_distance" in stattr else "MHDP"
        ))
        print("{:-^4}  {:-^4}  {:-^6}  {:-^4}  {:-^4} {:-^4} {:-^3}  {:-^7}  {:-^7}  {:-^7}  {:-^7}".format(
            "","","","","","","","","","",""
        ))
        for season in sorted_seasons:
            try:
                current_rank = ranks.index(rseason[season.year][stattr]) + 1 \
                    if ranks.index(rseason[season.year][stattr]) + 1 \
                    not in printedqty else None
            except:
                # indicates bounds beyond quantity asked for exceeded
                break
            print("{:>3}{:1}  {:4}  {:^6}  {:^4}  {:^4}  {:^4} {:^3}  {:>7.1f}  {:>{ACELEN}f}  {:>{ACELEN}f}  {:>{ACELEN}f}".format(
                current_rank if current_rank is not None else "", 
                "." if current_rank is not None else "",
                season.year,
                rseason[season.year]["tracks"],
                rseason[season.year]["landfall_TC"],
                rseason[season.year]["TSreach"],
                rseason[season.year]["HUreach"],
                rseason[season.year]["MHUreach"],
                rseason[season.year]["track_distance_TC"],
                rseason[season.year]["track_distance_TS"] if "track_distance" in stattr else rseason[season.year]["ACE"] * math.pow(10,-4),
                rseason[season.year]["track_distance_HU"] if "track_distance" in stattr else rseason[season.year]["HDP"] * math.pow(10,-4),
                rseason[season.year]["track_distance_MHU"] if "track_distance" in stattr else rseason[season.year]["MHDP"] * math.pow(10,-4),
                ACELEN = 7.1 if "track_distance" in stattr else 7.3
            ))
            if current_rank is not None and current_rank not in printedqty:
                printedqty.append(current_rank)
        print("")

    def rank_storms(self, quantity, stattr, year1=None, year2=None, coordextent=None, contains_method="anywhere"):
        """Rank and compare individual tropical cyclones to one another.

        Required Arguments:
            quantity: how long of a list of ranks do you want; an integer.
            stattr: the storm attribute that you'd like to rank seasons by.
            
                * Working Storm Attributes for ranking: 
                    "track_distance_TC", "landfalls", "maxwind", "minmslp",
                    "ACE", "track_distance_TS",  "HDP", "track_distance_HU",
                    "MHDP", "track_distance_MHU"

                * The following attributes will not work because at the
                individual storm level these are bools:
                    "landfall_TC", "landfall_TD", "landfall_TS", "landfall_HU",
                    "landfall_MHU", "TSreach", "HUreach", "MHUreach",
                    "cat45reach", "cat5reach"

                * Other attributes of class TropicalCyclone that are not
                mentioned here will work for ranking too, but their actual
                values will not display on the printed report.

        Default Arguments:
            year1 (None): begin year. If included, the indicated year will
                represent the low-end of years to assess. In the absence of
                the end-year, all years from this begin year to the end of the
                record-range will be used to determine ranking.
            year2 (None): end year. If included, the indicated year will
                represent the upper-end of years to assess. In the absence of
                the begin-year, all years from the start of the record-range
                to this indicated year will be used to determine ranking.
            coordextent (None): **EXPERIMENTAL** This accepts 2 tupled latitude
                and longitude coordinates, representing a geographical
                bounding-box. The use of this bounding-box is determined by the
                kwarg, contains_method. See the documentation for determination
                of use. The results from using these two arguments only
                indicates that the track of the storm identified *AT SOME
                POINT* tracked into this bounding-box. It in no way indicates
                that the ranked value occurred within.
            contains_method ("anywhere"): if a coordinate extent is included (see
                above), this default argument determines this method's
                strategy. The default of 'anywhere' implies that all matching
                storms will be further discriminated by whether or not any point of their track occurred within the bounding-box (coordextent). A value of "start" means if the start of the storm's track occurred in the bounding-box.

        Examples:
        ---------
        <Hurdat2>.rank_storms(10, "ACE"): Retrieve a report of tropical
                cyclones sorted by the top-10 values of Accumulated Cyclone
                Energy on record.
        <Hurdat2>.rank_storms(20, "HDP", 1967): Retrieve a report of tropical
                cyclones sorted by the top-20 values of Hurricane Destruction
                Potential since 1967 (the beginning of the satellite era).
        <Hurdat2>.rank_storms(5, "minmslp", 1901, 1940): Retrieve a report of the
                top-5 tropical cyclones with the lowest minimum pressure
                readings between 1901 and 1940.
        <Hurdat2>.rank_storms(10, "maxwind", coordextent=[(31,-98), (18,-80)])
                Retrieve a report of the top 10 storms, ranked by max-wind,
                whose genesis occurred in (roughly) the Gulf of Mexico.
        """

        year1 = self.record_range[0] if year1 is None \
            or year1 < self.record_range[0] else year1
        year2 = self.record_range[1] if year2 is None \
            or year2 > self.record_range[1] else year2

        # List of tropical-cyclones sorted by stattr
        sorted_storms = sorted(
            [tc for tc in self.tc.values() if year1 <= tc.year <= year2],
            key=lambda tc: getattr(tc, stattr),
            reverse = False if stattr == "minmslp" else True
        )
        # Values sorted
        ranks = sorted(
            set([
                getattr(tc, stattr) for tc in sorted_storms \
                    if stattr == "minmslp" \
                    or getattr(tc, stattr) > 0
            ]),
            reverse = False if stattr == "minmslp" else True
        )[:quantity]

        # If bounding-box coords provided...
        if coordextent is not None:
            contains_method = contains_method.lower()   # Ensure lowercase
            # Warning message
            if contains_method not in ["start", "anywhere"]:
                print(
                    "* Defaulting to 'anywhere' location method. The only "
                    "valid values for the contains_method keyword argument "
                    "are 'start' and 'anywhere'."
                )
                contains_method = "anywhere"
            # Just search starting point
            if contains_method == "start":
                sorted_storms = [
                    TC for TC in sorted_storms if self.coord_contains(
                        TC.entry[0].location,
                        coordextent[0],
                        coordextent[1]
                    )
                ]
            # Any point within the bounding-box
            else:
                sorted_storms = [
                    TC for TC in sorted_storms \
                    if any(
                        self.coord_contains(
                            entry.location,
                            *coordextent
                        ) for entry in TC.entry
                    )
                ]
            ranks = sorted(
                set([
                    getattr(TC, stattr) for TC in sorted_storms \
                        if stattr == "minmslp" \
                        or getattr(TC, stattr) > 0
                ]),
                reverse = False if stattr == "minmslp" else True
            )[:quantity]

        # List that holds printed quantities
        printedqty = []

        print("")
        print("TOP {} STORMS RANKED BY {}".format(
            len(ranks),
            stattr.upper()
        ).center(79))
        if coordextent is not None:
            print("{:^79}".format(
                "* Coordinate Bounding-Box: {}; {}".format(
                    "{}{} {}{}".format(
                        abs(coordextent[0][0]),
                        "N" if coordextent[1][0] >= 0 else "S",
                        abs(coordextent[0][1]),
                        "W" if -180 < coordextent[1][1] <= 0 else "E"
                    ),
                    "{}{} {}{}".format(
                        abs(coordextent[1][0]),
                        "N" if coordextent[1][0] >= 0 else "S",
                        abs(coordextent[1][1]),
                        "W" if -180 < coordextent[1][1] <= 0 else "E"
                    )
                )
            ))

        print("{}{}".format(
            str(self.basin()),
            ", {}-{}".format(year1, year2)
        ).center(79))
        print("-" * 79)

        print("{:^4}  {:^10} {:^8} {:^4} {:^4} {:^4}  {:^6}  {:^22}".format(
            "","","","LAND","","","TCDIST",
            "STATUS-RELATED TRACK" if "track" in stattr else "ENERGY INDICES"
        ))
        print("{:^4}  {:^10} {:^8} {:^4} {:>4} {:>4}  {:^6}  {:^22}".format(
            "","","","FALL","MIN","MAX","TRVRSD",
            "DISTANCES (nmi)" if "track" in stattr else "x10^4 kt^2"
        ))
        print("{:^4}  {:<10} {:^8} {:<4} {:^4} {:^4}  {:^6}  {:^6}  {:^6}  {:^6}".format(
            "RANK","NAME","ATCFID","QTY","MSLP","WIND","(nmi)",
            "TRPCST" if "track" in stattr else "ACE",
            "HURRCN" if "track" in stattr else "HDP",
            "MAJHUR" if "track" in stattr else "MHDP"
        ))
        print("{:-^4}  {:-^10} {:-^8} {:-^4} {:-^4} {:-^4}  {:-^6}  {:-^6}  {:-^6}  {:-^6}".format(
            "","","","","","","","","",""
        ))

        for TC in sorted_storms:
            try:
                current_rank = ranks.index(getattr(TC, stattr)) + 1 \
                    if ranks.index(getattr(TC, stattr)) + 1 \
                    not in printedqty else None
            except:
                break
            print("{:>3}{:1}  {:<10} {:8} {:^4} {:>4} {:>4}  {:>6.1f}  {:>{ACELEN}f}  {:>{ACELEN}f}  {:>{ACELEN}f}".format(
                current_rank if current_rank is not None else "", 
                "." if current_rank is not None else "",
                TC.name.title(),
                TC.atcfid,
                TC.landfalls,
                TC.minmslp if TC.minmslp is not None else "N/A",
                TC.maxwind if TC.maxwind > 0 else "N/A",
                TC.track_distance_TC,
                TC.track_distance_TS if "track" in stattr else TC.ACE * math.pow(10,-4),
                TC.track_distance_HU if "track" in stattr else TC.HDP * math.pow(10,-4),
                TC.track_distance_MHU if "track" in stattr else TC.MHDP * math.pow(10,-4),
                ACELEN = 6.1 if "track" in stattr else 6.3
            ))
            if current_rank is not None and current_rank not in printedqty:
                printedqty.append(current_rank)
        print("")

    def rank_climo(self, quantity, stattr, year1=None, year2=None, descending=True, **climoparam):
        """Rank and compare climatological eras to one another.

        Required Arguments:
            quantity: how long of a list of ranks do you want; an integer.
            stattr: the storm attribute that you'd like to rank seasons by.
            
                * Working Storm Attributes for ranking: 
                    "track_distance_TC", "landfalls", "maxwind", "minmslp",
                    "ACE", "track_distance_TS",  "HDP", "track_distance_HU",
                    "MHDP", "track_distance_MHU"

                * The following attributes will not work because at the
                individual storm level these are bools:
                    "landfall_TC", "landfall_TD", "landfall_TS", "landfall_HU",
                    "landfall_MHU", "TSreach", "HUreach", "MHUreach",
                    "cat45reach", "cat5reach"

                * Other attributes of class TropicalCyclone that are not
                mentioned here will work for ranking too, but their actual
                values will not display on the printed report.

        Default Arguments:
            year1 (None): begin year. If included, the indicated year will
                represent the low-end of years to assess. In the absence of
                the end-year, all years from this begin year to the end of the
                record-range will be used to determine ranking.
            year2 (None): end year. If included, the indicated year will
                represent the upper-end of years to assess. In the absence of
                the begin-year, all years from the start of the record-range
                to this indicated year will be used to determine ranking.
            descending (True): parallel bool used to determine reverse kw of
                sorted calls; whether results will be printed higher-to-lower
                or not.
        
        Optional Keyword Arguments (**climoparam):
            * These control Climatological Spans and Extents *
            climatology (30): the quantity of years that will be assessed per
                climate era.
            increment (5): the time (in years) between one climate era and the
                next (ex. 1981-2010, 1986-2015, etc).

        Examples:
        ---------
        <Hurdat2>.rank_climo(10,"ACE"): Retrieve the top 10 climate eras in the
            record that have the largest ACE (30yr climo; 5yr incremented)
        <Hurdat2>.rank_climo(20,"track_distance_TC", climatology=10, increment=1):
            Retrieve the top 20 10-year climatological eras (incremented by 1
            year) of accumulated tropical cyclone track-distance.
        """
        climatology = climoparam.get("climatology", 30)
        increment = climoparam.get("increment", 5)

        year1 = self.record_range[0] if year1 is None \
            or year1 < self.record_range[0] else year1
        year2 = self.record_range[1] if year2 is None \
            or year2 > self.record_range[1] else year2

        Era = collections.namedtuple("Era", ["era", stattr])

        climo = {}  # dictionary to hold the climatology data

        for yr1, yr2 in [(y, y+climatology-1) \
                for y in range(1801, year2, increment) \
                if year1 <= y <= year2 \
                and year1 <= y+climatology-1 <= year2]:
            climo[yr1, yr2] = Era(
                (yr1, yr2),
                sum(getattr(self.season[s], stattr) for s in range(yr1, yr2+1))
            )

        # List of tropical-cyclones sorted by stattr
        sorted_climo = sorted(
            [era for era in climo.values()],
            key=lambda era: getattr(era, stattr),
            reverse = descending
        )
        # Values sorted
        ranks = sorted(
            set([
                getattr(era, stattr) for era in sorted_climo \
                    if descending is False \
                    or getattr(era, stattr) > 0
            ]),
            reverse = descending
        )[:quantity]

        # Rank printed list
        printedqty = []

        print("")
        print("{:^41}".format(
            "TOP {} CLIMATOLOGICAL PERIODS".format(quantity)
        ))
        print("{:^41}".format(
            "RANKED BY {}".format(stattr.upper())
        ))
        print("{}{}".format(
            str(self.basin()),
            ", {}-{}".format(year1, year2)
        ).center(41))

        print("{:-^41}".format(""))
        print("{:^41}".format(
            "{}-Year Climatologies; {}-Year Incremented".format(
                climatology,
                increment
            )
        ))
        print("{:-^41}".format(""))
        print(" {:^4}  {:^9}  {:^12}".format(
            "RANK",
            "PERIOD",
            stattr.upper()
        ))
        print(" {:-^4}  {:-^9}  {:-^12}".format(
            "","",""
        ))
        for clmt in sorted_climo:
            try:
                current_rank = ranks.index(getattr(clmt, stattr)) + 1 \
                    if ranks.index(getattr(clmt, stattr)) + 1 \
                    not in printedqty else None
            except:
                break
            print(" {:>4}  {:9}  {}".format(
                "{:>3}{:1}".format(
                    current_rank if current_rank is not None else "", 
                    "." if current_rank is not None else ""
                ),
                "{}-{}".format(*clmt.era),
                getattr(clmt,stattr)
            ))
            if current_rank is not None and current_rank not in printedqty:
                printedqty.append(current_rank)
        print("")

    def _season_stats_str(self, seasonreq, year1, year2, rstart, rthru, width, **kw):
        strlist = []
        yr = seasonreq
        strlist.append("-" * width)
        strlist.append("Tropical Cyclone Stats for {}".format(yr).center(width))
        strlist.append(
            "{}{}".format(
                self.basin(),
                ""
            ).center(width)
        )
        strlist[-1] += "\n"

        statyrline = "Stats calculated for Seasons {}".format(
            "{}-{}".format(
                year1,
                year2
            ) if year2 != self.record_range[1] \
            else "since {} ({} total seasons)".format(
                year1,
                self.record_range[1] - year1 + 1
            )
        ).center(width)
        strlist.append(statyrline)

        if rstart != (1,1) or rthru != (12,31):
            strlist.append(
                "from {} thru {}".format(
                    "{} {}".format(
                        calendar.month_name[rstart[0]],
                        rstart[1],
                    ),
                    "{} {}".format(
                        calendar.month_name[rthru[0]],
                        rthru[1],
                    )
                ).center(width)
            )
        strlist[-1] += "\n"
        for line in textwrap.wrap(
            "* TS-related Statistics include Hurricanes in their totals" \
            " except for landfall data",
            width,
            initial_indent=" " * 4,
            subsequent_indent=" " * 4
        ):
            strlist.append(line.center(width))
        strlist[-1] += "\n"
        if any(1971 <= y <= 1990 for y in range(year1, year2 + 1)):
            for line in textwrap.wrap(
                "* Hurdat2 Landfall data incomplete for seasons 1971-1990",
                width,
                initial_indent=" " * 4,
                subsequent_indent=" " * 4
            ):
                strlist.append(line.center(width))
        strlist.append("-" * width)

        for attr, label in [
            ("tracks", "Tropical Cyclones"),
            ("track_distance_TC", "TC Track Distance"),
            ("track_distance_TS", "TS Distance"),
            ("track_distance_HU", "HU Distance"),
            ("track_distance_MHU", "MHU Distance"),
            ("TSreach", "Tropical Storms"),
            ("ACE", "ACE"),
            ("HUreach", "Hurricanes"),
            ("HDP", "HDP"),
            ("MHUreach", "Major Hurricanes"),
            ("MHDP", "MHDP"),
            ("landfall_TC", "Total Landfalling TC's"),
            ("landfall_TS", "TS Landfalls"),
            ("landfall_HU", "HU Landfalls")
        ]:
            if "landfall" not in attr or ("landfall" in attr and all(1971 <= y <= 1990 for y in range(year1, year2)) is False):
                rankinfo = self.rank_seasons_thru(
                    1337,
                    attr,
                    year1,
                    year2,
                    start = rstart,
                    thru = rthru,
                    descending=kw.get("descending", True),
                    info=yr
                )
                strlist.append('{:<35}Rank {}/{}{}'.format(
                    "* {}: {}{}   ".format(
                        label,
                        "{:.1f}".format(rankinfo["seasonvalu"]) \
                            if "distance" in attr \
                            else ("{:.1f}".format(rankinfo["seasonvalu"] * 10 ** (-4)) \
                                if attr in ["ACE", "HDP", "MHDP"] \
                                else rankinfo["seasonvalu"]
                            ),
                        " nmi" if "track_distance" in attr \
                            else (" * 10^4 kt^2" \
                                if attr in ["ACE", "HDP", "MHDP"] else ""
                            ),
                    ),
                    rankinfo["rank"],
                    rankinfo["outof"],
                    " (tied w/{} other season{})".format(
                        rankinfo["tied"],
                        "s" if rankinfo["tied"] >= 2 else ""
                    ) if rankinfo["tied"] > 0 else ""
                ))
        strlist.append("\n")
        return "\n".join(strlist)

    def _season_stats(self, seasonreq, year1, year2, rstart, rthru, width, **kw):

        yr = seasonreq

        print("")
        print("-" * width)
        print("Tropical Cyclone Stats for {}".format(yr).center(width))
        print("{}{}".format(
                self.basin(),
                ""
            ).center(width)
        )
        print("")
        for line in textwrap.wrap(
                "Stats calculated for Seasons {}".format(
                    "{}-{}".format(
                        year1,
                        year2
                    ) if year2 != self.record_range[1] \
                    else "since {} ({} total seasons)".format(
                        year1,
                        self.record_range[1] - year1 + 1
                    )
                ),
                width,
                initial_indent=" " * 4,
                subsequent_indent=" " * 4):
            print(line.center(width))
        if rstart != (1,1) or rthru != (12,31):
            print(
                "from {} thru {}".format(
                    "{} {}".format(
                        calendar.month_name[rstart[0]],
                        rstart[1],
                    ),
                    "{} {}".format(
                        calendar.month_name[rthru[0]],
                        rthru[1],
                    )
                ).center(width)
            )
        print("")
        for line in textwrap.wrap(
                "* TS-related Statistics include Hurricanes in their totals" \
                " except for landfall data",
                width,
                initial_indent=" " * 4,
                subsequent_indent=" " * 4):
            print(line.center(width))

        print("")
        # Only print this disclaimer if years in this range overlap
        if any(1971 <= y <= 1990 for y in range(year1, year2 + 1)):
            for line in textwrap.wrap(
                    "* Hurdat2 Landfall data incomplete for seasons 1971-1990",
                    width,
                    initial_indent=" " * 4,
                    subsequent_indent=" " * 4):
                print(line.center(width))
        print("-" * width)

        for attr, label in [
            ("tracks", "Tropical Cyclones"),
            ("track_distance_TC", "TC Track Distance"),
            ("track_distance_TS", "TS Distance"),
            ("track_distance_HU", "HU Distance"),
            ("track_distance_MHU", "MHU Distance"),
            ("TSreach", "Tropical Storms"),
            ("ACE", "ACE"),
            ("HUreach", "Hurricanes"),
            ("HDP", "HDP"),
            ("MHUreach", "Major Hurricanes"),
            ("MHDP", "MHDP"),
            ("landfall_TC", "Total Landfalling TC's"),
            ("landfall_TS", "TS Landfalls"),
            ("landfall_HU", "HU Landfalls")
        ]:
            if "landfall" not in attr or ("landfall" in attr and all(1971 <= y <= 1990 for y in range(year1, year2)) is False):
                rankinfo = self.rank_seasons_thru(
                    1337,
                    attr,
                    year1,
                    year2,
                    start = rstart,
                    thru = rthru,
                    descending=kw.get("descending", True),
                    info=yr
                )
                print('{:<35}Rank {}/{}{}'.format(
                    "* {}: {}{}   ".format(
                        label,
                        "{:.1f}".format(rankinfo["seasonvalu"]) \
                            if "distance" in attr \
                            else ("{:.1f}".format(rankinfo["seasonvalu"] * 10 ** (-4)) \
                                if attr in ["ACE", "HDP", "MHDP"] \
                                else rankinfo["seasonvalu"]
                            ),
                        " nmi" if "track_distance" in attr \
                            else (" * 10^4 kt^2" \
                                if attr in ["ACE", "HDP", "MHDP"] else ""
                            ),
                    ),
                    rankinfo["rank"],
                    rankinfo["outof"],
                    " (tied w/{} other season{})".format(
                        rankinfo["tied"],
                        "s" if rankinfo["tied"] >= 2 else ""
                    ) if rankinfo["tied"] > 0 else ""
                ))
        print("")

class SeasonCalculations:

    @property
    def start_date(self):
        """The <<datetime>> of the start of the season."""
        return self.tc_entries[0].entrytime

    @property
    def start_ordinal(self):
        """The day-number (1-365) of the year that the start of the season took
        place.
        """
        return self.start_date.replace(year=1).toordinal()

    @property
    def end_date(self):
        """The <<datetime>> of the end of the season."""
        last_tc_en = self.tc_entries[-1]
        return last_tc_en.next_entry.entrytime \
            if last_tc_en.next_entry is not None \
            else last_tc_en.entrytime

    @property
    def end_ordinal(self):
        """The day-number (1-365) of the year that the end of the season
        occurred.

        In the event that the day number exceeds 365, it generally means that
        the season extended into the following year.
        """
        end = self.end_date.replace(year=1).toordinal()
        # protect against seasons that extend into the following year
        if end <= self.start_ordinal:
            return self.end_date.replace(year=2).toordinal()
        else:
            return end

    @property
    def duration(self):
        """Returns the duration of the season in days.

        This is calculated using the .start_date and .end_date for the season
        """
        tdelta = self.end_date - self.start_date
        # return all_times[-1] - all_times[0]
        return tdelta.days + tdelta.seconds / 86400

    @property
    def track_distance(self):
        """Returns the accumulated track distances (in nmi) of all systems
        during the season, regardless of the systems' status.
        """
        return sum(tcyc.track_distance for tcyc in self.tc.values())

    @property
    def track_distance_TC(self):
        """Returns the accumulated track distances (in nmi) of all systems
        during the season, while the systems were designated as tropical
        cyclones ("SD","SS","TD","TS","HU").
        """
        return sum(tcyc.track_distance_TC for tcyc in self.tc.values())

    @property
    def ACE(self):
        """Returns the accumulated cyclone energy (ACE) for the entire season,
        being the sum of all individual tropical cyclone ACE's.
        """
        return sum(tcyc.ACE for tcyc in self.tc.values())

    @property
    def track_distance_TS(self):
        """Returns the sum of track distances (in nmi) of all tropical
        cyclones while they were designated as at-least tropical storms (SS,
        TS, or HU).
        """
        return sum(tcyc.track_distance_TS for tcyc in self.tc.values())

    @property
    def HDP(self):
        """Returns the hurricane destruction potential (HDP) for the entire
        season, being the sum of all individual tropical cyclone HDP's.
        """
        return sum(tcyc.HDP for tcyc in self.tc.values())

    @property
    def track_distance_HU(self):
        """Returns the sum of track distances (in nmi) of all tropical
        cyclones while they were of hurricane status.
        """
        return sum(tcyc.track_distance_HU for tcyc in self.tc.values())

    @property
    def MHDP(self):
        """Returns the major hurricane destruction potential (MHDP) for the
        entire season, being the sum of all individual tropical cyclone MHDP's.
        """
        return sum(tcyc.MHDP for tcyc in self.tc.values())

    @property
    def track_distance_MHU(self):
        """Returns the sum of track distances (in nmi) of all tropical
        cyclones when the storms were designated as major hurricanes.
        """
        return sum(tcyc.track_distance_MHU for tcyc in self.tc.values())

class TropicalCycloneCalculations:

    @property
    def start_date(self):
        """The <<datetime>> of the birth of the tropical cyclone."""
        return self.tc_entries[0].entrytime \
            if len(self.tc_entries) > 0 else None

    @property
    def start_ordinal(self):
        """
        The day-number (1-365) of the year that the birth of the tropical
        cyclone took place.
        """
        return self.tc_entries[0].entrytime.replace(year=1).toordinal() \
            if len(self.tc_entries) > 0 else None

    @property
    def end_date(self):
        """The <<datetime>> where the storm became post-tropical."""
        if len(self.tc_entries) > 0:
            return self.tc_entries[-1].next_entry.entrytime \
                if self.tc_entries[-1].next_entry is not None \
                else self.tc_entries[-1].entrytime
        else:
            return None

    @property
    def end_ordinal(self):
        """
        The day-number (1-365) of the year that the tropical cyclone became
        post-tropical.

        In the event that the day number exceeds 365, it generally means that
        the tropical storm didn't become post-tropical until the following
        year.
        """
        if len(self.tc_entries) > 0:
            end = self.end_date.replace(year=1).toordinal()
            # protect against seasons that extend into the following year
            if end <= self.start_ordinal:
                return self.end_date.replace(year=2).toordinal()
            else:
                return end
        else:
            return None

    @property
    def duration(self):
        """
        The track duration in days; simply the end time minus the beginning
        time. In essence, this variable disregards the status of the storm.

        For more substantive properties, try duration_<TC, TS, HU, or MHU> for
        aggregated measurements as storms can lose and regain statuses
        """

        return (self.entry[-1].entrytime - self.entry[0].entrytime).days \
             + (self.entry[-1].entrytime - self.entry[0].entrytime).seconds / 86400

    @property
    def track_distance(self):
        """Returns the distance (in nmi) traversed by the system, regardless of
        status (whether or not the system is designated as a tropical cyclone).
        """
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
        )

    @property
    def duration_TC(self):
        """
        This is the total time that a storm was a designated tropical cyclone.

        * Of note * A storm can lose previous tropical cyclone status but
        regain it. For the Atlantic Hurdat2, this occurs in around 2.6% of
        storms, but almost 8% of storms since the year 2000. So if one compares
        track life versus this duration property, it isn't out of the question
        that they'll be different. See Hurricane Ivan (2004) as a prime
        example.
        """

        totes = sum(
            (en.next_entry.entrytime - en.entrytime).days
            + (en.next_entry.entrytime - en.entrytime).seconds / 86400
            if en.next_entry is not None
            and en.is_TC
            else 0
            for en in self.entry
        )

        return totes

    @property
    def track_distance_TC(self):
        """The distance (in nmi) trekked by the system when a designated
        tropical cyclone (status as a tropical or sub-tropical depression, a
        tropical or sub-tropical storm, or a hurricane).
        """
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
            and en.previous_entry.is_TC
        )

    @property
    def ACE(self):
        """Returns the tropical cyclone's Accumulated Cyclone Energy (ACE).

        Using values from required observations (0Z, 6Z, 12Z, and 18Z), this
        variable is "calculated by summing the squares of the estimated
        6-hourly maximum sustained surface wind speed in knots for all periods
        while the system is either a tropical storm or hurricane." (G. Bell,
        M. Chelliah. Journal of Climate. Vol. 19, Issue 4. pg 593. 15 February
        2006.). 

        Because sub-tropical storms (SS) still have some tropical
        characteristics, their values are included as well. Regardless of the
        case for or against, note that it is a very small contribution. Using
        the Atlantic Hurdat2 Database as an example, when included in the
        calculation (using only storms since 1968, as that is when the SS
        designation first appears in the Atlantic HURDAT2), only around 2.5% of ACE
        contribution has occurred from sub-tropical storms.
        """
        return sum(
            math.pow(en.wind,2) for en in self.entry
            if en.wind >= 34
            and en.is_synoptic
            and en.status in ("SS","TS","HU")
        )

    @property
    def perc_ACE(self):
        """The percent (decimal form) of total season ACE contributed by this
        storm.
        """
        if self._season.ACE > 0:
            return self.ACE / self._season.ACE
        else:
            return 0

    @property
    def duration_TS(self):
        """
        This is the total time that a storm was designated at least a tropical
        storm.
        """

        totes = sum(
            (en.next_entry.entrytime - en.entrytime).days
            + (en.next_entry.entrytime - en.entrytime).seconds / 86400
            if en.next_entry is not None
            and en.status in ["SS", "TS", "HU"]
            else 0
            for en in self.entry
        )

        return totes

    @property
    def track_distance_TS(self):
        """The distance (in nmi) trekked by the system while a tropical storm
        or hurricane.
        """
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
            and en.previous_entry.status in ["SS", "TS", "HU"]
        )

    @property
    def track_TS_perc_TC(self):
        """Returns the system's tropical storm track-distance divided by its 
        tropical cyclone track-distance.

        This value represents the proportional distance of a storm that
        occurred while it was at-least a tropical storm compared to when it was
        a designated tropical cyclone.

        None will be returned if track_distance_TC == 0
        """
        if self.track_distance_TC != 0:
            return round(self.track_distance_HU / self.track_distance_TC,2)
        else:
            return None

    @property
    def ACE_per_nmi(self):
        """Returns the Accumulated Cyclone Energy (ACE) divided by the
        systems's track-distance when it was at-least a tropical storm.
        """
        return self.ACE / self.track_distance_TS if self.track_distance_TS > 0 else 0

    @property
    def ACE_no_landfall(self):
        """Returns the ACE of the storm prior to any landfall made (if
        applicable).
        """

        ace_no_lf = 0
        for en in self.entry:
            if en.record_identifier == "L":
                break
            if en.wind >= 34 \
            and en.is_synoptic \
            and en.status in ("SS","TS","HU"):
                ace_no_lf += math.pow(en.wind, 2)
        return ace_no_lf

    @property
    def HDP(self):
        """Returns the tropical cyclone's Hurricane Destruction Potential
        (HDP).

        Using values from required observations (0Z, 6Z, 12Z, and 18Z), this
        variable is "calculated by summing the squares of the estimated
        6-hourly maximum sustained wind speed for all periods in which the
        system is a hurricane." (Bell, et. al. Climate Assessment for 1999.
        Bulletin of the American Meteorological Society. Vol 81, No. 6. June
        2000. S19.)
        """
        return sum(
            math.pow(en.wind, 2) for en in self.entry
            if en.wind >= 64
            and en.is_synoptic
            and en.status == "HU"
        )

    @property
    def perc_HDP(self):
        """The percent (decimal form) of total season HDP contributed by this
        storm.
        """
        if self._season.HDP > 0:
            return self.HDP / self._season.HDP
        else:
            return 0

    @property
    def duration_HU(self):
        """
        This is the total time that a storm was designated at a hurricane.
        """

        totes = sum(
            (en.next_entry.entrytime - en.entrytime).days
            + (en.next_entry.entrytime - en.entrytime).seconds / 86400
            if en.next_entry is not None
            and en.status == "HU"
            else 0
            for en in self.entry
        )

        return totes

    @property
    def track_distance_HU(self):
        """The distance (in nmi) trekked by the system while a hurricane."""
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
            and en.previous_entry.status == "HU"
        )

    @property
    def HDP_per_nmi(self):
        """Returns the system's Hurricane Destruction Potential (HDP) divided
        by the systems's track-distance when it was a hurricane.
        """

        return self.HDP / self.track_distance_HU if self.track_distance_HU > 0 else 0

    @property
    def HDP_perc_ACE(self):
        """Returns the system's HDP divided by its ACE.

        This is the value (0 is lowest; 1 highest) representing how much
        contribution to ACE was made while a system was designated as a
        hurricane.

        return None will occur if ACE is 0 for the system.
        """
        if self.ACE != 0: return round(self.HDP / self.ACE,2)
        else: return None

    @property
    def track_HU_perc_TC(self):
        """Returns the system's hurricane track-distance divided by its
        tropical cyclone track-distance

        This value represents the proportional distance of a storm that
        occurred while it was a hurricane compared to when it was a designated
        tropical cyclone.

        None will be returned if track_distance_TC == 0
        """
        if self.track_distance_TC != 0:
            return round(self.track_distance_HU / self.track_distance_TC,2)
        else:
            return None

    @property
    def track_HU_perc_TS(self):
        """Returns the system's hurricane track-distance divided by its
        tropical storm track-distance.

        This value represents the proportional distance of a storm that
        occurred while it was a hurricane compared to when it was at-least a
        tropical storm.

        None will be returned if track_distance_TS == 0
        """
        if self.track_distance_TS != 0:
            return round(self.track_distance_HU / self.track_distance_TS,2)
        else:
            return None

    @property
    def MHDP(self):
        """Returns the tropical cyclone's Major Hurricane Destruction Potential
        (MHDP).

        This inclusion of this variable is merely an extension of the
        definitions of ACE and HDP, which are widely referenced indices. This
        takes the logic of those definitions and applies it only to major-
        hurricanes (max-wind >= 96kts).
        """
        return sum(
            math.pow(en.wind, 2) for en in self.entry
            if en.wind >= 96
            and en.is_synoptic
            and en.status == "HU"
        )

    @property
    def perc_MHDP(self):
        """The percent (decimal form) of total season MHDP contributed by this
        storm.
        """
        if self._season.MHDP > 0:
            return self.MHDP / self._season.MHDP
        else:
            return 0

    @property
    def duration_MHU(self):
        """
        This is the total time that a storm was designated at a hurricane.
        """

        totes = sum(
            (en.next_entry.entrytime - en.entrytime).days
            + (en.next_entry.entrytime - en.entrytime).seconds / 86400
            if en.next_entry is not None
            and en.status == "HU" and en.wind >= 96
            else 0
            for en in self.entry
        )

        return totes

    @property
    def track_distance_MHU(self):
        """The distance (in nmi) trekked by the system while a major
        hurricane.
        """
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self.entry
            if en.previous_entry is not None
            and en.previous_entry.wind >= 96
            and en.previous_entry.status == "HU"
        )

    @property
    def MHDP_per_nmi(self):
        """Returns the system's Major Hurricane Destruction Potential (MHDP)
        divided by the systems's track-distance when it was a major hurricane.
        """
        return self.MHDP / self.track_distance_MHU if self.track_distance_MHU > 0 else 0

    @property
    def MHDP_perc_ACE(self):
        """Returns the system's MHDP divided by its ACE.

        This is the value (0 is lowest; 1 highest) representing how much
        contribution to ACE was made while a system was designated as a
        major hurricane.

        return None will occur if ACE is 0 for the system.
        """
        if self.ACE != 0: return round(self.MHDP / self.ACE,2)
        else: return None

    @property
    def track_MHU_perc_TC(self):
        """Returns the system's major-hurricane track-distance divided by its
        tropical cyclone track-distance.

        This value represents the proportional distance of a storm that
        occurred while it was a major-hurricane compared to when it was a
        designated tropical cyclone.

        None will be returned if track_distance_TC == 0
        """
        if self.track_distance_TC != 0:
            return round(self.track_distance_MHU / self.track_distance_TC,2)
        else:
            return None

    @property
    def track_MHU_perc_TS(self):
        """Returns the system's major-hurricane track-distance divided by its
        tropical storm track-distance.

        This value represents the proportional distance of a storm that
        occurred while it was a major-hurricane compared to when it was at-
        least a tropical storm.

        None will be returned if track_distance_TS == 0
        """
        if self.track_distance_TS != 0:
            return round(self.track_distance_MHU / self.track_distance_TS,2)
        else:
            return None

    @property
    def MHDP_perc_HDP(self):
        """Returns the system's MHDP divided by its HDP.

        This is the value (0 is lowest; 1 highest) representing how much
        contribution to its HDP was made while a system was designated as a
        major hurricane.

        return None will occur if HDP is 0 for the system.
        """
        if self.HDP != 0: return round(self.MHDP / self.HDP,2)
        else: return None

    @property
    def track_MHU_perc_HU(self):
        """Returns the system's major-hurricane track-distance divided by its
        hurricane track-distance.

        This value represents the proportional distance of a storm that
        occurred while it was a major-hurricane compared to when it was a
        hurricane.

        None will be returned if track_distance_HU == 0
        """
        if self.track_distance_HU != 0:
            return round(self.track_distance_MHU / self.track_distance_HU,2)
        else:
            return None


class TCEntryCalculations:

    __slots__ = []

    @property
    def track_distance(self):
        """
        The track distance traversed by the system (regardless of status) from
        the start of the track to the time of this <<TCRecordEntry>>
        """
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self._tc.entry
            if self._tc.entry.index(en) <= self._tc.entry.index(self)
            and en.previous_entry is not None
        )

    @property
    def track_distance_TC(self):
        """
        The track distance traversed by the system while designated a tropical
        cyclone from the start of the track to the time of this
        <<TCRecordEntry>>.
        """
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self._tc.entry[:self._tc.entry.index(self)+1]
            if en.previous_entry is not None
            and en.previous_entry.is_TC
        )

    @property
    def track_distance_TS(self):
        """
        The track distance traversed by the system while a tropical storm or
        stronger, from the start of the track to the time of this
        <<TCRecordEntry>>
        """
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self._tc.entry[:self._tc.entry.index(self)+1]
            if en.previous_entry is not None
            and en.previous_entry.status in ("SS", "TS", "HU")
        )

    @property
    def track_distance_HU(self):
        """
        The track distance traversed by the system while designated a hurricane
        from the start of the track to the time of this <<TCRecordEntry>>
        """
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self._tc.entry[:self._tc.entry.index(self)+1]
            if en.previous_entry is not None
            and en.previous_entry.status == "HU"
        )

    @property
    def track_distance_MHU(self):
        """
        The track distance traversed by the system while designated a major-
        hurricane, from the start of the track to the time of this
        <<TCRecordEntry>>
        """
        return sum(
            haversine(en.previous_entry.location, en.location)
            for en in self._tc.entry[:self._tc.entry.index(self)+1]
            if en.previous_entry is not None
            and en.previous_entry.status == "HU"
            and en.previous_entry.wind >= 96
        )

    def direction(self, cardinal=False):
        """Returns the heading (in degrees) of the tropical cyclone at the time
        of the <TCRecordEntry>.

        This is calculated using this and the previous entry locations.

        Default Argument
        ----------------
            cardinal (False): if True, it will return an accurate cardinal
                direction abbreviation (ex: 'NNW' == North-Northwest) instead
                of degrees.

        Of note, the first entry (index of 0) of any tropical cyclone will not
        have any associated direction because there is no previous entry to
        compare it with.

        For reference:
              Degrees           Direction
            ----------      -------------------
              0 //  45      North // North-east
             90 // 135      East  // South-east
            180 // 225      South // South-west
            270 // 315      West  // North-west
        """
        if self._tc.entry.index(self) != 0:
            dlat = self.latitude - self.previous_entry.latitude
            # account for longitudinal traversals of 180E/-180W
            if abs(self.longitude - self.previous_entry.longitude) < 180:
                dlon = self.longitude - self.previous_entry.longitude
            else:
                dlon = self.longitude + (
                    360 * (1 if self.longitude < 0 else -1)
                ) - self.previous_entry.longitude
            deg_dir = math.degrees(math.atan2(dlon, dlat))
            if cardinal is True:
                return cardinal_direction(
                    deg_dir + (360 if deg_dir < 0 else 0)
                )
            else:
                return deg_dir + (360 if deg_dir < 0 else 0)
        else:
            return None

    @property
    def speed(self):
        """
        Returns the forward lateral speed of the tropical cyclone at the time
        of the <TCRecordEntry> in knots (nautical miles per hour).

        This is calculated using this and the previous entry locations (gps
        coordinates) and the time of the entry.

        Of note, the first entry (index of 0) of any tropical cyclone will not
        have any associated speed because there is no previous entry to compare
        it to.
        """
        if self._tc.entry.index(self) != 0:
            dist = haversine(self.location, self.previous_entry.location)
            et = (self.entrytime - self.previous_entry.entrytime).seconds / 60 / 60
            return dist / et
        else:
            return None

    @property
    def saffir_simpson(self):
        return saffir_simpson_scale(self.wind)

    @property
    def avg_wind_extent_TS(self):
        """Returns the average extent of at-least tropical storm winds."""
        return statistics.mean(self.extent_TS)

    @property
    def areal_extent_TS(self):
        """Return the instantaneous maximum tropical-storm-strength wind areal
        expanse (in nmi^2) covered by the storm.
        
        This is calculated by taking each TS-wind quadrant value and summing
        their areal-extents (those extents being considered 1/4 of a circle). 
        """
        return sum(
            math.pi * math.pow(r, 2) / 4
            for r in self.extent_TS
            if r is not None
        )

    @property
    def avg_wind_extent_TS50(self):
        """Returns the average extent of at-least gale winds."""
        return statistics.mean(self.extent_TS50)

    @property
    def areal_extent_TS50(self):
        """Return the instantaneous maximum gale-strength wind (TS50; winds >=
        50kts) areal expanse (in nmi^2) covered by the storm.
        
        This is calculated by taking each TS50-wind quadrant value and summing
        their areal-extents (those extents being considered 1/4 of a circle). 
        """
        return sum(
            math.pi * math.pow(r, 2) / 4 \
            for r in self.extent_TS50 \
            if r is not None
        )

    @property
    def avg_wind_extent_HU(self):
        """Returns the average extent of hurricane-strength winds."""
        return statistics.mean(self.extent_HU)

    @property
    def areal_extent_HU(self):
        """Return the instantaneous maximum hurricane-strength wind areal
        expanse (in nmi^2) covered by the storm.
        
        This is calculated by taking each HU-wind quadrant value and summing
        their areal-extents (those extents being considered 1/4 of a circle).
        """

        return sum(
            math.pi * math.pow(r, 2) / 4 \
            for r in self.extent_HU \
            if r is not None
        )

def saffir_simpson_scale(spd):
    """Static method that returns the equivalent saffir-simpson scale rating,
    based on wind-speed in knots.

    This is the most-common index used to generalize tropical cyclone
    intensity. Tropical storm speeds will return 0; Weaker storms will return
    -1.

    Example: saffir_simpson_scale(100) --> 3 (implying category 3).
    """
    if 34 <= spd < 64:     return 0
    elif 64 <= spd < 83:   return 1
    elif 83 <= spd < 96:   return 2
    elif 96 <= spd < 114:  return 3
    elif 114 <= spd < 136: return 4
    elif spd >= 136:   return 5
    else: return -1

def distance_from_coordinates(lat, lon, distance, direction):
    latr = math.radians(lat)
    lonr = math.radians(lon)
    if distance == None: distance = 0
    r = 3440.065    # mean radius of earth in nmi
    
    if direction in ["N", "S"]:
        y = (1 if direction == "N" else -1) * distance / r + latr
        return (math.degrees(y), lon)
    else:
        # x = (2 if direction == "E" else -1) * math.asin(distance / (2 * r * math.pow(math.cos(latr), 2))) + lonr
        # x = (2 if direction == "E" else -2) * math.asin(math.sqrt(distance / math.pow(math.cos(latr), 2))) + lonr
        # x = (1 if direction == "E" else -1) * math.acos(2 * distance / math.cos(latr)**2) + lonr
        x = (2 if direction == "E" else -2) * math.asin(math.sqrt(math.pow(math.sin(distance / (2 * r)), 2) / math.pow(math.cos(latr), 2))) + lonr
        return (lat, math.degrees(x))

def haversine(startpos, endpos):
    """Returns the distance (in nmi) between two tupled GPS coordinates.

    Args:
        startpos: the starting gps-coordinate point; in tuple form of 
            (latitude, longitude). Both need to be an int or float.
        endpos: the ending gps-coordinate point; in tuple form of (latitude,
            longitude). Both need to be an int or float.

    The formula used was found on Wikipedia
        (https://en.wikipedia.org/wiki/Haversine_formula).
    """
    lat1 = math.radians(startpos[0])
    lon1 = math.radians(startpos[1])
    lat2 = math.radians(endpos[0])
    lon2 = math.radians(endpos[1])
    r = 3440.065    # mean radius of earth in nmi
    d = 2 * r * math.asin(math.sqrt(math.pow(math.sin((lat2 - lat1)/2),2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin((lon2-lon1)/2),2)))
    return d

def cardinal_direction(deg):
    """
    Returns the cardinal direction (an abbreviation) based on a degree-heading.

    Examples:
        10.5 --> 'N'
        257  --> 'WSW'
        20.2 --> 'NNE'
        93   --> 'E'
        165  --> 'SSE'
    """
    if   deg <=  11.25: return "N"
    elif deg <=  33.75: return "NNE"
    elif deg <=  56.25: return "NE"
    elif deg <=  78.75: return "ENE"
    elif deg <= 101.25: return "E"
    elif deg <= 123.75: return "ESE"
    elif deg <= 146.25: return "SE"
    elif deg <= 168.75: return "SSE"
    elif deg <= 191.25: return "S"
    elif deg <= 213.75: return "SSW"
    elif deg <= 236.25: return "SW"
    elif deg <= 258.75: return "WSW"
    elif deg <= 281.25: return "W"
    elif deg <= 303.75: return "WNW"
    elif deg <= 326.25: return "NW"
    elif deg <= 348.75: return "NNW"
    else: return "N"


def direction(lat1, lon1, lat2, lon2, cardinal=False):
    """
    This is essentially a mirror function of the
    <TCEntryCalculations>.direction method. Just included so I could test some
    arbitrary coordinates and revisit later if I choose.
    """
    dlat = lat2 - lat1
    # account for longitudinal traversals of 180E/-180W
    if abs(lon2 - lon1) < 180:
        dlon = lon2 - lon1
    else:
        dlon = lon2 + (
            360 * (1 if lon2 < 0 else -1)
        ) - lon1
    deg_dir = math.degrees(math.atan2(dlon, dlat))
    if cardinal is True:
        return cardinal_direction(
            deg_dir + (360 if deg_dir < 0 else 0)
        )
    else:
        return deg_dir + (360 if deg_dir < 0 else 0)

























