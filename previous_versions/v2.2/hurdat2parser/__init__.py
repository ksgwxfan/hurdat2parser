"""hurdat2parser v2.2

https://github.com/ksgwxfan/hurdat2parser

hurdat2parser v2.x is provides a convenient access to interpret and work with
tropical cyclone data that is contained in a widely-used and updated dataset,
HURDAT2 (https://www.nhc.noaa.gov/data/#hurdat). The purpose of this module is to
provide a quick way to investigate HURDAT2 data. It includes methods for
retrieving, inspecting, ranking, or even exporting data for seasons, individual
storms, or climatological eras.

To get started:
1) Install: >>> pip install hurdat2parser
2a) Download HURDAT2 Data: https://www.nhc.noaa.gov/data/#hurdat
    OR See example call below to have the program attempt to download it for you
3) In python, import and invoke call using the hurdat2 file you downloaded (the
    following is just an example):

    >>> import hurdat2parser
    >>> atl = hurdat2parser.Hurdat2("path_to_hurdat2.txt")

    OR ATTEMPT TO RETRIEVE FROM ONLINE
    >>> atl = hurdat2parser.Hurdat2(basin="atl")
    # Use "pac" to get the NE/CEN Pacific version

hurdat2parser, Copyright (c) 2019-2023, Kyle Gentry (KyleSGentry@outlook.com)
License: MIT
ksgwxfan.github.io
echotops.blogspot.com
"""

