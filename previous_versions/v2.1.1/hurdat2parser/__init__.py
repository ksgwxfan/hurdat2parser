"""hurdat2parser v2.1.1

https://github.com/ksgwxfan/hurdat2parser

hurdat2parser v2.x is an object-oriented approach to viewing tropical cyclone
data that is contained in a widely-used and updated dataset, HURDAT2
(https://www.nhc.noaa.gov/data/#hurdat). The purpose of this module is to
provide a quick way to investigate HURDAT2 data. Its aim is to make it easier
to access historical hurricane data.

To get started:
1) Install: >>> pip install hurdat2parser
2) Download HURDAT2 Data: https://www.nhc.noaa.gov/data/#hurdat
3) In python, import and invoke call using the hurdat2 file you downloaded (the
    following is just an example):

    >>> import hurdat2parser
    >>> atl = hurdat2parser.Hurdat2("path_to_hurdat2.txt")

hurdat2parser, Copyright (c) 2019-2022, Kyle Gentry (KyleSGentry@outlook.com)
License: MIT
ksgwxfan.github.io
echotops.blogspot.com
"""

import calendar
import difflib
import math
import re
import itertools
import datetime
import collections

from . import _aliases, _calculations, _reports

class Hurdat2(_aliases.Hurdat2Aliases, _calculations.Hurdat2Calculations, _reports.Hurdat2Reports):

    BASIN_DICT = dict(
            AL = "North Atlantic",
            NA = "North Atlantic",
            SL = "South Atlantic",
            SA = "South Atlantic",
            EP = "East Pacific",
            CP = "Central Pacific",
            WP = "West Pacific",
            SH = "Southern Hemisphere",
            IO = "North Indian",
            NI = "North Indian",
            SI = "South Indian",
            SP = "South Pacific",
            AS = "Arabian Sea",
            BB = "Bay of Bengal",
        )

    def __init__(self, hurdat2file):
        """Initializes a new Hurdat2 object.
        
        Arguments:
            hurdat2file (str): file-path of the hurdat2 record (a text file)
        """
        self._tc = {}        # Dictionary containing all hurdat2 storm data
        self._season = {}    # Dictionary containing all relevant season data
        self._rank = {"tc":{}, "season":{}}
        # used to prevent multiple loads of the same file to the same object
        self._filesappended = []
        self._build_tc_dictionary(hurdat2file)  # Call to build/analyze the hurdat2 file

    def __repr__(self):
        return "<{} object - {}: {}-{} - at 0x{}>".format(
            re.search(r"'(.*)'", str(type(self)))[1],
            self.basin(),
            *self.record_range,
            str(id(self)).upper().zfill(16)
        )

    def __len__(self):
        """Returns the number of tracked systems in the Hurdat2 record"""
        return len(self.tc)

    def __str__(self):
        return "{}, {}".format(
            self.basin(),
            "{}-{}".format(*self.record_range)
        )

    def __getitem__(self, s):
        """Indexing handling here is designed more of as a 'switchboard
        operator.' It handles multiple types and interprets their passage and
        routes them to the proper methods, providing shortcuts of sorts.
        
        Accepted types:
            slice: calls the multi_season_info method, using the slice's start
                and stop attributes for it. In an effort to preserve the
                typical implementation of slice, the end year is decremented by
                1. So [2000:2005] would include stats from 2000 thru 2004;
                excluding 2005. For different behavior, see the next entry, for
                tuples.
            tuple or list: returns the Season(1), TropicalCyclone(2), or
                TCRecordEntry(3) desired, depending on length of tuple passed.
            int: grabs the _season object matching the year passed.
            str: inspects the string and returns either a storm object, a
                season object, or a call to the name-search function
        """
        # multi-season info
        if type(s) is slice:
            st = s.start
            en = s.stop-1
            return self.multi_season_info(st, en)
        # use items of an iterable as season, tcnumber, and entry index
        elif type(s) in [tuple, list]:
            if len(s) == 1:
                return self[s[0]]
            elif len(s) >= 2:
                return self[s[0]][s[1:]]
        # Season passed as int
        elif type(s) is int:
            return self.season[s]
        # String based
        elif type(s) == str:
            # ATCFID Request
            if re.search(r"^[A-Z]{2}[0-9]{6}.*", str(s), flags=re.I):
                return self.tc[s.upper()[:8]]
            # Season Request
            elif s.isnumeric():
                return self.season[int(s[:4])]
            # Name Search implied (will return the last storm so-named)
            else:
                return self.storm_name_search(s, False, True if "_" in s else False)
        # try handling all other types by converting to str then search by name
        else:
            return self.storm_name_search(str(s), False)

    def _build_tc_dictionary(self, hurdat2file):
        """Populate the Hurdat2 object with data from a hurdat2 file.

        Arguments:
            hurdat2file: the file-path of the hurdat2 file
        """
        if hurdat2file in self.filesappended:
            return print("OOPS! That file has already been read-in to this Hurdat2 object.")
        self.filesappended.append(hurdat2file)
        with open(hurdat2file) as h:
            # for line in h.readlines():
                # lineparsed = [each.strip() for each in line.strip("\n").split(",")]
            for line in h.read().splitlines():
                lineparsed = re.split(r", *", re.sub(r", *$", "", line))
                # above definition will leave a trailing comma at the end of e
                lineparsed[-1] = lineparsed[-1].strip(",")
                # New Storm
                if re.search(r"^[A-Z]{2}\d{6}",lineparsed[0]):
                    atcfid = lineparsed[0]
                    tcyr = int(atcfid[4:])
                    # Create Season
                    if tcyr not in self.season:
                        self.season[tcyr] = Season(tcyr, self)
                    # Create TropicalCyclone
                    self.tc[atcfid] = TropicalCyclone(
                        atcfid,
                        lineparsed[1],
                        self.season[tcyr],
                        self
                    )
                    # Add storm to that particular season
                    self.season[tcyr].tc[atcfid] = self.tc[atcfid]
                # TCRecordEntry for storm indicated
                else:
                    self.tc[atcfid].entry.append(
                        TCRecordEntry(
                            lineparsed.copy(),
                            self.tc[atcfid],
                            self.season[tcyr],
                            self
                        )
                    )

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

        # for yr1, yr2 in [(y, y+climatology-1) \
                # for y in range(1801, year2, increment) \
                # if year1 <= y <= year2 \
                # and year1 <= y+climatology-1 <= year2]:
            # climo[yr1, yr2] = Era(
                # (yr1, yr2),
                # sum(self.season[s].tracks for s in range(yr1, yr2+1)),
                # sum(self.season[s].landfalls for s in range(yr1, yr2+1)),
                # sum(self.season[s].landfall_TC for s in range(yr1, yr2+1)),
                # sum(self.season[s].landfall_TD for s in range(yr1, yr2+1)),
                # sum(self.season[s].landfall_TS for s in range(yr1, yr2+1)),
                # sum(self.season[s].landfall_HU for s in range(yr1, yr2+1)),
                # sum(self.season[s].landfall_MHU for s in range(yr1, yr2+1)),
                # sum(self.season[s].TSreach for s in range(yr1, yr2+1)),
                # sum(self.season[s].TSonly for s in range(yr1, yr2+1)),
                # sum(self.season[s].HUreach for s in range(yr1, yr2+1)),
                # sum(self.season[s].HUonly for s in range(yr1, yr2+1)),
                # sum(self.season[s].MHUreach for s in range(yr1, yr2+1)),
                # sum(self.season[s].cat45reach for s in range(yr1, yr2+1)),
                # sum(self.season[s].cat5reach for s in range(yr1, yr2+1)),
                # sum(self.season[s].track_distance for s in range(yr1, yr2+1)),
                # sum(self.season[s].track_distance_TC for s in range(yr1, yr2+1)),
                # sum(self.season[s].track_distance_TS for s in range(yr1, yr2+1)),
                # sum(self.season[s].track_distance_HU for s in range(yr1, yr2+1)),
                # sum(self.season[s].track_distance_MHU for s in range(yr1, yr2+1)),
                # sum(self.season[s].ACE for s in range(yr1, yr2+1)),
                # sum(self.season[s].HDP for s in range(yr1, yr2+1)),
                # sum(self.season[s].MHDP for s in range(yr1, yr2+1))
            # )
        # # If this method was called by the output_climo method...
        # if "op" in climoparam:
            # return climo

        # # List of tropical-cyclones sorted by stattr
        # sorted_climo = sorted(
            # [era for era in climo.values()],
            # key=lambda era: getattr(era, stattr),
            # reverse = descending
        # )
        # # Values sorted
        # ranks = sorted(
            # set([
                # getattr(era, stattr) for era in sorted_climo \
                    # if descending is False \
                    # or getattr(era, stattr) > 0
            # ]),
            # reverse = descending
        # )[:quantity]
        # --------------------------------
        class Era(object):
            def __init__(self, **kw):
                self.__dict__.update(**kw)

        yrrange = range(year1, year2+1)
        clmt = Era(
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

    def storm_name_search(self, searchname, info=True, feeling_lucky=False):
        """Search the Hurdat2 object's records by storm name. Returns the
        matches info method or returns the matching object itself.

        Required Argument:
            searchname: the storm name to search

        Default Arguments:
            info = True: if True, the method will return the info method of the
                chosen search result. Otherwise it will simply return the
                object (used in __getitem__)
            feeling_lucky = False: if True, and if there are multiple search
                results, it will return the newest one. This kw is employed
                by a 'global' search for a storm by name. This is included due
                to the assumption that users, when operating on the entire
                Hurdat2 record, are inquiring about a particular storm that
                would now have a retired name, and as such, would be the 
                newest storm to be issued that identifying name.
                
        """
        searchname = searchname.upper()     # Capitalize the search term

        # Searching for a storm of a particular name; will return the most
        #   recent storm where a match was found in the name
        if feeling_lucky is True:
            searchname = searchname.replace("_", "")
            # 1st pass
            matchlist = [(TC, 1.0) for TC in self.tc.values() if searchname == TC.name]

            if len(matchlist) > 0:
                return matchlist[-1][0]
            # 2nd pass
            else:
                matchlist = sorted(
                    filter(
                        lambda tup: tup[1] >= 0.8,
                        [
                            (
                                TC,
                                difflib.SequenceMatcher(
                                    None,
                                    searchname,
                                    TC.name
                                ).quick_ratio()
                            ) for TC in self.tc.values() if TC.name[0] == searchname[0]
                        ]
                    ), key=lambda tup: tup[0].year, reverse=True
                )
            return matchlist[0][0]

        # All other searches
        # -----------------------------

        # 1st pass - Limit the search results to exact matches
        matchlist = [(TC, 1.0) for TC in self.tc.values() if searchname == TC.name]

        # 2nd pass - Limit the search results by requiring that
        #            the first is letter correct
        if len(matchlist) == 0:
            matchlist = sorted(
                filter(
                    lambda tup: tup[1] >= 0.8,
                    [
                        (
                            TC,
                            difflib.SequenceMatcher(
                                None,
                                searchname,
                                TC.name
                            ).quick_ratio()
                        ) for TC in self.tc.values() if TC.name[0] == searchname[0]
                    ]
                ), key=lambda tup: tup[1], reverse=True
            )
        #3rd pass - if necessary; if no match found
        if len(matchlist) == 0:
            matchlist = sorted(
                filter(
                    lambda tup: tup[1] >= 0.6,
                    [
                        (
                            TC,
                            difflib.SequenceMatcher(
                                None,
                                searchname,
                                TC.name
                            ).quick_ratio()
                        ) for TC in self.tc.values() if TC.name[0] == searchname[0]
                    ]
                ), key=lambda tup: tup[1], reverse=True
            )

        # No Matches Determined
        if len(matchlist) == 0:
            print("* No Matches Found for '{}'*".format(searchname))
            return None

        # If only one match found, return it!
        elif len(matchlist) == 1:
            # Manual Search call
            if info is True:
                return matchlist[0][0].info()
            # Indexing being attempted; return TropicalCyclone Object
            else:
                return matchlist[0][0]

        # Display a choice for multiple matches (up to the first 7)
        else:
            i = itertools.count(1)
            for tc, qratio in matchlist[:7]:
                print("{}. {:.1%} - {}: {}{}".format(
                    next(i),
                    qratio,
                    tc.atcfid,
                    "{} ".format(tc.status_highest) \
                        if tc.name != "UNNAMED" \
                        else "",
                    tc.name.title() if tc.name != "UNNAMED" else tc.name
                ))
            print("")
            while True:
                choice = input("Which storm are you inquiring about? ")
                if choice.isnumeric() and 1 <= int(choice) <= 7:
                    print("--------------------")
                    if info is True:
                        return matchlist[int(choice) - 1][0].info()
                    else:
                        return matchlist[int(choice) - 1][0]
                else:
                    print("* OOPS! Invalid Entry! Try again.")

    @staticmethod
    def coord_contains(testcoord, ux, lx):
        """Returns True or False whether the coordinates (testcoord) would be
        contained in a box defined by 'upper' coordinates (ux) and 'lower'
        coordinates (lx).
        """
        if lx[0] <= testcoord[0] <= ux[0] and ux[1] <= testcoord[1] <= lx[1]:
            return True
        else:
            return False

    def basin(self, season_obj=None):

        basin_id = list(set([
            tc.atcfid[:2] for tc in (self.tc.values() if season_obj is None else season_obj.tc.values())
        ]))
        basin_names = []
        try:
            basin_names = list(set([
                self.BASIN_DICT[basin] for basin in basin_id
            ]))
        except:
            pass
        # print(basin_id)
        if len(basin_names) > 0:
            return " / ".join(basin_names) \
                + " Basin{}".format("s" if len(basin_id) > 1 else "")
        else:
            return "Unknown Region"

    @property
    def record_range(self):
        """Returns a tuple containing the beginning and end seasons covered by
        the Hurdat2 object.
        """
        return (min(self.season), max(self.season))

class Season(_aliases.SeasonAliases, _calculations.SeasonCalculations, _reports.SeasonReports):
    """Represents a single hurricane season; represented by its year."""
    def __init__(self,yr,hd2obj):
        self._year = yr
        self._tc = {}
        self._hd2 = hd2obj

    def __repr__(self):
        return "<{} object - {} - {} - at 0x{}>".format(
            re.search(r"'(.*)'", str(type(self)))[1],
            self.year,
            self._hd2.basin(self),
            str(id(self)).upper().zfill(16)
        )

    def __len__(self):
        """Returns the number of tropical cyclones from a particular season."""
        return len(self.tc)

    def __getitem__(self, s):
        # Storm Number passed
        if type(s) == int:
            for atcfid, tc in self.tc.items():
                if re.search(
                    r"[A-Z][A-Z]{:0>2}\d\d\d\d".format(s),
                    atcfid
                ):
                    return tc
                
            # return self.tc[
                # list(self.tc.keys())[
                    # (s-1) if s > 0 else s
                # ]
            # ]
        # List/Tuple (storm number, tcrecord index)
        elif type(s) in [tuple, list]:
            if len(s) == 1:
                return self[s[0]]
            else:
                return self[s[0]][s[1]]
        elif type(s) == str:
            # ATCFID
            if re.search(r"^[A-Z]{2}\d{6}", s, flags=re.I):
                return self.tc[str(s).upper()]
            # Storm name / Starting first-letter
            else:
                num_name = {tc.atcfid : tc.name for tc in self.tc.values()}
                for atcfid, name in {tc.atcfid : tc.name for tc in self.tc.values()}.items():
                    if s.upper()[0] == name[0]:
                        return self.tc[atcfid]

    def stats(self, year1=None, year2=None, start=None, thru=None, width=70, **kw):
        """Returns a report of a host of stats from the season and their ranks 
        relative to compared seasons. It also fully supports partial season
        stats (like rank_seasons_thru).

        * Of note, this can be quite slow especially when comparing full
        seasons to the full record.

        Default Arguments (all are used strictly for comparison purposes):
            year1 (None): start year of the comparison.
            year2 (None): end year of the comparison.
            start (None): accepts a 2-member tuple representing month and day;
                the start month and day for the comparison.
            thru (None): accepts a 2-member tuple representing month and day;
                the end month and day for the comparison.
            width (70): used to control the width of the report

        Keyword Arguments:
            descending: bool used to determine sorting method of rank results 
                (defaults to True)

        Examples:
            atl[1984].stats() :: Return stat-report for the 1984 season.
            atl[2005].stats(1967) :: Return stat-report for 2005, compared to
                seasons since 1967 (satellite era). If year2 is not specified,
                the comparison would include all seasons beyond 1967, including
                those beyond 2005.
            atl[2020].stats(1967, start=(9,1)) :: Return a 2020 stat-report,
                compared to seasons since 1967, limited from September to the
                end of the year.
            atl[1981].stats(1971, 1990, thru=(6,30)) :: Return a 1981 report
                with comparisons to seasons between 1971 and 1990, limited to
                data before July.
        """
        # set bounds to years for comparison
        if year1 is None:
            year1 = self._hd2.record_range[0]
        if year2 is None:
            year2 = self._hd2.record_range[1]

        # set bound on calendar dates for comparison
        if start is None:
            start = (1,1)
        if thru is None:
            thru = (12,31)
        
        return self._hd2._season_stats(
            self.year,
            year1,
            year2,
            start,
            thru,
            width,
            descending=kw.get("descending", True)
        )

    def summary(self):
        """Returns a report detailing all individual systems/storms tracked
        during a particular season.
        """
        print("")
        print("{:-^67}".format(""))
        print("{:^67}".format(
            "Tropical Cyclone Summary for {}".format(self.year)
        ))
        try:
            print("{:^67}".format(self._hd2.basin(self)))
        except:
            pass
        print("{:-^67}".format(""))
        print("{:^67}".format(
            "Tropical Cyclones: {}  //  {} TS  //  {} HU ({} Major)".format(
                self.tracks,
                self.TSreach,
                self.HUreach,
                self.MHUreach
            )
        ))
        print("{:^67}".format(
            "ACE: {} * 10^4 kt^2; Track Distance (TC): {} nmi".format(
                "{:>6.3f}".format(self.ACE * math.pow(10,-4)),
                "{:>6.1f}".format(self.track_distance_TC)
            )
        ))
        print("{:-^67}".format(""))
        print(" {:^10} {:^8} {:^4} {:^4} {:^4}  {:^6}  {:^22}".format(
            "","","LAND","","","TC TRK","ENERGY INDICES"
        ))
        print(" {:^10} {:^8} {:^4} {:>4} {:>4}  {:^6}  {:^22}".format(
            "","","FALL","MIN","MAX","DSTNCE","x10^4 kt^2"
        ))
        print(" {:<10} {:^8} {:<4} {:^4} {:^4}  {:^6}  {:^6}  {:^6}  {:^6}".format(
            "NAME","ATCFID","QTY","MSLP","WIND","(nmi)","ACE","HDP","MHDP"
        ))
        print(" {:-^10} {:-^8} {:-^4} {:-^4} {:-^4}  {:-^6}  {:-^6}  {:-^6}  {:-^6}".format(
            "","","","","","","","",""
        ))
        for trop in self.tc:
            print(" {:<10} {:8} {:^4} {:>4} {:>4}  {:>6.1f}  {:^6}  {:^6}  {:^6}".format(
                self.tc[trop].name.title(),
                self.tc[trop].atcfid,
                self.tc[trop].landfalls,
                self.tc[trop].minmslp if self.tc[trop].minmslp != None else "N/A",
                self.tc[trop].maxwind if self.tc[trop].maxwind > 0 else "N/A",
                self.tc[trop].track_distance_TC,
                "{:>6.3f}".format(self.tc[trop].ACE * math.pow(10,-4)) if self.tc[trop].ACE > 0 else "--",
                "{:>6.3f}".format(self.tc[trop].HDP * math.pow(10,-4)) if self.tc[trop].HDP > 0 else "--",
                "{:>6.3f}".format(self.tc[trop].MHDP * math.pow(10,-4)) if self.tc[trop].MHDP > 0 else "--"
            ))
        print("")

    def hurdat2(self):
        """Prints a Hurdat2-formatted summary of the entire season."""
        for tc in self.tc.values():
            tc.hurdat2()


    @property
    def tracks(self):
        """Returns the total number of tropical cyclones from the season. It's
        the same as calling len(self). It's included for readability in other
        methods.
        """
        return len(self)

    @property
    def TDonly(self):
        """Returns the quantity of tropical cyclones occurring during the
        season that reached tropical depression designation (SD, TD) but never
        strengthened to become at least a tropical storm.
        """
        return self.tracks - self.TSreach

    @property
    def landfalls(self):
        """Returns the aggregate of all landfalls from the season made by
        tropical cyclones. Keep in mind TC's can make multiple landfalls
        """
        return sum([self.tc[trop].landfalls for trop in self.tc])

    @property
    def landfall_TC(self):
        """Returns the quantity of tropical cyclones during the season that
        recorded at least one landfall.
        """
        return len(["L" for trop in self.tc if self.tc[trop].landfalls > 0])

    @property
    def landfall_TD(self):
        """Returns the quantity of tropical cyclones during the season that
        recorded at least one landfall as a tropical depression (SD, TD).
        Exclusive of other categorized strengths.
        """
        return len(["L_TD" for trop in self.tc if self.tc[trop].landfall_TD is True])

    @property
    def landfall_TS(self):
        """Returns the quantity of tropical cyclones during the season that
        recorded at least one landfall as a tropical storm (SS, TS).

        Exclusive of other categorized strengths.
        """
        return len(["L_TS" for trop in self.tc if self.tc[trop].landfall_TS is True])

    @property
    def landfall_HU(self):
        """Returns the quantity of tropical cyclones during the season that
        recorded at least one landfall while designated a hurricane.

        This is inclusive of major-hurricane landfalls.
        """
        return len(["L_HU" for trop in self.tc if self.tc[trop].landfall_HU is True])

    @property
    def landfall_MHU(self):
        """Returns the quantity of tropical cyclones during the season that
        recorded at-least one landfall as a major hurricane (>= 96kts).
        """
        return len(["L_MHU" for trop in self.tc if self.tc[trop].landfall_MHU is True])

    @property
    def TSreach(self):
        """Returns the quantity of tropical cyclones during the season if they
        were objectively issued the status of at-least tropical storm (SS, TS,
        or HU) during their life span.
        """
        return len(["TS" for trop in self.tc if self.tc[trop].TSreach is True])

    @property
    def TSonly(self):
        """Returns the quantity of tropical cyclones occurring during the
        season that reached tropical storm designation (SS, TS) but never
        became a hurricane.
        """
        return self.TSreach - self.HUreach

    @property
    def HUreach(self):
        """Returns the quantity of tropical cyclones during the season if they
        were objectively issued the status of Hurricane (HU) during their life.

        This is inclusive of those hurricanes that would eventually reach
        major-hurricane status.
        """
        return len(["HU" for trop in self.tc if self.tc[trop].HUreach is True])

    @property
    def HUonly(self):
        """Returns the quantity of hurricanes that were only Category 1 or
        Category 2 hurricanes.

        *** THIS IS DIFFERENT *** from HUreach as it EXCLUDES category 3+
        hurricanes.
        """
        return self.HUreach - self.MHUreach

    @property
    def MHUreach(self):
        """Returns the quantity of tropical cyclones during the season that at
        any point became a major hurricane (>= 96kts).
        """
        return len(["MHUreach" for trop in self.tc if self.tc[trop].MHUreach is True])

    @property
    def cat45reach(self):
        """Returns the quantity of tropical cyclones from the season that
        reached category-4 or 5 (saffir-simpson scale) strength at any point
        during its life.
        """
        return len(["cat5" for tc in self.tc.values() if tc.maxwind >= 114])

    @property
    def cat5reach(self):
        """Returns the quantity of tropical cyclones from the season that
        reached category-5 (saffir-simpson scale) strength at any point during
        its life.
        """
        return len(["cat5" for tc in self.tc.values() if tc.maxwind >= 136])

class TropicalCyclone(_aliases.TropicalCycloneAliases, _calculations.TropicalCycloneCalculations, _reports.TropicalCycloneReports):
    """Object holding data for an individual tropical cyclone."""
    def __init__(self, storm_id, storm_name, seasonobj, hd2obj):
        self._atcfid = storm_id
        self._atcf_num = int(storm_id[2:4])
        self._year = int(storm_id[4:])
        self._name = storm_name
        self._entry = []     # List to keep track of indiv time entries
        self._season = seasonobj
        self._hd2 = hd2obj

    def __len__(self):
        """Returns the number of record entries for the particular storm in the
        Hurdat2 record.
        """
        return len(self.entry)

    def __repr__(self):
        return "<{} object - {}:{} - at 0x{}>".format(
            re.search(r"'(.*)'", str(type(self)))[1],
            self.atcfid,
            self.name,
            str(id(self)).upper().zfill(16)
        )

    def __getitem__(self, indx):
        return self.entry[indx]

    def coord_list(self):
        """Prints a report of entry-dates and the corresponding latitude and
        longitude of the storm's center position.
        """
        print("DATE, LAT, LON")
        for trk in self.entry:
            print("{:%Y-%m-%d %H:%M},{},{}".format(
                trk.entrytime,
                trk.location[0],
                trk.location[1]
            ))

    def stats(self):
        self.info()

    def info(self):
        """Prints a basic report of information on the tropical cyclone."""
        print("")
        print("{:^40}".format(
            "Statistics for {}{}".format(
                "{} ".format(
                    self.status_highest if self.name != "UNNAMED" else ""
                ),
                self.name
            )
        ))
        print("{:-^40}".format(""))
        print("* ATCF ID: {}".format(self.atcfid))
        print("* Track Entries: {}".format(len(self)))
        print("* TC Track Distance: {:.1f} nmi".format(self.track_distance_TC))
        if self.track_distance_TS > 0:
            print("  -- TS Track Distance: {:.1f} nmi".format(
                self.track_distance_TS
            ))
        if self.track_distance_HU > 0:
            print("  -- HU Track Distance: {:.1f} nmi".format(
                self.track_distance_HU
            ))
        if self.track_distance_MHU > 0:
            print("  -- MHU Track Distance: {:.1f} nmi".format(
                self.track_distance_MHU
            ))
        if self.maxwind > 0:
            print("* Peak Winds: {} kts".format(self.maxwind))
        else:
            print("* Peak Winds: N/A")
        print("* Minimum MSLP: {}{}".format(
            self.minmslp if self.minmslp != None else "N/A",
            " hPa" if self.minmslp != None else ""
        ))
        print("* ACE: {:.3f} * 10^4 kts^2".format(
            self.ACE * math.pow(10,-4)
        )) if self.ACE > 0 else print("* ACE: N/A")
        if self.HDP > 0:
            print("* HDP: {:.3f} * 10^4 kts^2".format(
                self.HDP * math.pow(10,-4)
            ))
        if self.MHDP > 0:
            print("* MHDP: {:.3f} * 10^4 kts^2".format(
                self.MHDP * math.pow(10,-4)
            ))
        print("* Started: {:%Y-%m-%d %H}Z".format(self.entry[0].entrytime))
        print("* Ended: {:%Y-%m-%d %H}Z".format(self.entry[-1].entrytime))
        print("   -Total Track Time: {} days, {} hours".format(
            math.floor(int((self.entry[-1].entrytime - self.entry[0].entrytime).total_seconds()) / 60 / 60 / 24),
            math.floor(int((self.entry[-1].entrytime - self.entry[0].entrytime).total_seconds()) / 60 / 60 % 24)
        ))
        print("* Landfall: {}{}".format(
            "Yes" if self.landfalls > 0 else "None",
            ", {} Record{}".format(
                self.landfalls,
                "s" if self.landfalls > 1 else ""
            ) if self.landfalls > 0 else ""
        ))
        print("")

    def summary(self):
        """Prints a detailed report for all entries recorded during the
        system's life-span.
        """
        print("")
        print(" {:-^59}".format(""))
        print(" {:^59}".format(
            "Track Summary for '{}', {}".format(
                self.atcfid,
                self.name
            )
        ))
        print(" {:-^59}".format(""))
        print(" {:5} {:^14} {:-^4} {:^13}  {:^18}".format(
            "ENTRY","","LAND", "LOCATION", "INTENSITY"
        ))
        print(" {:5} {:^14} {:^4} {:^5}  {:^6}  {:^4}  {:^4}  {:^6}".format(
            "INDEX","DATE", "FALL", "LAT", "LON", "MSLP", "WIND", "STATUS"
        ))
        print(" {:-^5} {:-^14} {:-^4} {:-^5}  {:-^6}  {:-^4}  {:-^4}  {:-^6}".format("","","","","","","",""))
        for trk in self.entry:
            print(" {:^5} {:%Y-%m-%d %H}Z {:^4} {:5}  {:6}  {:4}  {:4}  {:^6}".format(
                self.entry.index(trk),
                trk.entrytime,
                trk.record_identifier if trk.record_identifier == "L" else "",
                trk.lat_str,
                trk.lon_str,
                trk.mslp if trk.mslp != None else "N/A",
                trk.wind,
                trk.status if trk.wind < 96 else "MHU"
            ))
        print("")

    def hurdat2(self):
        """Prints a Hurdat2-formatted summary of the tropical cyclone."""
        print("{:>8},{:>19},{:>7},".format(
            self.atcfid,
            self.name,
            len(self.entry)
        ))
        for entry in self.entry:
            print(entry.hurdat2())

    @property
    def gps(self):
        """Return a list of tuples containing the gps coordinates of the
        tropical cyclone's track
        """
        return [e.location for e in self.entry]

    @property
    def minmslp(self):
        """Returns the minimum mean sea-level pressure (MSLP) recorded during
        the life of the storm.

        If insufficient data exists to determine MSLP, None will be returned.
        """
        return min([t.mslp for t in self.entry if t.mslp != None],default=None)

    @property
    def maxwind(self):
        """Returns the max peak-wind recorded during the life of the storm."""
        return max([t.wind for t in self.entry])

    @property
    def landfalls(self):
        """Returns the QUANTITY of landfalls recorded made by the system
        as a tropical cyclone.
        """
        return len(["L" for t in self.entry if t.record_identifier == "L" and t.status in ["SD","TD","SS","TS","HU"]])

    @property
    def landfall_TC(self):
        """Bool indicating whether at-least one landfall was made while a
        tropical cyclone.
        """
        return self.landfalls > 0

    @property
    def landfall_TD(self):
        """Bool indicating whether at-least one landfall was made while a
        tropical depression.
        """
        return any(t.record_identifier == "L" for t in self.entry if t.status in ["SD","TD"])

    @property
    def landfall_TS(self):
        """Bool indicating whether at-least one landfall was recorded by the
        tropical cyclone while designated as a tropical storm (TS) or
        sub-tropical storm (SS).
        """
        return any(t.record_identifier == "L" for t in self.entry if t.status in ["SS","TS"])

    @property
    def landfall_HU(self):
        """Bool indicating whether at-least one landfall was recorded by the
        tropical cyclone while designated as a Hurricane.
        """
        return any(t.record_identifier == "L" for t in self.entry if t.status == "HU")

    @property
    def landfall_MHU(self):
        """Bool indicating whether at-least one landfall was recorded by the
        tropical cyclone while a hurricane at major-hurricane strength
        (>= 96kts).
        """
        return any(t.record_identifier == "L" for t in self.entry if t.wind >= 96 and t.status == "HU")

    @property
    def TSreach(self):
        """Bool indicating whether the storm was ever objectively designated as
        a tropical storm (TS) or sub-tropical storm (SS). Hurricane's (HU) are
        tested for as well with an explanation below.

        The inclusivity of hurricanes may seem a bit-too overzealous, as a
        tropical cyclone MUST become a tropical storm before it could become a
        hurricane since max-wind tendency is a continuous function. But in
        HURDAT2, they are represented as discrete or time-stepped. Because of
        this, though exceptionally rare, it is possible for a storm to have a
        hurricane entry but zero tropical storm entries. For example, in the
        Atlantic HURDAT2, this occurrence happens, but virtually all storms of
        this nature occur before 1900.
        """
        return any(t.status in ["TS","SS","HU"] for t in self.entry)

    @property
    def HUreach(self):
        """Bool indicating whether the storm was ever objectively designated as
        a hurricane (HU).
        """
        return any(t.status == "HU" for t in self.entry)

    @property
    def MHUreach(self):
        """Bool indicating whether the storm ever reached major hurricane
        status (>= 96kts).
        """
        return any(t.wind >= 96 for t in self.entry if t.status == "HU")

    @property
    def cat45reach(self):
        """Returns a bool indicating if the tropical cyclone ever reached at-
        least Category 4 strength during its life.
        """
        return any(t.wind >= 114 for t in self.entry if t.status == "HU")

    @property
    def cat5reach(self):
        """Returns a bool indicating if the tropical cyclone ever reached
        Category 5 strength during its life.
        """
        return any(t.wind >= 136 for t in self.entry if t.status == "HU")

    @property
    def maxwind_mslp(self):
        """Returns the MSLP recorded at the time of the tropical cyclone's peak
        wind-based intensity. This attribute was included as peak-winds and
        minimum MSLP, though closely related, may not necessarily occur at the
        same time.
        """
        return max(
            filter(
                lambda en: en.wind is not None,
                self.entry
            ),
            key = lambda en: en.wind,
            default=None
        ).mslp

    @property
    def minmslp_wind(self):
        """Returns the wind recorded at the time of the tropical cyclone's
        minimum MSLP reading. This attribute was included as peak-winds and
        minimum MSLP, though closely related, may not necessarily occur at the
        same time.
        """
        return min(
            filter(
                lambda en: en.mslp is not None,
                self.entry
            ),
            key = lambda en: en.mslp,
            default=None
        ).wind

    @property
    def statuses_reached(self):
        """Returns a list of all designated statuses during the tropical
        cyclone's life.
        """
        return list(set([s.status for s in self.entry]))

    @property
    def status_highest(self):
        """
        Returns a readable descriptor for the storm based on its highest status
        reached.
        
        Examples
        -------
        TS -> 'Tropical Storm'
        HU -> 'Hurricane'
        HU and self.maxwind >= 96 -> 'Major Hurricane'
        """
        order = ["HU", "TS", "SS", "TD", "SD", "LO", "EX"]
        for status in order:
            if status in self.statuses_reached:
                return format_status(status, self.maxwind)

class TCRecordEntry(_aliases.TCEntryAliases, _calculations.TCEntryCalculations):
    """Object that holds information from one individual (one line) HURDAT2
    entry.
    """

    __slots__ = [
        "_entrytime", "_record_identifier", "_status",
        "_lat_str", "_lon_str", "_location", "_lat", "_lon",
        "_wind", "_status_desc", "_mslp",
        "_tsNE", "_tsSE", "_tsSW", "_tsNW",
        "_ts50NE", "_ts50SE", "_ts50SW", "_ts50NW",
        "_huNE", "_huSE", "_huSW", "_huNW", "_wind_radii",
        "_tc", "_season", "_hd2"
    ]

    TCRecordLine = collections.namedtuple(
        "TCRecordLine",
        [
            "day", "time", "record_identifier", "status",
            "latitude", "longitude", "wind", "mslp",
            "tsNE", "tsSE", "tsSW", "tsNW",
            "ts50NE", "ts50SE", "ts50SW", "ts50NW",
            "huNE", "huSE", "huSW", "huNW", "wind_radii"
        ],
        defaults = (None,)
    )

    def __init__(self, tc_entry, tcobj, seasonobj, hd2obj):

        try:
            tcentry = self.TCRecordLine(*tc_entry)
        except:
            print(tc_entry)
            raise

        # Date
        self._entrytime = datetime.datetime(
            int(tcentry.day[:4]),
            int(tcentry.day[4:6]),
            int(tcentry.day[6:]),
            int(tcentry.time[:2]),
            int(tcentry.time[2:])
        )

        self._record_identifier = tc_entry[2] if tc_entry[2] != '' else None
        self._status = tc_entry[3]
        self._lat_str = tc_entry[4]
        self._lon_str = tc_entry[5]
        self._location = coord(self.lat_str,self.lon_str)
        self._lat = self.location[0]
        self._lon = self.location[1]
        self._wind = int(tc_entry[6])
        self._status_desc = format_status(self.status,self.wind)
        self._mslp = int(tc_entry[7]) if tc_entry[7] != '-999' else None
        # Extent Indices - 0 = NE, 1 = SE, 2 = SW, 3 = NW
        self._tsNE = int(tcentry.tsNE) if tcentry.tsNE != "-999" else None
        self._tsSE = int(tcentry.tsSE) if tcentry.tsSE != "-999" else None
        self._tsSW = int(tcentry.tsSW) if tcentry.tsSW != "-999" else None
        self._tsNW = int(tcentry.tsNW) if tcentry.tsNW != "-999" else None
        self._ts50NE = int(tcentry.ts50NE) if tcentry.ts50NE != "-999" else None
        self._ts50SE = int(tcentry.ts50SE) if tcentry.ts50SE != "-999" else None
        self._ts50SW = int(tcentry.ts50SW) if tcentry.ts50SW != "-999" else None
        self._ts50NW = int(tcentry.ts50NW) if tcentry.ts50NW != "-999" else None
        self._huNE = int(tcentry.huNE) if tcentry.huNE != "-999" else None
        self._huSE = int(tcentry.huSE) if tcentry.huSE != "-999" else None
        self._huSW = int(tcentry.huSW) if tcentry.huSW != "-999" else None
        self._huNW = int(tcentry.huNW) if tcentry.huNW != "-999" else None
        self._wind_radii = int(tcentry.wind_radii) if tcentry.wind_radii not in ["-999", None] else None

        # Record parent objects
        self._tc = tcobj
        self._season = seasonobj
        self._hd2 = hd2obj

    def __repr__(self):
        return "<{} object - {}:{} - Index {}: {:%Y%m%d %H%MZ} - at 0x{}>".format(
            re.search(r"'(.*)'", str(type(self)))[1],
            self._tc.atcfid,
            self._tc.name,
            self._tc.entry.index(self),
            self.date,
            str(id(self)).upper().zfill(16)
        )

    def hurdat2(self):
        """Returns a string of a hurdat2-formatted line of the entry
        information. It should be identical to the corresponding entry in the
        actual Hurdat2 record.
        """
        return "{:>8},{:>5},{:>2},{:>3},{:>6},{:>7},{:>4},{:>5},".format(
            "{:%Y%m%d}".format(self.entrytime),
            "{:%H%M}".format(self.entrytime),
            "" if self.record_identifier is not "L" else "L",
            self.status,
            self.lat_str,
            self.lon_str,
            self.wind,
            self.mslp if self.mslp is not None else -999,
        ) + "{:>5},{:>5},{:>5},{:>5},".format(
            *[quad if quad is not None else -999 for quad in self.extent_TS]
        ) + "{:>5},{:>5},{:>5},{:>5},".format(
            *[quad if quad is not None else -999 for quad in self.extent_TS50]
        ) + "{:>5},{:>5},{:>5},{:>5},".format(
            *[quad if quad is not None else -999 for quad in self.extent_HU]
        )

def coord(strlat,strlon):
    """Method used typically only on read-in of data to convert a Hurdat2-
    formatted lat/lon coordinate into a float representation of the information
    and return it.

    Example: coord("26.1N", "88.9W") -->  (26.1, -88.9)
    """
    if strlat[-1] == "N": decimal_lat = round(float(strlat[:-1]),1)
    else: decimal_lat = round(-1 * float(strlat[:-1]),1)
    if strlon[-1] == "E": decimal_lon = round(float(strlon[:-1]),1)
    else: decimal_lon = round(-1 * float(strlon[:-1]),1)
    return (decimal_lat, decimal_lon)

def format_record_identifier(ri):
    """Returns a description about an entry's record_identifier.

    Definitions/interpretations found in hurdat2-format pdf found online.
    """
    if ri == "L": return "Landfall"
    elif ri == "W": return "Maximum sustained wind speed"
    elif ri == "P": return "Minimum in central pressure"
    elif ri == "I": return "An intensity peak in terms of both pressure and wind"
    elif ri == "C": return "Closest approach to a coast, not followed by a landfall"
    elif ri == "S": return "Change of status of the system"
    elif ri == "G": return "Genesis"
    elif ri == "T": return "Provides additional detail on the track (position) of the cyclone"
    else: return "* No Description Available *"

def format_status(status,wind):
    """Returns a description about a record's 2-letter status.

    Definitions/interpretations found in hurdat2-format pdf found online.
    """
    if status == "DB" or status == "LO" or status == "WV": return "Disturbance, Low, or Tropical Wave"
    elif status == "SD": return "Subtropical Depression"
    elif status == "TD": return "Tropical Depression"
    elif status == "SS": return "Subtropical Storm"
    elif status == "TS": return "Tropical Storm"
    elif status == "EX": return "Extratropical Cyclone"
    elif status == "HU" and wind < 96: return "Hurricane"
    elif status == "HU" and wind >= 96: return "Major Hurricane"
    else: return "Unknown"