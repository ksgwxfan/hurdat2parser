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

import math
import datetime
import calendar
import textwrap

from ._calculations import haversine

class Hurdat2:
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
            # result = self.rank_seasons(
            result = rank_seasons(
                self,
                quantity,
                stattr,
                year1,
                year2,
                descending,
                info=kw.get("info")
            )
            return result

        rseason = {}
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
        for season in [
            s for s in self.season.values() \
            if year1 <= s.year <= year2 \
            or (
                kw.get("info") is not None \
                and s.year == kw.get("info")
            )
        ]:
            yr = season.year
            rseason[yr] = dict(
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
                # rankinfo = self.rank_seasons_thru(
                rankinfo = self.new_rank_seasons(
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

class Null: pass