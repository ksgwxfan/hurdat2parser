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
import textwrap
import datetime
import calendar
import collections
import secrets
import operator

from . import _gis

class Hurdat2Calculations:

    def random(self):
        """
        Returns a random <TropicalCyclone> object from the database.
        """
        return secrets.choice(list(self.tc.values()))

    def rank_seasons(self, quantity, stattr, year1=None, year2=None, descending=True, **kw):
        """Rank and compare full tropical cyclone seasons to one another.

        Required Arguments:
            quantity: how long of a list of ranks do you want; an integer.
            stattr: the storm attribute that you'd like to rank seasons by.
            
                * Storm Attributes: 
                    "tracks", "landfall_TC", "TSreach", "HUreach", "MHUreach",
                    "track_distance_TC", "ACE", "track_distance_TS", "HDP",
                    "track_distance_HU", "MHDP", "track_distance_MHU"

                * Note: Other <<Season>> attributes are valid to rank by, but their quantities will not be visible in the ranking output.

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
            method ("D"): what ranking method to use. "D" (the default) will
                report dense (quantity-based) ranks, while "C" will report
                competition-method ranks.

                * (D)ense: rank-placement will be based on their quantities.
                    For example, if a season has the 3rd highest quantity of a
                    value, its rank will be 3, regardless of the number of
                    seasons that rank higher.
                * (C)ompetiton: rank-placement will be based on the season
                    compared to other seasons. For example, though a season may
                    have the 3rd highest value, its rank could be 28th because
                    there could be 27 seasons that have a higher value. This is
                    common in sports (golf as a prime example).

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
        from .__init__ import Season, TropicalCyclone

        class DerivedTropicalCyclone(TropicalCyclone):
            @property
            def track_distance(self):
                """Returns the distance (in nmi) traversed by the system, regardless of
                status (whether or not the system is designated as a tropical cyclone).
                """
                return sum(
                    haversine(en.location, en.next_entry.location)
                    for en in self.entry
                    if en.next_entry is not None
                )

            @property
            def track_distance_TC(self):
                """The distance (in nmi) trekked by the system when a designated
                tropical cyclone (status as a tropical or sub-tropical depression, a
                tropical or sub-tropical storm, or a hurricane).
                """
                return sum(
                    haversine(en.location, en.next_entry.location)
                    for en in self.entry
                    if en.next_entry is not None
                    and en.is_TC
                )

            @property
            def track_distance_TS(self):
                """The distance (in nmi) trekked by the system while a tropical storm
                or hurricane.
                """
                return sum(
                    haversine(en.location, en.next_entry.location)
                    for en in self.entry
                    if en.next_entry is not None
                    and en.status in ["SS", "TS", "HU"]
                )

            @property
            def track_distance_HU(self):
                """The distance (in nmi) trekked by the system while a hurricane."""
                return sum(
                    haversine(en.location, en.next_entry.location)
                    for en in self.entry
                    if en.next_entry is not None
                    and en.status == "HU"
                )

            @property
            def track_distance_MHU(self):
                """The distance (in nmi) trekked by the system while a major
                hurricane.
                """
                return sum(
                    haversine(en.location, en.next_entry.location)
                    for en in self.entry
                    if en.next_entry is not None
                    and en.wind >= 96
                    and en.status == "HU"
                )

        year1 = self.record_range[0] if year1 is None \
            or year1 < self.record_range[0] else year1
        year2 = self.record_range[1] if year2 is None \
            or year2 > self.record_range[1] else year2

        rank_method = str(kw.get("method", "D"))
        if len(rank_method) > 0 and rank_method[0] in ["C", "c"]:
            rank_method = "C"
        else:
            rank_method = "D"

        # Partial-Season Bookened Month, Day Tuples
        start = kw.get("start", (1,1))
        thru = kw.get("thru", (12,31))

        # error if thru or start are not list/tuples
        if type(thru) not in [list,tuple]:
            return print("OOPS! Ensure thru is a list or tuple of (month,day)")
        if type(start) not in [list,tuple]:
            return print("OOPS! Ensure start is a list or tuple of (month,day)")

        start = tuple(start)
        thru = tuple(thru)

        partyear = False

        rseason = {}

        infoseason = None
        valid_seasons = [s for s in self.season.values() if year1 <= s.year <= year2]

        # account for a non-existent season being requested by stats method
        if all([
            kw.get("info") is not None,
            kw.get("info") not in self.season
        ]):
            infoseason = Season(kw.get("info"), self)
            valid_seasons.append(infoseason)

        # Full year being asked for
        if start == (1,1) and thru == (12,31):
            # List seasons sorted by stattr
            sorted_seasons = sorted(
                valid_seasons,
                key=lambda czen: getattr(czen, stattr),
                reverse = descending
            )
            # Values sorted
            ranks = sorted(
                [
                    getattr(s, stattr)
                    for s in sorted_seasons
                    if descending is False
                    or (
                        getattr(s, stattr) > 0
                        and kw.get("info") is None
                    ) or kw.get("info") is not None
                ],
                reverse = descending
            )
        # partial year
        else:
            partyear = True
            rseason = {}
            for season in [
                s for s in self.season.values() \
                if year1 <= s.year <= year2 \
                or (
                    kw.get("info") is not None \
                    and s.year == kw.get("info")
                )
            ]:
                if season.year not in rseason:
                    rseason[season.year] = Season(season.year, self)
                for tcyc in season.tc.values():
                    for en in tcyc.entry:
                        if start <= en.month_day_tuple <= thru:
                            # ensure cyclone exists in rseason
                            if tcyc.atcfid not in rseason[season.year].tc:
                                rseason[season.year].tc[tcyc.atcfid] = DerivedTropicalCyclone(
                                    tcyc.atcfid,
                                    tcyc.name,
                                    rseason[season.year],
                                    self
                                )
                            # append the entry
                            # BUT !!!! What about handling of Track Distance related vars?
                            # if INDX >= 1 and start <= tc.entry[INDX-1].month_day_tuple <= thru ????
                            rseason[season.year].tc[tcyc.atcfid]._entry.append(en)
            # append missing (info) season to rseason so next command will work
            if kw.get("info") and kw.get("info") not in rseason:
                rseason[kw.get("info")] = Season(kw.get("info"), self)
            sorted_seasons = sorted(
                valid_seasons,
                key=lambda s: getattr(rseason[s.year], stattr),
                reverse = descending
            )
            # Values sorted
            ranks = sorted(
                [
                    getattr(rseason[s.year], stattr)
                    for s in sorted_seasons
                    if descending is False
                    or (
                        getattr(rseason[s.year], stattr) > 0
                        and kw.get("info") is None
                    ) or kw.get("info") is not None
                ],
                reverse = descending
            )
            # return rseason

        # List that holds printed quantities
        printedqty = []

        # RETURN if info method called this method
        if kw.get("info", None) is not None:
            stat_season_obj = infoseason if infoseason is not None \
                else rseason[kw.get("info")] if partyear \
                else self.season[kw.get("info")]
            if (year1 <= kw["info"] <= year2) is False:
                ranks = sorted(
                    set(ranks + [getattr(stat_season_obj, stattr)]),
                    reverse = descending
                )

            return {
                "seasonvalu": getattr(stat_season_obj, stattr),
                "rank": sorted(set(ranks), reverse=descending).index(getattr(stat_season_obj, stattr)) + 1,
                "tied": len([
                    "tie" for season in (
                        rseason.values() if partyear else self.season.values()
                    ) if getattr(season, stattr) == getattr(stat_season_obj, stattr)
                ]) - 1,
                "outof": len(sorted(set(ranks),reverse=descending)),
                # the .index() method works because it finds the index of the first inst.
                "golf_rank": ranks.index(getattr(stat_season_obj, stattr)) + 1,
                "golf_outof": len(ranks) - len([valu for valu in ranks if valu == ranks[-1]]) + 1,
            }

        print("")
        print("TOP {} SEASONS RANKED BY {}{}".format(
                quantity,
                stattr.upper(),
                "" if partyear is False 
                else ", {}{}".format(
                    "from {} {}".format(
                        calendar.month_abbr[start[0]], start[1]
                    ) if start != (1,1) else "",
                    "{}through {} {}".format(
                        " " if start != (1,1) else "",
                        calendar.month_abbr[thru[0]]
                            if thru != (12,31) else "the End of",
                        thru[1]
                            if thru != (12,31) else "Season"
                    )
                ),
            ).center(79)
        )

        print("{}{}".format(
            str(self.basin()),
            ", {}-{}".format(year1, year2)
        ).center(79))

        print(
            "{} Rankings".format(
                "Dense" if rank_method == "D" else "Competition"
            ).center(79)
        )
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

        # set up ranks for default dense mode (1-2-3-4)
        if rank_method == "D":
            ranks = sorted(set(ranks), reverse=descending)

        for season in sorted_seasons:
            # only print stats if ordering by least-to-greatest
            #    or if greatest-to-least at stat != 0
            if descending is False or (
                partyear is False and getattr(season, stattr) != 0
                or
                partyear is True and getattr(rseason[season.year], stattr) != 0
            ):
                season_obj = rseason[season.year] if partyear else season

                current_rank = ranks.index(getattr(season_obj, stattr)) + 1 \
                    if ranks.index(getattr(season_obj, stattr)) + 1 \
                    not in printedqty else None
                if current_rank is not None and current_rank > quantity:
                    break

                print("{:>3}{:1}  {:4}  {:^6}  {:^4}  {:^4}  {:^4} {:^3}  {:>7.1f}  {:>{ACELEN}f}  {:>{ACELEN}f}  {:>{ACELEN}f}".format(
                    current_rank if current_rank is not None else "",
                    "." if current_rank is not None else "",
                    season.year,
                    season_obj.tracks,
                    season_obj.landfall_TC,
                    season_obj.TSreach,
                    season_obj.HUreach,
                    season_obj.MHUreach,
                    season_obj.track_distance_TC,
                    season_obj.track_distance_TS if "track_distance" in stattr else season_obj.ACE * math.pow(10,-4),
                    season_obj.track_distance_HU if "track_distance" in stattr else season_obj.HDP * math.pow(10,-4),
                    season_obj.track_distance_MHU if "track_distance" in stattr else season_obj.MHDP * math.pow(10,-4),
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

    def _season_stats(self, seasonreq, year1, year2, rstart, rthru, width, **kw):
        """
        Handler for <Season>.stats calls.
        """
        class SuperList(list):
            def __init__(self, *args):
                self.printed = []
                super().__init__(*args)

            def continue_print(self):
                print_queue = []
                for indx, line in enumerate(self):
                    if indx not in self.printed:
                        print_queue.append(line)
                        self.printed.append(indx)
                print("\n".join(print_queue))

            def reset_printed(self):
                self.printed = []

        instruction = kw.get("instruction", print)

        strlist = SuperList()
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
        strlist.append(
            "* Reported ranks are Dense (value-based) "
            "and Competition (if different)",
        )
        strlist.append("-" * width)
        if instruction == print: strlist.continue_print()
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
            if "landfall" not in attr or (
                "landfall" in attr and all(
                    1971 <= y <= 1990 for y in range(year1, year2)
                ) is False
            ):
                rankinfo = self.rank_seasons(
                    1337,
                    attr,
                    year1,
                    year2,
                    start = rstart,
                    thru = rthru,
                    descending=kw.get("descending", True),
                    info=yr
                )
                strlist.append('{:<35}Ranks: {:>{LEN}}{}{}'.format(
                    "* {}: {}{}   ".format(
                        label,
                        "{:.1f}".format(rankinfo["seasonvalu"])
                            if "distance" in attr
                            else "{:.1f}".format(rankinfo["seasonvalu"] * pow(10,-4))
                            if attr in ["ACE", "HDP", "MHDP"]
                            else rankinfo["seasonvalu"],
                        " nmi"
                            if "track_distance" in attr
                            else " * 10^4 kt^2"
                            if attr in ["ACE", "HDP", "MHDP"]
                            else "",
                    ),
                    "{}/{}".format(
                        rankinfo["rank"],
                        rankinfo["outof"],
                    ),
                    " :: {:>{LEN}}".format(
                        "{}/{}".format(
                            rankinfo["golf_rank"],
                            rankinfo["golf_outof"],
                        ),
                        LEN = len(str(year2-year1+1)) * 2 + 1,
                    ) if rankinfo["rank"] != rankinfo["golf_rank"]
                      or rankinfo["outof"] != rankinfo["golf_outof"]
                      else "",
                    " (tied w/{} season{})".format(
                        rankinfo["tied"],
                        "s" if rankinfo["tied"] >= 2 else ""
                    ) if rankinfo["tied"] > 0 else "",
                    LEN = len(str(year2-year1+1)) * 2 + 1,
                ))
            if instruction == print: strlist.continue_print()
        if instruction == print: strlist.continue_print()
        if instruction != print:
            return "\n".join(strlist)
        # if instruction == print:
            # print("\n".join(strlist))
        # else:
            # return "\n".join(strlist)

class SeasonCalculations:

    @property
    def start_date_entry(self):
        """The <<TCRecordEntry>> of the start of the season."""
        return self.tc_entries[0]

    @property
    def start_date(self):
        """The <<datetime>> of the start of the season."""
        return self.start_date_entry.entrytime

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
        # provide for seasons that extend into the following year
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
    def bounding_box(self):
        """The bounding box enclosing all of the cyclones <TCRecordEntry>s."""
        return _gis.BoundingBox(
            _gis.Coordinate(
                min(en.lon for en in self.entry),
                max(en.lat for en in self.entry)
            ),
            _gis.Coordinate(
                max(en.lon for en in self.entry),
                min(en.lat for en in self.entry)
            )
        )

    @property
    def bounding_box_TC(self):
        """
        The bounding box enclosing all <TCRecordEntry>s where the system was
        designated as a tropical cyclone
        """
        return _gis.BoundingBox(
            _gis.Coordinate(
                min(en.lon for en in self.tc_entries),
                max(en.lat for en in self.tc_entries)
            ),
            _gis.Coordinate(
                max(en.lon for en in self.tc_entries),
                min(en.lat for en in self.tc_entries)
            )
        )

    @staticmethod
    def test(point, point2):
        # the segment to inspect if the track crosses
        segbb = _gis.BoundingBox(
            _gis.Coordinate(*point),
            _gis.Coordinate(*point2)
        )
        # find the angle that is perpendicular to the segment
        perpendicular = direction(
            segbb.p1.lat,
            segbb.p1.lon,
            segbb.p2.lat,
            segbb.p2.lon,
            right_hand_rule=True
        )
        p2 = abs(segbb.theta-180)
        return [tuple(point), (round(point2[0],5), round(point2[1],5)), segbb.theta, segbb.heading, perpendicular, p2]


    def crosses(self, *reference, direction_range=None, landfall=False, category=None, is_TC=False):
        """
        Returns whether or not the track of this system intersects a referenced
        list of tupled coordinates (longitude, latitude). Optional
        discriminators are detailed below.

        Arguments:
            reference: the list of coordinates in (lon, lat) tuples. It is
                recommended to use the <Hurdat2>.from_map() method to formulate
                the coordinate list. For convenience, there are coastline
                coordinate lists that are part of the <Hurdat2> object. See
                README about those.

        Default Keyword Arguments:
            direction_range (None): an optional list/tuple of direction range
                only matching if the storm crosses the coordinates while its
                direction is within the given range.

                Direction Reference:
                    0 or 360: North
                          90: East
                         180: South
                         270: West

                Examples:
                             Tuple       Scope
                             -----       -----
                    North: (316, 44)     Broad
                           (346, 14)    Narrow
                     East: (46, 134)     Broad
                           (75, 105)    Narrow
                    South: (136, 224)    Broad
                           (165, 205)   Narrow
                     West: (226, 314)    Broad
                           (255, 285)   Narrow

            landfall (False): if True, it assesses crossings from a particular
                side of segments of the reference. Think of this as a "right
                hand rule", being perpendicular to a reference segment. So the
                referenced list must be prepared using this in mind. As you
                sketch around the landmass, envision an arrow pointing to the
                right of the segment, with respect to its forward direction.

                Example: To find systems that made landfall along the Carolina
                    coasts, the reference must be compiled starting from the
                    northern-most tip of the Outer Banks of North Carolina,
                    tracing generally southwestward thru South Carolina.
            category (None): represents an optional saffir-simpson (ss)
                equivalent integer that will further discriminate whether a
                cyclone crossed while its ss scale value was >= the category
                given. Of note, this does NOT discriminate via the cyclone's
                status at the time of crossing. See the is_TC kw for more info.
            is_TC (False): if True, this will test if the system was a tropical
                cyclone at the time of crossing (status of SD, SS, TD, TS, or
                HU). It is recommended to use this in conjunction with the
                category kw, as the saffir-simpson rating is strictly wind-
                based.
        """

        if len(reference) == 1: # if a list of tupled coords are passed (like from_map method)
            reference = [(x, y) for x, y in reference[0]]
        if len(reference) <= 1:
            raise ValueError(
                "the list `reference` must contain 2 or more coordinate pairs "
                "for comparison"
            )

        # if category is given, there is no need to check if the storm
        #   never reached the magnitude inquired
        if category is not None and saffir_simpson_scale(self.maxwind) < category:
            return False

        # if bounding boxes never cross, no need to check
        refbb = _gis.BoundingBox(
            _gis.Coordinate(
                min(lon for lon, lat in reference),
                max(lat for lon, lat in reference)
            ),
            _gis.Coordinate(
                max(lon for lon, lat in reference),
                min(lat for lon, lat in reference)
            )
        )

        # no need to check if no track points are in the reference bounding box
        # if all([en.location_rev not in refbb for en in self.entry]):
            # return False

        # iterate over each point
        for indx, point in enumerate(reference):
            try:
                point2 = reference[indx+1]
            except:
                # no more segments to test
                return False
            if point2 == point:
                # skip if points are the same
                continue

            # the segment to inspect if the track crosses
            segbb = _gis.BoundingBox(
                _gis.Coordinate(*point),
                _gis.Coordinate(*point2)
            )

            # No need to check (so skip) if the reference segment doesn't even
            #   intersect the track bounding box
            if not segbb.intersects(self.bounding_box):
                continue

            # find the angle that is perpendicular to the segment
            perpendicular = direction(
                segbb.p1.lat,
                segbb.p1.lon,
                segbb.p2.lat,
                segbb.p2.lon,
                right_hand_rule=True
            )
            # perpendicular = math.fabs(segbb.theta-180)

            # iterate over segments made by the cyclone's entries
            # for entry in self.entry[1:]:
            for entry in [
                EN for EN in self.entry[1:]
                if (
                    category is None
                    or EN.previous_entry.saffir_simpson >= category
                ) and (
                    not is_TC
                    or EN.previous_entry.is_TC
                ) and (
                        # EN.location_rev in refbb
                        # or EN.previous_entry.location_rev in refbb
                    # )
                    EN.previous_entry.bounding_box.intersects(segbb)
                )
            ]:
                # the track segment to compare/inspect
                enbb = entry.previous_entry.bounding_box

                # determine if the entry's direction lies within the requested
                #  range of angles (used for landfall testing)
                angle_is_valid = is_angle_bounded(
                    entry.direction(),
                    perpendicular
                )

                # parallel test - if slopes are the same they will never cross
                # and conditionally tests if cyclone's direction is within a requested range
                if segbb.slope != enbb.slope and (
                    direction_range is None
                    or direction_range[0] <= entry.direction() <= direction_range[1]
                ):
                    # ilon = longitude intersection (x intersection)
                    #   put 2 equations equal to one another; solve for x
                    #   x = (b2 - b1) / (m1 - m2)
                    try:
                        ilon = (enbb.b - segbb.b) / (segbb.slope - enbb.slope)
                        # if the x-intercept is bounded by the e/w points of each segment,
                        #   PRESENCE HERE MEANS CROSSING HAS OCCURRED
                        if enbb.w <= ilon <= enbb.e and segbb.w <= ilon <= segbb.e:
                            # if testing for "landfall" (entry crosses from a
                            #    compatible direction (to negate crossing the
                            #    reference when going from land to sea)
                            if landfall is True:
                                # tests the crossing angle if it falls within a
                                #   180deg sweep of the perpendicular angle of
                                #   the 'land' segment
                                if angle_is_valid is True and (
                                    category is None
                                    or entry.previous_entry.saffir_simpson >= category
                                ):
                                    return True
                            # No landfall but >= category is requested
                            elif category is not None:
                                if entry.previous_entry.saffir_simpson >= category:
                                    return True
                            # otherwise, the crossing has been guaranteed
                            else:
                                return True
                    # This block will run if one of the segments fail the
                    #   vertical line test (segment runs north/south)
                    except Exception as e:
                        # solve the line formula for segbb with the enbb x value
                        #  and test if that value lies within the n/s scope of enbb
                        #  and if the enbb x value is withing the e/w scope of segbb
                        if enbb.isvertical and (
                            enbb.s <= segbb.slope * enbb.p1.x + segbb.b <= enbb.n
                            and segbb.w <= enbb.p1.x <= segbb.e
                        # solve the line formula for enbb with the segbb lon. value
                        #  and test if that value lies within the n/s scope of segbb
                        #  and if the segbb lon value is withing the e/w scope of enbb
                        ) or segbb.isvertical and (
                            segbb.s <= enbb.slope * segbb.p1.x + enbb.b <= segbb.n
                            and enbb.w <= segbb.p1.x <= enbb.e
                        ):
                            # PRESENCE HERE MEANS CROSSING GUARANTEED
                            # landfall test
                            if landfall is True:
                                if angle_is_valid is True and (
                                    category is None
                                    or entry.previous_entry.saffir_simpson >= category
                                ):
                                    return True
                            # No landfall but >= category is requested
                            elif category is not None:
                                if entry.previous_entry.saffir_simpson >= category:
                                    return True
                            # otherwise, the crossing has been guaranteed
                            else:
                                return True
        return False

    @property
    def start_date_entry(self):
        """The <TCRecordEntry> of the birth of the cyclone."""
        return self.tc_entries[0] if len(self.tc_entries) > 0 else None

    @property
    def start_date(self):
        """The <<datetime>> of the birth of the tropical cyclone."""
        return self.start_date_entry.entrytime \
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
    def bounding_box(self):
        """
        The bounding box (or really, segment) defined by the point of this
        entry and the next entry (if applicable).
        """

        if self.next_entry is not None:
            return _gis.BoundingBox(
                _gis.Coordinate(self.lon, self.lat),
                _gis.Coordinate(self.next_entry.lon, self.next_entry.lat),
            )
        else:
            return None

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

    def direction(self, cardinal=False, right_hand_rule=False):
        """Returns the heading (in degrees) of the tropical cyclone at the time
        of the <TCRecordEntry>.

        This is calculated using this and the previous entry locations.

        Default Argument
        ----------------
            cardinal (False): if True, it will return an accurate cardinal
                direction abbreviation (ex: 'NNW' == North-Northwest) instead
                of degrees.
            right_hand_rule (False): if True, it will return the direction
                normal or perpendicular to the heading following the right-hand
                rule.

        Of note, the first entry (index of 0) of any tropical cyclone will not
        have any associated direction because there is no previous entry to
        compare it with.

        For reference:
              Degrees           Direction
            ----------      -------------------
              0 //  45      North // Northeast
             90 // 135      East  // Southeast
            180 // 225      South // Southwest
            270 // 315      West  // Northwest
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

            if right_hand_rule:
                deg_dir += 90
            if cardinal is True:
                return cardinal_direction(
                    deg_dir + (360 if deg_dir < 0 else 0)
                )
            else:
                return deg_dir + (360 if deg_dir < 0 else 0) 
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
        """
        Returns the saffir-simpson scale rating of the tropical cyclone. This
        is solely based upon the maximum sustained wind value. If at-least
        hurricane-strength, this will return a category between 1 and 5. For Non-
        hurricane strength storms will return 0 if tropical storm strength or
        -1 for depression strength or less. 0 or -1 does not appear on the
        saffir-simpson scale but were included in this method for continuity
        and distinguishing between those weaker systems.
        """
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
        """Returns the average extent of at-least 50kt winds."""
        return statistics.mean(self.extent_TS50)

    @property
    def areal_extent_TS50(self):
        """Return the instantaneous maximum 50kt+ wind (TS50) areal expanse (in
        nmi^2) covered by the storm.
        
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
    """Returns the equivalent Saffir-Simpson scale rating, based on wind-speed
    in knots.

    This is a very common scale used to generalize tropical cyclone intensity.
    Though not officially part of the scale, cyclones that have Tropical Storm
    speeds will return 0 while even-weaker storms will return -1.

    Example: saffir_simpson_scale(100) --> 3 (implying category 3).
    """
    if 34 <= spd < 64:     return 0
    elif 64 <= spd < 83:   return 1
    elif 83 <= spd < 96:   return 2
    elif 96 <= spd < 113:  return 3
    elif 113 <= spd < 137: return 4
    elif spd >= 137:   return 5
    else: return -1

def distance_from_coordinates(lat, lon, distance, direction):
    direction = direction.upper()
    latr = math.radians(lat)
    lonr = math.radians(lon)
    if distance == None:
        distance = 0
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

def haversine(startpos, endpos, gis=False):
    """Returns the distance (in nmi) between two tupled GPS coordinates.

    Args:
        startpos: the starting gps-coordinate point; in tuple form of 
            (latitude, longitude) unless gis kw is True. Both need to be an int
            or float.
        endpos: the ending gps-coordinate point; in tuple form of (latitude,
            longitude) unless gis kw is Ture. Both need to be an int or float.

    Default Args:
        gis (False): the function wants coordinates in (lat, lon) format. If this kw is True, then it expects (lon, lat) order.

    The formula used was found on Wikipedia
        (https://en.wikipedia.org/wiki/Haversine_formula).
    """
    lat1 = math.radians(startpos[0 if gis is False else 1])
    lon1 = math.radians(startpos[1 if gis is False else 0])
    lat2 = math.radians(endpos[0 if gis is False else 1])
    lon2 = math.radians(endpos[1 if gis is False else 0])
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

def direction(lat1, lon1, lat2, lon2, cardinal=False, right_hand_rule=False):
    """
    Return the navigational heading (0deg = North) between two points (going
    from point 1 towards point 2.

    Arguments
    ---------
        lat1 = latitude of point 1
        lon1 = longitude of point 1
        lat2 = latitude of point 2
        lon2 = longitude of point 2

    Default Arguments
    -----------------
        cardinal (False): if True, this will return a string representation of
            the heading (its abbreviation actually).
            Examples:
                0 -> "N"
                45 -> "NE"
                225 -> "SW"
        right_hand_rule (False): if True, the returned value will be rotated 90
            degrees "to the right" of the heading.

    This is essentially a mirror function of <TCEntryCalculations>.direction so
    it could be accessible to other functions/methods in this file.
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
    if right_hand_rule:
        deg_dir = deg_dir + 90
    if cardinal is True:
        return cardinal_direction(
            deg_dir + (360 if deg_dir < 0 else 0)
        )
    else:
        return deg_dir + (360 if deg_dir < 0 else 0) 

def is_angle_bounded(deg, reference, scope=180):
    """
    Tests (and returns) whether or not an angle falls within a certain range
    that is centered at a reference angle.

    Args:
        deg = the angle to be tested
        reference = the angle that will be the center of the determined range

    Default Keyword Arguments:
        scope (180): the angle spectrum centered at the reference angle from
            which the test will be made. For example:

                 Deg   Reference Angle   Scope      Angle Range      Result
                ----   ---------------   -----   ----------------    ------
                  70        85            180       (>=355, <=175)    True
                 200        175            40     (>=155, <=195)      False
                 325        350            60      (>=320, <=20)      True
    """
    _min = reference - scope/2
    _max = reference + scope/2

    return _min < deg < _max \
        if not deg < _min < _max \
        and not _min < _max < deg \
        else _min < deg + 360 < _max \
        if not _min < _max < deg \
        else _min < deg - 360 < _max

def operator_map(logic):
    opmap = {
        "<"  : operator.lt,
        "<=" : operator.le,
        "==" : operator.eq,
        "!=" : operator.ne,
        ">=" : operator.ge,
        ">"  : operator.gt,
    }
    return opmap[logic]
