import calendar
import difflib
import math
import re
import urllib.request
import itertools
import datetime
import os
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

    def __init__(self, *hurdat2file_list, **kw):
        """Initializes a new Hurdat2 object.
        
        Arguments:
            *hurdat2file_list: the local file-paths (or URLs) of the hurdat2
            record(s)

        Keyword Arguments:
            basin (None): If you want to try to retrieve the latest hurdat2
                file from the NHC to ingest, let it know which basin you want
                to download. Acceptable strings to use would be "atl", "al", or
                "atlantic" for the North Atlantic hurdat2. For the North-East/
                Central Pacific, "pac", "nepac", and "pacific" are recognized.
                Of note, the Atlantic hurdat2 file is around 6MB.
            urlcheck (False): If True, urls are accepted. This enables the
                download of a remote version of a Hurdat2 dataset. The url
                string is passed as if a local file and will eventually be
                attempted to be downloaded.

        Example call:
            atl = hurdat2parser.Hurdat2("atlantic_hurdat2.txt")
                * Attempts to load a local file named "hurdat2_file.txt"
            atl = hurdat2parser.Hurdat2(basin="pac")
                * Attempts to download the latest NE/CEN Pacific hurdat2 file
            atl = hurdat2parser.Hurdat2("https://somewebsite.zxcv/hd2.txt", urlcheck=True)
                * Attempts to download inspect the passed-string as a url and
                tries to download
            
        """
        self._tc = {}        # Dictionary containing all hurdat2 storm data
        self._season = {}    # Dictionary containing all relevant season data

        # Validity checking -------------------------------
        # no local path given and Non-existent or invalid basin
        if len(hurdat2file_list) == 0 \
        and (kw.get("basin") is None or type(kw.get("basin")) != str):
            raise ValueError(
                "No path to a local hurdat2 file given and no valid basin "
                "indicated to attempt online retrieval."
            )
        # No online, but invalid local paths
        if kw.get("basin") is None \
        and len(hurdat2file_list) != 0 \
        and all(os.path.exists(fi) == False for fi in hurdat2file_list) \
        and kw.get("urlcheck", False) is False:
            raise FileNotFoundError(
                "{} {} not {}valid file path{}.".format(
                    ", ".join([
                        "'{}'".format(fi) for fi in hurdat2file_list
                    ]),
                    "is" if len(hurdat2file_list) == 1 else "are",
                    "a " if len(hurdat2file_list) == 1 else "",
                    "" if len(hurdat2file_list) == 1 else "s",
                )
            )
        # -------------------------------------------------------

        # Download from online
        if type(kw.get("basin")) == str \
        and kw.get("basin").lower() in [
            "al", "atl", "atlantic", "pac", "nepac", "pacific"
        ]:
            # determines which dataset will be downloaded
            basin_prefix = "nepac-" \
                if kw.get("basin").lower() in ["pac", "nepac", "pacific"] \
                else ""

            # https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2021-100522.txt
            with urllib.request.urlopen("https://www.nhc.noaa.gov/data/hurdat", timeout=5) as u:
                _pgdata = u.read().decode()

            _hd2list = re.findall(
                "hurdat2-{}".format(basin_prefix) + r"\d{4}-\d{4}.*\.txt",
                _pgdata,
                flags=re.I
            )
            hd2url = "https://www.nhc.noaa.gov/data/hurdat/" \
                + sorted(_hd2list, reverse=True)[0]

            # read in the url
            try:
                with urllib.request.urlopen(hd2url, timeout=5) as u:
                    hd2fileobj = u.read().decode()
                # print("* Downloaded '{}'".format(hd2url))
            except:
                if len(hurdat2file_list) == 0:
                    raise
            self._build_tc_dictionary(hd2fileobj, False)
            # print("* Download and read-in of `{}` successful!".format(
                # hd2url
            # ))
        # invalid basin listed
        elif type(kw.get("basin")) == str:
            if len(hurdat2file_list) == 0:
                raise ValueError(
                    "'{}' is an unrecognized basin. ".format(kw.get("basin")) \
                  + "Please use something like 'atl' or 'pac' to direct the " \
                  + "module to retrieve the deisred hurdat2 file from online."
                )
            else:
                print(
                    "* Skipping basin download. " \
                  + "'{}' is an unrecognized basin. ".format(kw.get("basin")) \
                  + "Please use something like 'atl' or 'pac' to direct the " \
                  + "module to retrieve the deisred hurdat2 file from online."
                )

        for hd2file in hurdat2file_list:
            if os.path.exists(hd2file):
                self._build_tc_dictionary(hd2file)  # Call to build/analyze the hurdat2 file
                # print("* Read-in of `{}` successful!".format(hd2file))
            # download a given url
            elif kw.get("urlcheck"):
                try:
                    with urllib.request.urlopen(hd2file, timeout=5) as u:
                        hd2fileobj = u.read().decode()
                    # print("* Downloaded '{}'".format(hd2file))
                except Exception as e:
                    print("* Skipping '{}' due to {}".format(hd2file, e))
                    hd2fileobj = None
                if hd2fileobj is not None:
                    self._build_tc_dictionary(hd2fileobj, False)
                    # print("* Download and read-in of `{}` successful!".format(
                        # hd2file
                    # ))
            else:
                print("* Skipping `{}` because that path doesn't exist!".format(
                    hd2file
                ))

        if len(self) == 0:
            raise ValueError("No storm data ingested!")

    def __repr__(self):
        return "<{} object - {}: {}-{} - at 0x{}>".format(
            re.search(r"'(.*)'", str(type(self)))[1],
            self.basin(),
            *self.record_range,
            hex(id(self))[2:].upper().zfill(16)
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
        if type(s) == slice:
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
        elif type(s) == int:
            return self.season[s]
        # String based
        elif type(s) == str:
            # ATCFID Request
            if re.search(r"^[A-Z]{2}[0-9]{6}.*", s, flags=re.I):
                return self.tc[s.upper()[:8]]
            # Season Request
            elif s.isnumeric():
                return self.season[int(s[:4])]
            # Name Search implied (will return the last storm so-named)
            else:
                return self.storm_name_search(s, False, True if "_" in s or "-" in s else False)
        # try handling all other types by converting to str then search by name
        else:
            return self.storm_name_search(str(s), False)

    def _build_tc_dictionary(self, hurdat2file, path=True):
        """Populate the Hurdat2 object with data from a hurdat2 file.

        Arguments:
            hurdat2file: the file-path (or string version) of the hurdat2 file

        Default Arguments:
            path (True): this tells the method what kind object to expect. By
                default, it will be considered a file-path. If False, it will
                expect a stringified version of the database.
        """
        if path is True:
            with open(hurdat2file) as h:
                _hd2data = h.read().splitlines()
        else:
            _hd2data = hurdat2file.splitlines()

        for line in _hd2data:
            lineparsed = re.split(r", *", re.sub(r", *$", "", line))
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
                        line,
                        self.tc[atcfid],
                        self.season[tcyr],
                        self
                    )
                )

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
            searchname = searchname.replace("_", "").replace("-", "")
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
                ),
                key=lambda tup: tup[1],
                reverse=True
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

    def basin_abbr(self, season_obj=None):
        """Returns a list of basin abbreviations used in the hurdat2 record.
        
        This is primarily of use to the .basin() method.
        """
        try:
            return list(set([
                tc.atcfid[:2]
                for tc in (
                    self.tc.values()
                    if season_obj is None
                    else season_obj.tc.values()
                )
            ]))
        except:
            return ["UNK"]

    def basin(self, season_obj=None):
        """Returns a string containing the various oceanic basins represented in the hurdat2 database(s) being analyzed. As an example, the NHC releases a East/Central Pacific Hurdat2.

        Keyword Argument:
            season_obj (None): This is used to isolate a basin names from a particular season. It's possible in the aforementioned East/Central Pacific that cyclones occur in the east pacific but not central. So a report or inquired stats from a particular season wouldn't need to show data from the non-existent basin.
        """

        basin_names = []
        try:
            basin_names = list(set([
                self.BASIN_DICT[basin]
                for basin in self.basin_abbr(season_obj)
            ]))
        except:
            pass
        if len(basin_names) > 0:
            return " / ".join(basin_names) \
                + " Basin{}".format(
                    "s" if len(self.basin_abbr(season_obj)) > 1 else ""
                )
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
            hex(id(self))[2:].upper().zfill(16)
        )

    def __len__(self):
        """Returns the number of tropical cyclones from a particular season."""
        return len(self.tc)

    def __getitem__(self, s):
        # Storm Number passed
        if type(s) == int and s >= 0:
            tcmatches = [
                tc for atcfid, tc in self.tc.items()
                if re.search(
                    r"[A-Z][A-Z]{:0>2}\d\d\d\d".format(s),
                    atcfid
                )
            ]
            if len(tcmatches) == 0:
                return list(self.tc.values())[s]
            elif len(tcmatches) == 1:
                return tcmatches[0]
            else:
                print("* Multiple matches found. Choose intended storm:")
                print("------------------------------------------------")
                for indx, tc in enumerate(tcmatches):
                    print("{}. {} - '{}'".format(
                        indx+1,
                        tc.atcfid,
                        tc.name
                    ))
                print("------------------------------------------------")
                choice = input("  -- Enter selection ('c' to cancel): ")
                while True:
                    if choice.isnumeric() \
                    and 0 < int(choice) <= len(tcmatches):
                        return tcmatches[int(choice)-1]
                    elif len(choice) > 0 and choice.lower()[0] == "c":
                        raise KeyboardInterrupt
                    else:
                        choice = input("  -- Invalid selection. Try again: ")

        elif type(s) == int and s < 0:
            return list(self.tc.values())[s]
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

    def stats(self, year1=None, year2=None, start=None, thru=None, width=70, report_type=print, **kw):
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
            report_type (print): controls the format of the seasonal stats
                requested. By default, it prints out to the console. if <<str>>
                (no quotations needed), it returns a stringified version of the
                stats

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
        return getattr(
            self._hd2,
            "_season_stats" + ("_str" if report_type == str else "")
        )(
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
        for tcid, trop in self.tc.items():
            print(" {:<10} {:8} {:^4} {:>4} {:>4}  {:>6.1f}  {:^6}  {:^6}  {:^6}".format(
                trop.name.title(),
                trop.atcfid,
                trop.landfalls,
                trop.minmslp if trop.minmslp != None else "N/A",
                trop.maxwind if trop.maxwind > 0 else "N/A",
                trop.track_distance_TC,
                "{:>6.3f}".format(trop.ACE * math.pow(10,-4)) if trop.ACE > 0 else "--",
                "{:>6.3f}".format(trop.HDP * math.pow(10,-4)) if trop.HDP > 0 else "--",
                "{:>6.3f}".format(trop.MHDP * math.pow(10,-4)) if trop.MHDP > 0 else "--"
            ))
        print("")

    def hurdat2(self):
        """Prints a Hurdat2-formatted summary of the entire season."""
        for tc in self.tc.values():
            tc.hurdat2()

    @property
    def tc_entries(self):
        """
        Returns a temporally-ascending list of <<TCRecordEntry>>s of all
        tropical cyclones occurring during the season.
        """
        return sorted([
            en for tcid, TC in self.tc.items()
            for en in TC.entry
            if en.is_TC
        ], key = lambda moment: moment.entrytime)

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
            hex(id(self))[2:].upper().zfill(16)
        )

    def __getitem__(self, indx):
        return self.entry[
            int(indx) if type(indx) not in [list, tuple] else indx[0]
        ]

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
        print("   - Life as Tropical Cyclone: {} days".format(self.duration))
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
        for en in self.entry:
            print(" {:^5} {:%Y-%m-%d %H}Z {:^4} {:5}  {:6}  {:4}  {:4}  {:^6}".format(
                self.entry.index(en),
                en.entrytime,
                en.record_identifier if en.record_identifier == "L" else "",
                en.lat_str,
                en.lon_str,
                en.mslp if en.mslp != None else "N/A",
                en.wind,
                en.status if en.wind < 96 else "MHU"
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
    def tc_entries(self):
        """
        Returns a list of <<TCRecordEntry>>'s where the storm is designated a
        tropical cyclone.
        """
        return [
            en for en in self.entry
            if en.is_TC
        ]

    @property
    def gps(self):
        """Return a list of tuples containing the gps coordinates of the
        tropical cyclone's track
        """
        return [en.location for en in self.entry]

    @property
    def minmslp(self):
        """Returns the minimum mean sea-level pressure (MSLP) recorded during
        the life of the storm.

        If insufficient data exists to determine MSLP, None will be returned.
        """
        return min(
            [en.mslp for en in self.entry if en.mslp != None],
            default=None
        )

    @property
    def maxwind(self):
        """Returns the max peak-wind recorded during the life of the storm."""
        return max(en.wind for en in self.entry)

    @property
    def landfalls(self):
        """Returns the QUANTITY of landfalls recorded made by the system
        as a tropical cyclone.
        """
        return len([
            "L" for en in self.entry
            if en.record_identifier == "L"
            and en.is_TC
        ])

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
        return any(
            en.record_identifier == "L"
            for en in self.entry
            if en.status in ["SD","TD"]
        )

    @property
    def landfall_TS(self):
        """Bool indicating whether at-least one landfall was recorded by the
        tropical cyclone while designated as a tropical storm (TS) or
        sub-tropical storm (SS).
        """
        return any(
            en.record_identifier == "L"
            for en in self.entry
            if en.status in ["SS","TS"]
        )

    @property
    def landfall_HU(self):
        """Bool indicating whether at-least one landfall was recorded by the
        tropical cyclone while designated as a Hurricane.
        """
        return any(
            en.record_identifier == "L"
            for en in self.entry
            if en.status == "HU"
        )

    @property
    def landfall_MHU(self):
        """Bool indicating whether at-least one landfall was recorded by the
        tropical cyclone while a hurricane at major-hurricane strength
        (>= 96kts).
        """
        return any(
            en.record_identifier == "L"
            for en in self.entry
            if en.wind >= 96 and en.status == "HU"
        )

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
        return any(en.status in ["TS","SS","HU"] for en in self.entry)

    @property
    def HUreach(self):
        """Bool indicating whether the storm was ever objectively designated as
        a hurricane (HU).
        """
        return any(en.status == "HU" for en in self.entry)

    @property
    def MHUreach(self):
        """Bool indicating whether the storm ever reached major hurricane
        status (>= 96kts).
        """
        return any(en.wind >= 96 for en in self.entry if en.status == "HU")

    @property
    def cat45reach(self):
        """Returns a bool indicating if the tropical cyclone ever reached at-
        least Category 4 strength during its life.
        """
        return any(en.wind >= 114 for en in self.entry if en.status == "HU")

    @property
    def cat5reach(self):
        """Returns a bool indicating if the tropical cyclone ever reached
        Category 5 strength during its life.
        """
        return any(en.wind >= 136 for en in self.entry if en.status == "HU")

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
        return list(set([
            en.status for en in self.entry
        ]))

    @property
    def status_highest(self):
        """
        Returns a readable descriptor for the storm based on its highest-order
        status designated.

        Examples
        -------
        TS -> 'Tropical Storm'
        HU -> 'Hurricane'
        HU and self.maxwind >= 96 -> 'Major Hurricane'
        """
        order = ["HU", "TS", "SS", "TD", "SD", "EX", "LO", "DB"]
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
        "_huNE", "_huSE", "_huSW", "_huNW", "_maxwind_radius",
        "_tc", "_season", "_hd2", "_hurdat2line"
    ]

    TCRecordLine = collections.namedtuple(
        "TCRecordLine",
        [
            "day", "time", "record_identifier", "status",
            "latitude", "longitude", "wind", "mslp",
            "tsNE", "tsSE", "tsSW", "tsNW",
            "ts50NE", "ts50SE", "ts50SW", "ts50NW",
            "huNE", "huSE", "huSW", "huNW", "maxwind_radius"
        ],
        # defaults necessary to maintain backward compatibility
        # This would be backward compatible
        defaults = (None, None, None, None, None)
    )

    def __init__(self, tc_entry, hurdat2line, tcobj, seasonobj, hd2obj):

        tcentry = self.TCRecordLine(*tc_entry)

        # The original hurdat2 line that this entry was created from
        self._hurdat2line = hurdat2line

        # Date
        self._entrytime = datetime.datetime(
            int(tcentry[0][:4]),  #year
            int(tcentry[0][4:6]), #month
            int(tcentry[0][-2:]), #day
            int(tcentry[1][:2]),
            int(tcentry[1][-2:])
        )

        self._record_identifier = tcentry[2] if tcentry[2] != '' else None
        self._status = tcentry[3]
        self._lat_str = tcentry[4]
        self._lon_str = tcentry[5]
        self._lat = coord_conv(self.lat_str)
        self._lon = coord_conv(self.lon_str)
        self._wind = int(tcentry[6])
        self._status_desc = format_status(self.status, self.wind)
        self._mslp = int(tcentry[7]) if tcentry[7] != '-999' else None
        # Extent Indices - 0 = NE, 1 = SE, 2 = SW, 3 = NW
        # Tropical Storm extents
        self._tsNE = int(tcentry[8]) \
            if tcentry[8] != "-999" \
            else 0 if self._wind < 34 \
            else None
        self._tsSE = int(tcentry[9]) \
            if tcentry[9] != "-999" \
            else 0 if self._wind < 34 \
            else None
        self._tsSW = int(tcentry[10]) \
            if tcentry[10] != "-999" \
            else 0 if self._wind < 34 \
            else None
        self._tsNW = int(tcentry[11]) \
            if tcentry[11] != "-999" \
            else 0 if self._wind < 34 \
            else None
        # Gale extents
        self._ts50NE = int(tcentry[12]) \
            if tcentry[12] != "-999" \
            else 0 if self._wind < 50 \
            else None
        self._ts50SE = int(tcentry[13]) \
            if tcentry[13] != "-999" \
            else 0 if self._wind < 50 \
            else None
        self._ts50SW = int(tcentry[14]) \
            if tcentry[14] != "-999" \
            else 0 if self._wind < 50 \
            else None
        self._ts50NW = int(tcentry[15]) \
            if tcentry[15] != "-999" \
            else 0 if self._wind < 50 \
            else None
        # Hurricane extents
        self._huNE = int(tcentry[16]) \
            if tcentry[16] != "-999" \
            else 0 if self._wind < 64 \
            else None
        self._huSE = int(tcentry[17]) \
            if tcentry[17] != "-999" \
            else 0 if self._wind < 64 \
            else None
        self._huSW = int(tcentry[18]) \
            if tcentry[18] != "-999" \
            else 0 if self._wind < 64 \
            else None
        self._huNW = int(tcentry[19]) \
            if tcentry[19] != "-999" \
            else 0 if self._wind < 64 \
            else None
        self._maxwind_radius = int(tcentry[20]) \
            if len(tcentry) >= 21 \
            and tcentry[20] not in ["-999", None] \
            else None

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
            hex(id(self))[2:].upper().zfill(16)
        )

    @property
    def location(self):
        """
        Returns a tuple of the latitude and longitude (in decimal degrees and
        in that respective order) for this entry.
        """
        return (self.lat, self.lon)

    @property
    def location_reversed(self):
        """
        Returns a tuple of the longitude and latitude (in decimal degrees and
        in that respective order) for this entry.

        This was included as GIS programs seem to prefer this order.
        """
        return (self.lon, self.lat)

    @property
    def is_TC(self):
        """Returns whether or not the storm was designated as a tropical
        cyclone at the time of this <<TCRecordEntry>>.

        The entry status must be one of the following: "SD", "TD", "SS", "TS", "HU".
        """
        return self.status in ["SD", "TD", "SS", "TS", "HU"]

    @property
    def is_synoptic(self):
        """Returns whether or not the <<TCRecordEntry>>.entrytime is considered
        to be synoptic.

        To be True, it must have a recorded hour of 0Z, 6Z, 12Z, or 18Z 'on the
        dot' (minute, second == 0).

        This is helpful in calculating energy indices.
        """
        return self.hour in [0, 6, 12, 18] and self.minute == 0

    @property
    def previous_entries(self):
        """
        Returns a list of preceding <TCRecordEntry>s in the parent
        <TropicalCyclone>.entry list.
        """
        return self._tc[0:self._tc.entry.index(self)]

    @property
    def previous_entry(self):
        """
        Returns the <TCRecordEntry> that occurred PREVIOUS (preceding this
        entry) in the parent <TropicalCyclone>.entry list. Returns None if it
        is the first index (index 0).
        """
        if self._tc.entry.index(self)-1 >= 0:
            return self._tc[self._tc.entry.index(self)-1]
        else:
            return None

    @property
    def next_entries(self):
        """
        Returns a list of succeeding <TCRecordEntry>s in the parent
        <TropicalCyclone>.entry list.
        """
        return self._tc[self._tc.entry.index(self)+1:]

    @property
    def next_entry(self):
        """
        Returns the <TCRecordEntry> that occurs NEXT (following this entry) in
        the parent <TropicalCyclone>.entry list. Returns None if it is the last
        entry.
        """
        try:
            return self._tc[self._tc.entry.index(self)+1]
        except:
            return None

    def hurdat2(self):
        """
        Returns a string of a hurdat2-formatted line of the entry information.

        A few minor differences will exist between this output and the actual
        line found in the hurdat2 database. If using an older hurdat2 database
        (prior to 2022 release), it won't have maxwind radii available. Though
        this field is not part of that older database, this method will report
        it as null ('-999'). Also, wind extent information will likely be
        different. This is because upon ingest, this module infers non-
        applicable wind-extents as 0. For example, a tropical storm, having
        winds < 64kt, will objectively have a hurricane wind-extent as 0, where
        for storms prior to 2004, the database would say '-999'.

        One other possible difference would occur if this version of the module
        is used with future hurdat2 databases that include more variables
        (which this version of the module would be oblivious to).

        To see the line that the data for this entry was formulated from, use
        the method hurdat2orig()
        """
        return "{:>8},{:>5},{:>2},{:>3},{:>6},{:>7},{:>4},{:>5},".format(
            "{:%Y%m%d}".format(self.entrytime),
            "{:%H%M}".format(self.entrytime),
            "" if self.record_identifier != "L" else "L",
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
        ) + "{:>5},".format(self.maxwind_radius if self.maxwind_radius is not None else -999)


    def hurdat2orig(self):
        """
        Returns a carbon-copy of the line from the hurdat2 database that this
        entry was formed from.
        """
        return self._hurdat2line

    @property
    def extent_TS(self):
        return [self.tsNE, self.tsSE, self.tsSW, self.tsNW]

    @property
    def extent_TS50(self):
        return [self.ts50NE, self.ts50SE, self.ts50SW, self.ts50NW]

    @property
    def extent_HU(self):
        return [self.huNE, self.huSE, self.huSW, self.huNW]

def coord_conv(coordstr):
    """
    Takes a hurdat2-formatted lat/lon coordinate and returns a float
    representation thereof.

    Example:
        coord_conv("26.1N") -->  26.1
        coord_conv("98.6W") -->  -98.6
    """
    if coordstr[-1] in ["N", "E"]:
        return round(float(coordstr[:-1]), 1)
    else:
        return round(-1 * float(coordstr[:-1]), 1)

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

def format_status(status, wind):
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