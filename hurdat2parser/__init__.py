"""hurdat2parser v2.0.1

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

hurdat2parser, Copyright (c) 2019-2021, Kyle Gentry (KyleSGentry@outlook.com)
License: MIT
ksgwxfan.github.io
echotops.blogspot.com

Fixes in 2.0.1:
    - fixed error preventing rank_seasons_thru from working

"""

import calendar
import difflib
import math
import os
import csv
import re
import time
import statistics
import itertools
import datetime
import shapefile
import geojson

class Hurdat2:
    """Initializes a new Hurdat2 object"""
    def __init__(self, hurdat2file):
        self.tc = {}        # Dictionary containing all hurdat2 storm data
        self.season = {}    # Dictionary containing all relevant season data
        # used to prevent multiple loads of the same file to the same object
        self.filesappended = []
        self._build_tc_dictionary(hurdat2file)  # Call to build/analyze the hurdat2 file

    def __len__(self):
        """Returns the number of tracked systems in the Hurdat2 record"""
        return len(self.tc)

    def __str__(self):
        if all(atcfid.startswith("A") for atcfid in self.tc): return "Atlantic Basin"
        elif all(re.search("^(E|C)",atcfid) for atcfid in self.tc): return "Northeast/Central Pacific Basin"
        elif all(re.search("^(A|C|E)",atcfid) for atcfid in self.tc): return "Atlantic and Northeast/Central Pacifc Basins"
        else: return "Unknown Region"

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
            tuple or list: calls the multi_season_info method. Index 0
                represents the start year while index 1 represents the end. In
                contrast to the slice method, this will be inclusive of the end
                year passed. [2000, 2005] would include 2005 in calculations.
            int: grabs the _season object matching the year passed.
            str: inspects the string and returns either a storm object, a
                season object, or a call to the name-search function
        """
        # multi-season info
        if type(s) is slice:
            st = s.start
            en = s.stop-1
            return self.multi_season_info(st, en)
        # multi-season info passed as tuple
        elif type(s) in [tuple, list]:
            st = int(s[0])
            en = int(s[1])
            return self.multi_season_info(st, en)
        # Season passed as int
        elif type(s) is int:
            return self.season[s]
        # String based
        elif type(s) == str:
            # ATCFID Request
            if re.search(r"^[A-Z]{2}[0-9]{4}.*", str(s), re.I):
                return self.tc[s.upper()[:8]]
            # Season Request
            elif re.search(r"^[0-9]{4}.*", s):
                return self.season[int(s[:4])]
            # Name Search implied
            else:
                return self.storm_name_search(s, False)
        # try handling all other types by converting to str then search by name
        else:
            return self.storm_name_search(str(s), False)

    def _build_tc_dictionary(self,hurdat2file):
        """Populate the Hurdat2 object with data from a hurdat2 file.

        Arguments:
            hurdat2file: the file-path of the hurdat2 file
        """
        if hurdat2file in self.filesappended:
            return print("OOPS! That file has already been read-in to this Hurdat2 object.")
        self.filesappended.append(hurdat2file)
        with open(hurdat2file) as h:
            for line in h.readlines():
                lineparsed = [each.strip() for each in line.strip("\n").split(",")]
                # If the line begins with AL, EP, or CP, it signals a new
                #   ATCFID, or in other words, a new storm; assigns to the
                #   self.tc dictionary
                if re.search(r"^(AL|EP|CP)",lineparsed[0]):   
                    self.tc[lineparsed[0]] = TropicalCyclone(lineparsed[0],lineparsed[1])
                    # The ATCFID (functions as a dictionary key)
                    _current_storm = lineparsed[0]
                else:   # indicates a time-stamped entry for the current storm
                    self.tc[_current_storm]._add_entry(lineparsed.copy())
        # Assign storms to self.seasons dictionary; individual years as keys
        for tc in self.tc.items():
            if tc[1].year not in self.season: self.season[tc[1].year] = Season(tc[1].year)
            self.season[tc[1].year].tc[tc[0]] = tc[1]

    def rank_seasons(self, quantity, stattr, year1=None, year2=None, ascending=False):
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
                    "landfall_MHU", "TDonly", "TSonly", and "HUonly" are valid
                    storm attributes to rank by, their quantities will not be
                    visible in the ranking output.

        Default Arguments:
            year1 (None): begin year. If included, the indicated year will
                represent the low-end of years to assess. In the absence of
                the end-year, all years from this begin year to the end of the
                record-range will be used in ranking.
            year2 (None): end year. If included, the indicated year will
                represent the upper-end of years to assess. In the absence of
                the begin-year, all years from the start of the record-range
                to this indicated year will be used in ranking.
            ascending (False): bool to indicate sorting seasons in ascending
                (lower-to-higher) or not. The default of False implies seasons
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
                Retrieve a report of the bottom-5 seasons of, distance
                traversed by, at-least, tropical storms, all between 1951 and
                2000.
        <Hurdat2>.rank_seasons(10,"HUreach",year2=2000): Retrieves a report 
                of the top-10 seasons with the most Hurricanes prior-to, and
                including the year 2000.
        """
        ## Handle common errors
        if type(quantity) != int:
            return print("OOPS! Ensure the quantity entered is an integer!")
        if quantity <= 0:
            return print("OOPS! Ensure a quantity that is > 0")
        if year1 is not None and year2 is not None:
            if type(year1) != int or type(year2) != int:
                return print("OOPS! Make sure both passed years are integers!")
            if year1 >= year2:
                return print("OOPS! year1 cannot be greater than year2!")
        elif year1 is not None:
            if type(year1) != int:
                return print("OOPS! Make sure year1 is an integer!")
            elif year1 < self.record_range[0]:
                year1 = self.record_range[0]
        elif year2 is not None:
            if type(year2) != int:
                return print("OOPS! Make sure year2 is an integer!")
            elif year2 > self.record_range[1]:
                year2 = self.record_range[1]
        # --------------------
        sorted_hd2_items = sorted(self.season.items(),key=lambda s: getattr(s[1],stattr),reverse=True if ascending is False else False)
        if all(y is not None for y in [year1,year2]): sorted_hd2_items = [tu for tu in sorted_hd2_items if year1 <= tu[0] <= year2]
        elif year1 is not None and year2 is None: sorted_hd2_items = [tu for tu in sorted_hd2_items if year1 <= tu[0] <= self.record_range[1]]
        elif year2 is not None and year1 is None: sorted_hd2_items = [tu for tu in sorted_hd2_items if self.record_range[0] <= tu[0] <= year2]
        li_set_hd2_values = sorted(list(set([getattr(s[1],stattr) for s in sorted_hd2_items])),reverse=True if ascending is False else False)[:quantity]
        printedqty = []
        print("")
        print("{:^76}".format(
            "TOP {} SEASONS RANKED BY {}".format(
                quantity,
                stattr.upper(),
                # ", through {}".format(
                    # ""
                # ) if thru is not None else ""
            )
        ))
        print("{:^76}".format(
            "{}{}".format(
                str(self),
                ", {}{}{}".format(
                    year1 if year1 != None else self.record_range[0],
                    " - " if all([year1 != None,year2 != None]) else "-",
                    year2 if year2 != None else self.record_range[1]
                )
            )
        ))
        print("{:-^76}".format(""))
        
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
        for s in range(len(sorted_hd2_items)):
            if getattr(self.season[sorted_hd2_items[s][0]],stattr) in li_set_hd2_values:    
                if getattr(self.season[sorted_hd2_items[s][0]],stattr) == 0 and ascending is False: break
                print("{:>3}{:1}  {:4}  {:^6}  {:^4}  {:^4}  {:^4} {:^3}  {:>7.1f}  {:>{ACELEN}f}  {:>{ACELEN}f}  {:>{ACELEN}f}".format(
                    li_set_hd2_values.index(getattr(self.season[sorted_hd2_items[s][0]],stattr)) + 1 if li_set_hd2_values.index(getattr(self.season[sorted_hd2_items[s][0]],stattr)) + 1 not in printedqty else "",
                    "." if li_set_hd2_values.index(getattr(self.season[sorted_hd2_items[s][0]],stattr)) + 1 not in printedqty else "",
                    self.season[sorted_hd2_items[s][0]].year,
                    self.season[sorted_hd2_items[s][0]].tracks,
                    self.season[sorted_hd2_items[s][0]].landfall_TC,
                    self.season[sorted_hd2_items[s][0]].TSreach,
                    self.season[sorted_hd2_items[s][0]].HUreach,
                    self.season[sorted_hd2_items[s][0]].MHUreach,
                    self.season[sorted_hd2_items[s][0]].track_distance_TC,
                    self.season[sorted_hd2_items[s][0]].track_distance_TS if "track_distance" in stattr else self.season[sorted_hd2_items[s][0]].ACE * math.pow(10,-4),
                    self.season[sorted_hd2_items[s][0]].track_distance_HU if "track_distance" in stattr else self.season[sorted_hd2_items[s][0]].HDP * math.pow(10,-4),
                    self.season[sorted_hd2_items[s][0]].track_distance_MHU if "track_distance" in stattr else self.season[sorted_hd2_items[s][0]].MHDP * math.pow(10,-4),
                    ACELEN = 7.1 if "track_distance" in stattr else 7.3
                ))
                if li_set_hd2_values.index(getattr(self.season[sorted_hd2_items[s][0]],stattr)) + 1 not in printedqty:
                    printedqty.append(li_set_hd2_values.index(getattr(self.season[sorted_hd2_items[s][0]],stattr)) + 1)
            else: break
        print("")

    def rank_seasons_thru(self, quantity, stattr, thru=(12,31), year1=None, year2=None, ascending=False, **kw):
        """Rank and compare *partial* tropical cyclone seasons to one another.

        * Of note, if something is not provided for the <thru> positional
        keyword or the optional 'start' keyword, this function becomes a
        wrapper for <Hurdat2>.rank_seasons

        Required Arguments:
            quantity: how long of a list of ranks do you want; an integer.
            stattr: the storm attribute that you'd like to rank seasons by.
            
                * Storm Attributes: 
                    "tracks", "landfall_TC", "TSreach", "HUreach", "MHUreach",
                    "track_distance_TC", "ACE", "track_distance_TS", "HDP",
                    "track_distance_HU", "MHDP", "track_distance_MHU"

                * Note: Though attributes "track_distance", "landfalls", 
                    "landfall_TD", "landfall_TS", "landfall_HU",
                    "landfall_MHU", "TDonly", "TSonly", and "HUonly" are valid
                    storm attributes to rank by, their quantities will not be
                    visible in the ranking output.

        Default Arguments:
            thru = [12,31]: list/tuple representing the month and day that you
                want to assess the seasons through. In the absence of the
                optional keyword-value 'start', seasonal values will be
                calculated on dates from the start of the year through the
                requested date.
            year1 = None: begin year. If included, the indicated year will
                represent the low-end of years to assess. In the absence of
                the end-year, all years from this begin year to the end of the
                record-range will be used in ranking.
            year2 = None: end year. If included, the indicated year will
                represent the upper-end of years to assess. In the absence of
                the begin-year, all years from the start of the record-range
                to this indicated year will be used in ranking.
            ascending = False: bool to indicate sorting seasons in ascending
                (lower-to-higher) or not. The default of False implies seasons
                will be ranked from higher-to-lower.

        Keyword Arguments:
            start: list/tuple given to indicate the starting month and day
                wherein a season's calculations will be made.

        Examples:
        ---------
        <Hurdat2>.rank_seasons_thru(10,"ACE",[8,31]): Retrieve a report of
                tropical cyclone seasons sorted by the top-10 ACE values
                through August 31.
        <Hurdat2>.rank_seasons_thru(10,"TSreach",[9,15],1967): Retrieve a
                report of tropical cyclone seasons sorted by the top-10 totals
                of tropical storms through September 15, since 1967 (the
                satellite era).
        <Hurdat2>.rank_seasons_thru(5,"track_distance_TC",(8,15),start=[7,1]):
                Retrieve a report of the top-5 seasons of total distance
                traversed by any systems designated tropical cyclones, between
                July 1 and August 15.
        """
        ## Handle common errors
        if type(quantity) != int:
            return print("OOPS! Ensure the quantity entered is an integer!")
        if quantity <= 0:
            return print("OOPS! Ensure a quantity that is > 0")
        if type(thru) not in [list,tuple]:
            return print("OOPS! Ensure thru is a list or tuple of (month,day)")
        if year1 is not None and year2 is not None:
            if type(year1) != int or type(year2) != int:
                return print("OOPS! Make sure both passed years are integers!")
            if year1 >= year2:
                return print("OOPS! year1 cannot be greater than year2!")
        elif year1 is not None:
            if type(year1) != int:
                return print("OOPS! Make sure year1 is an integer!")
            elif year1 < self.record_range[0]:
                year1 = self.record_range[0]
        elif year2 is not None:
            if type(year2) != int:
                return print("OOPS! Make sure year2 is an integer!")
            elif year2 > self.record_range[1]:
                year2 = self.record_range[1]
        # --------------------
        start = kw.get("start",(1,1))
        if type(start) not in [list,tuple]:
            return print("OOPS! Ensure start is a list or tuple of (month,day)")

        if start == (1,1) and thru == (12,31):
            self.rank_seasons(quantity, stattr, year1, year2, ascending)
            return None
               
        rseason = {}
        for yr in self.season:
            rseason[yr] = dict(
                tracks = 0, landfalls=0, landfall_TC = 0, landfall_TD = 0,
                landfall_TS = 0, landfall_HU = 0, landfall_MHU = 0,
                TSreach = 0, HUreach = 0, MHUreach = 0, track_distance = 0,
                track_distance_TC = 0, track_distance_TS = 0,
                track_distance_HU = 0, track_distance_MHU = 0,
                ACE = 0, HDP = 0, MHDP = 0
            )
            for tc in [TrCy[1] for TrCy in self.season[yr].tc.items()]:
                track_added = False
                lndfls = False; lndfl_TC = False; lndfl_TD = False;
                lndfl_TS = False; lndfl_HU = False; lndfl_MHU = False;
                rTS = False; rHU = False; rMHU = False
                # STILL NEED TO ACCOUNT FOR TRACK_DISTANCE AND DATE RANGE
                entry_trk = [trk for trk in tc.entry if start <= trk.month_day_tuple <= thru]
                for trk in range(1,len(entry_trk)):
                    rseason[yr]["track_distance"] += haversine(entry_trk[trk-1].location, entry_trk[trk].location)
                    rseason[yr]["track_distance_TC"] += haversine(entry_trk[trk-1].location, entry_trk[trk].location) if entry_trk[trk-1].status in ("SD","TD","SS","TS","HU") else 0
                    rseason[yr]["track_distance_TS"] += haversine(entry_trk[trk-1].location, entry_trk[trk].location) if entry_trk[trk-1].status in ("SS","TS","HU") else 0
                    rseason[yr]["track_distance_HU"] += haversine(entry_trk[trk-1].location, entry_trk[trk].location) if entry_trk[trk-1].status == "HU" else 0
                    rseason[yr]["track_distance_MHU"] += haversine(entry_trk[trk-1].location, entry_trk[trk].location) if entry_trk[trk-1].status == "HU" and entry_trk[trk-1].wind >= 96 else 0
                for en in tc.entry:
                    if start <= en.month_day_tuple <= thru:
                        rseason[yr]["ACE"] += math.pow(en.wind,2) if en.wind >= 34 and en.status in ("SS","TS","HU") and en.entryhour in [0,6,12,18] and en.entryminute == 0 else 0
                        rseason[yr]["HDP"] += math.pow(en.wind,2) if en.wind >= 64 and en.status == "HU" and en.entryhour in [0,6,12,18] and en.entryminute == 0 else 0
                        rseason[yr]["MHDP"] += math.pow(en.wind,2) if en.wind >= 96 and en.status == "HU" and en.entryhour in [0,6,12,18] and en.entryminute == 0 else 0
                        if track_added is False:
                            rseason[yr]["tracks"] += 1
                            track_added = True
                        if lndfls is False and en.record_identifier is "L":
                            rseason[yr]["landfalls"] += 1
                            lndfls = True
                        if lndfl_TC is False and en.record_identifier is "L" and en.status in ["SD","TD","SS","TS","HU"]:
                            rseason[yr]["landfall_TC"] += 1
                            lndfl_TC = True
                        if lndfl_TD is False and en.record_identifier is "L" and en.status in ["SD","TD"]:
                            rseason[yr]["landfall_TD"] += 1
                            lndfl_TD = True
                        if lndfl_TS is False and en.record_identifier is "L" and en.status in ["SS","TS","HU"]:
                            rseason[yr]["landfall_TS"] += 1
                            lndfl_TS = True
                        if lndfl_HU is False and en.record_identifier is "L" and en.status == "HU":
                            rseason[yr]["landfall_HU"] += 1
                            lndfl_HU = True
                        if lndfl_MHU is False and en.record_identifier is "L" and en.status == "HU" and en.wind >= 96:
                            rseason[yr]["landfall_MHU"] += 1
                            lndfl_MHU = True
                        if rTS is False and en.status in ["SS","TS","HU"]:
                            rseason[yr]["TSreach"] += 1
                            rTS = True
                        if rHU is False and en.status in ["HU"]:
                            rseason[yr]["HUreach"] += 1
                            rHU = True
                        if rMHU is False and en.wind >= 96:
                            rseason[yr]["MHUreach"] += 1
                            rMHU = True

        sorted_hd2_items = sorted(self.season.items(),key=lambda s: rseason[s[0]][stattr], reverse=True if ascending is False else False)
        if all(y is not None for y in [year1,year2]): sorted_hd2_items = [tu for tu in sorted_hd2_items if year1 <= tu[0] <= year2]
        elif year1 is not None and year2 is None: sorted_hd2_items = [tu for tu in sorted_hd2_items if year1 <= tu[0] <= self.record_range[1]]
        elif year2 is not None and year1 is None: sorted_hd2_items = [tu for tu in sorted_hd2_items if self.record_range[0] <= tu[0] <= year2]
        li_set_hd2_values = sorted(list(set([rseason[s[0]][stattr] for s in sorted_hd2_items])),reverse=True if ascending is False else False)[:quantity]
        printedqty = []
        print("")
        print("{:^75}".format(
            "TOP {} SEASONS RANKED BY {}, {}".format(
                quantity,
                stattr.upper(),
                "{}through {}".format(
                    "from {} ".format(
                        "{} {}".format(
                            calendar.month_abbr[start[0]], start[1]
                        )
                    ) if "start" in kw else "",
                    "{} {}".format(
                        calendar.month_abbr[thru[0]], thru[1]
                    )
                )
            )
        ))
        print("{:^75}".format(
            "{}{}".format(
                str(self),
                ", {}{}{}".format(
                    year1 if year1 is not None else self.record_range[0],
                    " - " if all([year1 is not None,year2 is not None]) else "-",
                    year2 if year2 is not None else self.record_range[1]
                )
            )
        ))
        print("{:-^75}".format(""))
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
        for s in range(len(sorted_hd2_items)):
            if rseason[sorted_hd2_items[s][0]][stattr] in li_set_hd2_values:
                if rseason[sorted_hd2_items[s][0]][stattr] == 0 and ascending is False: break

                print("{:>3}{:1}  {:4}  {:^6}  {:^4}  {:^4} {:^4} {:^3}  {:>7.1f}  {:>{ACELEN}f}  {:>{ACELEN}f}  {:>{ACELEN}f}".format(
                    li_set_hd2_values.index(rseason[sorted_hd2_items[s][0]][stattr]) + 1 if li_set_hd2_values.index(rseason[sorted_hd2_items[s][0]][stattr]) + 1 not in printedqty else "",
                    "." if li_set_hd2_values.index(rseason[sorted_hd2_items[s][0]][stattr]) + 1 not in printedqty else "",
                    sorted_hd2_items[s][0],
                    rseason[sorted_hd2_items[s][0]]["tracks"],
                    rseason[sorted_hd2_items[s][0]]["landfall_TC"],
                    rseason[sorted_hd2_items[s][0]]["TSreach"],
                    rseason[sorted_hd2_items[s][0]]["HUreach"],
                    rseason[sorted_hd2_items[s][0]]["MHUreach"],
                    rseason[sorted_hd2_items[s][0]]["track_distance_TC"],
                    rseason[sorted_hd2_items[s][0]]["track_distance_TS"] if "track_distance" in stattr else rseason[sorted_hd2_items[s][0]]["ACE"] * math.pow(10,-4),
                    rseason[sorted_hd2_items[s][0]]["track_distance_HU"] if "track_distance" in stattr else rseason[sorted_hd2_items[s][0]]["HDP"] * math.pow(10,-4),
                    rseason[sorted_hd2_items[s][0]]["track_distance_MHU"] if "track_distance" in stattr else rseason[sorted_hd2_items[s][0]]["MHDP"] * math.pow(10,-4),
                    ACELEN = 7.1 if "track_distance" in stattr else 7.3
                ))
                if li_set_hd2_values.index(rseason[sorted_hd2_items[s][0]][stattr]) + 1 not in printedqty:
                    printedqty.append(li_set_hd2_values.index(rseason[sorted_hd2_items[s][0]][stattr]) + 1)
            else: break
        print("")
        pass

    def rank_storms(self, quantity, stattr, year1=None, year2=None, coordextent=None):
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
                    "landfall_MHU", "TSreach", "HUreach", "MHUreach"

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
                bounding-box. If included, the ranking results will be narrowed
                to storms whose genesis occurred in the bounding box. This
                could be used to compare storms that were born in a relatively
                similar location. BE AWARE, that just because a storm's genesis
                occurred within a certain bounding box, it does not mean that
                the sought-after rank attribute occurred while the storm was
                located within that same coordinate extent.

        Examples:
        ---------
        <Hurdat2>.rank_storms(10,"ACE"): Retrieve a report of tropical
                cyclones sorted by the top-10 values of Accumulated Cyclone
                Energy on record.
        <Hurdat2>.rank_storms(20,"HDP",1967): Retrieve a report of tropical
                cyclones sorted by the top-20 values of Hurricane Destruction
                Potential since 1967 (the beginning of the satellite era).
        <Hurdat2>.rank_storms(5,"minmslp",1901,1940): Retrieve a report of the
                top-5 tropical cyclones with the lowest minimum pressure
                readings between 1901 and 1940.
        <Hurdat2>.rank_storms(10, "maxwind", coordextent=[(31,-98), (18,-80)])
                Retrieve a report of the top 10 storms, ranked by max-wind,
                whose genesis occurred in (roughly) the Gulf of Mexico.
        """
        if type(quantity) != int:
            return print("OOPS! type(quantity) must be an integer.")
        if hasattr(self.tc[next(iter(self.tc))],stattr) is False:
            return print("OOPS! <class TropicalCyclone> has no attribute named '{}'.".format(stattr))
        if type(getattr(self.tc[next(iter(self.tc))],stattr)) == bool:
            return print("OOPS! stattr, the storm attribute, cannot be a boolean")
        if any([year1 != None and type(year1) != int, year2 != None and type(year2) != int]):
            return print("OOPS! If included, ensure that year1 and/or year2 are integers!")
        if year1 is not None and year2 is not None and year1 >= year2:
            return print("OOPS! year1 cannot be greater than year2!")
        if year1 is not None and year1 < self.record_range[0]:
            year1 = self.record_range[0]
        if year2 is not None and year2 > self.record_range[1]:
            year2 = self.record_range[1]
        #sorted_hd2_items = sorted(self.tc.items(),key=lambda h: getattr(h[1],stattr) if getattr(h[1],stattr) != None else 9999,reverse=False if stattr is "minmslp" else True)
        sorted_hd2_items = sorted([TC for TC in self.tc.items() if getattr(TC[1],stattr) is not None],key=lambda i: getattr(i[1],stattr),reverse=False if stattr is "minmslp" else True)
        if coordextent is not None:
            sorted_hd2_items = [TC for TC in sorted_hd2_items if self.coord_contains(TC[1].entry[0].location, coordextent[0], coordextent[1])]
        if all(y != None for y in [year1,year2]): sorted_hd2_items = [tu for tu in sorted_hd2_items if year1 <= int(tu[0][4:]) <= year2]
        elif year1 != None and year2 is None: sorted_hd2_items = [tu for tu in sorted_hd2_items if year1 <= int(tu[0][4:]) <= self.record_range[1]]
        li_set_hd2_values = sorted(list(set([getattr(h[1],stattr) if getattr(h[1],stattr) != None else 9999 for h in sorted_hd2_items])),reverse=False if stattr is "minmslp" else True)[:quantity]
        #print(li_set_hd2_values)
        #for x in set([tu[1].name for tu in sorted_hd2_items]): print('"{}", len = {}'.format(x,len(x)))
        #for tu in sorted_hd2_items[:10]: print(tu[0],tu[1].name)
        printedqty = []
        print("")
        print("{:^72}".format("TOP {} STORMS RANKED BY {}".format(
            quantity,
            stattr.upper()
        )))
        if coordextent is not None:
            print("{:^72}".format(
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
        # ", {}-{}".format(year1,year2) if all(y != None for y in [year1,year2] and year1 != year2)
        # ", {}".format(self.record_range[1]) if year1 == self.record_range[1]
        # ", {}".format(year1) if year1 == year2
        # ",{}-{}".format(year1,self.record_range[1]) if year1 != None and year2 is None
        # ""
        print("{:^72}".format(
            "{}{}".format(
                str(self),
                ", {}{}{}".format(
                    year1 if year1 != None else self.record_range[0],
                    " - " if all([year1 != None,year2 != None]) else "-",
                    year2 if year2 != None else self.record_range[1]
                )
            )
        ))
        print("{:-^72}".format(""))
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
        #print(len(sorted_hd2_items))
        #print(len(li_set_hd2_values))
        for h in range(len(sorted_hd2_items)):
            if getattr(self.tc[sorted_hd2_items[h][0]],stattr) in li_set_hd2_values:
                if getattr(self.tc[sorted_hd2_items[h][0]],stattr) <= 0: break
                print("{:>3}{:1}  {:<10} {:8} {:^4} {:>4} {:>4}  {:>6.1f}  {:>{ACELEN}f}  {:>{ACELEN}f}  {:>{ACELEN}f}".format(
                    li_set_hd2_values.index(getattr(self.tc[sorted_hd2_items[h][0]],stattr)) + 1 if li_set_hd2_values.index(getattr(self.tc[sorted_hd2_items[h][0]],stattr)) + 1 not in printedqty else "",
                    "." if li_set_hd2_values.index(getattr(self.tc[sorted_hd2_items[h][0]],stattr)) + 1 not in printedqty else "",
                    self.tc[sorted_hd2_items[h][0]].name.title(),
                    self.tc[sorted_hd2_items[h][0]].atcfid,
                    self.tc[sorted_hd2_items[h][0]].landfalls,
                    self.tc[sorted_hd2_items[h][0]].minmslp if self.tc[sorted_hd2_items[h][0]].minmslp is not None else "N/A",
                    self.tc[sorted_hd2_items[h][0]].maxwind if self.tc[sorted_hd2_items[h][0]].maxwind > 0 else "N/A",
                    self.tc[sorted_hd2_items[h][0]].track_distance_TC,
                    self.tc[sorted_hd2_items[h][0]].track_distance_TS if "track" in stattr else self.tc[sorted_hd2_items[h][0]].ACE * math.pow(10,-4),
                    self.tc[sorted_hd2_items[h][0]].track_distance_HU if "track" in stattr else self.tc[sorted_hd2_items[h][0]].HDP * math.pow(10,-4),
                    self.tc[sorted_hd2_items[h][0]].track_distance_MHU if "track" in stattr else self.tc[sorted_hd2_items[h][0]].MHDP * math.pow(10,-4),
                    ACELEN = 6.1 if "track" in stattr else 6.3
                ))
                if li_set_hd2_values.index(getattr(self.tc[sorted_hd2_items[h][0]],stattr)) + 1 not in printedqty:
                    printedqty.append(li_set_hd2_values.index(getattr(self.tc[sorted_hd2_items[h][0]],stattr)) + 1)
            else: break
        print("")

    def rank_climo(self, quantity, stattr, year1=None, year2=None, ascending=False, **climoparam):
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
                    "landfall_MHU", "TSreach", "HUreach", "MHUreach"

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

        class LAMBDA_CLASS:
            def __init__(self,**kw):
                self.__dict__ = kw

        climo = {}
        for yr in range(
            #self.record_range[0] if year1 is None else year1,
            1801,
            self.record_range[1] + 1 if year2 is None else year2 + 1,
            increment
        ):
            if yr in range(self.record_range[0], self.record_range[1] + 1) and yr + climatology-1 in range(self.record_range[0], self.record_range[1] + 1):
                climo[(yr, yr+climatology-1)] = LAMBDA_CLASS(
                    tracks = sum([self.season[s].tracks for s in range(yr, yr+climatology)]),
                    landfalls = sum([self.season[s].landfalls for s in range(yr, yr+climatology)]),
                    landfall_TC = sum([self.season[s].landfall_TC for s in range(yr, yr+climatology)]),
                    landfall_TD = sum([self.season[s].landfall_TD for s in range(yr, yr+climatology)]),
                    landfall_TS = sum([self.season[s].landfall_TS for s in range(yr, yr+climatology)]),
                    landfall_HU = sum([self.season[s].landfall_HU for s in range(yr, yr+climatology)]),
                    landfall_MHU = sum([self.season[s].landfall_MHU for s in range(yr, yr+climatology)]),
                    TSreach = sum([self.season[s].TSreach for s in range(yr, yr+climatology)]),
                    TSonly = sum([self.season[s].TSonly for s in range(yr, yr+climatology)]),
                    HUreach = sum([self.season[s].HUreach for s in range(yr, yr+climatology)]),
                    HUonly = sum([self.season[s].HUonly for s in range(yr, yr+climatology)]),
                    MHUreach = sum([self.season[s].MHUreach for s in range(yr, yr+climatology)]),
                    track_distance = sum([self.season[s].track_distance for s in range(yr, yr+climatology)]),
                    track_distance_TC = sum([self.season[s].track_distance_TC for s in range(yr, yr+climatology)]),
                    track_distance_TS = sum([self.season[s].track_distance_TS for s in range(yr, yr+climatology)]),
                    track_distance_HU = sum([self.season[s].track_distance_HU for s in range(yr, yr+climatology)]),
                    track_distance_MHU = sum([self.season[s].track_distance_MHU for s in range(yr, yr+climatology)]),
                    ACE = sum([self.season[s].ACE for s in range(yr, yr+climatology)]),
                    HDP = sum([self.season[s].HDP for s in range(yr, yr+climatology)]),
                    MHDP = sum([self.season[s].MHDP for s in range(yr, yr+climatology)])
                )
        if "op" in climoparam:
            return climo
        sorted_climo_items = sorted(climo.items(),key=lambda s: getattr(s[1],stattr),reverse=True if ascending is False else False)
        li_set_climo_values = sorted(list(set([getattr(s[1],stattr) for s in sorted_climo_items])),reverse=True if ascending is False else False)[:quantity]
        printedqty = []
        print("")
        print("{:^41}".format(
            "TOP {} CLIMATOLOGICAL PERIODS".format(quantity)
        ))
        print("{:^41}".format(
            "RANKED BY {}".format(stattr.upper())
        ))
        print("{:^41}".format(
            "{}{}".format(
                str(self),
                ", {}{}{}".format(
                    year1 if year1 != None else self.record_range[0],
                    " - " if all([year1 != None,year2 != None]) else "-",
                    year2 if year2 != None else self.record_range[1]
                )
            )
        ))
        print("{:-^41}".format(""))
        print("{:^41}".format(
            "{}-Year Climatologies; {}-Year Incremented".format(
                climatology,
                increment
            )
        ))
        print("{:-^41}".format(""))
        #rank = itertools.counter(1)
        print(" {:^4}  {:^9}  {:^12}".format(
            "RANK",
            "PERIOD",
            stattr.upper()
        ))
        print(" {:-^4}  {:-^9}  {:-^12}".format(
            "","",""
        ))
        for s in range(len(sorted_climo_items)):
            if getattr(sorted_climo_items[s][1],stattr) in li_set_climo_values:
                if getattr(sorted_climo_items[s][1],stattr) == 0 and ascending is False: break
                print(" {:>4}  {:9}  {}".format(
                    "{:>3}{:1}".format(
                        li_set_climo_values.index(getattr(sorted_climo_items[s][1],stattr)) + 1 if li_set_climo_values.index(getattr(sorted_climo_items[s][1],stattr)) + 1 not in printedqty else "",
                        "." if li_set_climo_values.index(getattr(sorted_climo_items[s][1],stattr)) + 1 not in printedqty else ""
                    ),
                    "{}-{}".format(
                        sorted_climo_items[s][0][0],
                        sorted_climo_items[s][0][1]
                    ),
                    getattr(sorted_climo_items[s][1],stattr)
                ))
                if li_set_climo_values.index(getattr(sorted_climo_items[s][1],stattr)) + 1 not in printedqty:
                    printedqty.append(li_set_climo_values.index(getattr(sorted_climo_items[s][1],stattr)) + 1)
            else: break
        print("")

    def multi_season_info(self, year1=None, year2=None):
        """Grab a chunk of multi-season data and report on that climate era.
        This method can be viewed as a climatological era info method.
        
        Default Arguments:
            year1 (None): The start year
            year2 (None): The end year
        """
        # Common Error Handling
        if year1 is None: year1 = self.record_range[0]
        if year2 is None: year2 = self.record_range[1]
        if type(year1) != int or type(year2) != int:
            return print("* OOPS! Requested years must be integers!")
        if year2 <= year1:
            return print("* OOPS! Year 2 must be > Year 1")
        if year2 > self.record_range[1]:  # set year2 to max year if needed
            year2 = self.record_range[1]
        if year1 < self.record_range[0]:  # set year1 to max year if needed
            year1 = self.record_range[0]
        # ---------------------

        class LAMBDA_CLASS:
            def __init__(self,**kw):
                self.__dict__ = kw

        clmt = LAMBDA_CLASS(
            y1 = year1, y2 = year2, tracks = 0, landfalls=0, landfall_TC = 0,
            landfall_TD = 0, landfall_TS = 0, landfall_HU = 0,
            landfall_MHU = 0, TSonly = 0, TSreach = 0, HUonly = 0, HUreach = 0, MHUreach = 0,
            track_distance = 0, track_distance_TC = 0, track_distance_TS = 0,
            track_distance_HU = 0, track_distance_MHU = 0, ACE = 0, HDP = 0,
            MHDP = 0
        )

        for y in range(year1,year2+1):
            clmt.tracks += self.season[y].tracks
            clmt.landfalls += self.season[y].landfalls
            clmt.landfall_TC += self.season[y].landfall_TC
            clmt.landfall_TD += self.season[y].landfall_TD
            clmt.landfall_TS += self.season[y].landfall_TS
            clmt.landfall_HU += self.season[y].landfall_HU
            clmt.landfall_MHU += self.season[y].landfall_MHU
            clmt.TSreach += self.season[y].TSreach
            clmt.TSonly += self.season[y].TSonly
            clmt.HUreach += self.season[y].HUreach
            clmt.HUonly += self.season[y].HUonly
            clmt.MHUreach += self.season[y].MHUreach
            clmt.track_distance += self.season[y].track_distance
            clmt.track_distance_TC += self.season[y].track_distance_TC
            clmt.track_distance_TS += self.season[y].track_distance_TS
            clmt.track_distance_HU += self.season[y].track_distance_HU
            clmt.track_distance_MHU += self.season[y].track_distance_MHU
            clmt.ACE += self.season[y].ACE
            clmt.HDP += self.season[y].HDP
            clmt.MHDP += self.season[y].MHDP
        # Print Report
        totalyrs = clmt.y2-clmt.y1 + 1
        print("")
        print(" --------------------------------------------------------")
        print(" Tropical Cyclone Season Stats, for {} to {}".format(clmt.y1,clmt.y2))
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

    def storm_name_search(self, searchname, info=True):
        """Search the Hurdat2 object's records by storm name. Returns the
        matches info method or returns the matching object itself.

        Required Argument:
            searchname: the storm name to search

        Default Arguments:
            info = True: if True, the method will return the info method of the
            chosen search result. Otherwise it will simply return the object
            (used in __getitem__)
        """
        searchname = searchname.upper()     # Capitalize the search term

        # 1st pass - Limit the search results to exact matches
        matchlist = [(TC[1], 1.0) for TC in self.tc.items() if searchname == TC[1].name]
        # 2nd pass - Limit the search results by requiring that
        #            the first is letter correct
        if len(matchlist) == 0:
            matchlist = sorted(
                [
                    (TC[1], difflib.SequenceMatcher(None, searchname, TC[1].name).quick_ratio()) for TC in self.tc.items() if TC[1].name[0] == searchname[0]
                ], key=lambda t: t[1], reverse=True
            )
        #3rd pass - if necessary; if no match found
        if len(matchlist) == 0:
            matchlist = sorted([
                (TC[1], difflib.SequenceMatcher(None, searchname, TC[1].name).quick_ratio()) for TC in self.tc.items()
            ], key=lambda t: t[1], reverse=True)
        # No Matches Determined
        if len(matchlist) == 0:
            return print("* No Matches Found for '{}'*".format(searchname))
        # If only one match found, return it!
        elif len(matchlist) == 1:
            # Manual Search call
            if info is True:
                return matchlist[0][0].info()
            # Indexing being attempted; return TropicalCyclone Object
            else:
                return matchlist[0][0]
        # Display a choice for multiple matches
        else:
            i = itertools.count(1)
            for opt in matchlist[:5]:
                print("{}. {} - {}{}".format(
                    next(i),
                    opt[0].atcfid,
                    "{} ".format(
                        opt[0].status_highest if opt[0].name != "UNNAMED" else ""
                    ),
                    opt[0].name.title() if opt[0].name != "UNNAMED" else opt[0].name
                ))
            print("")
            while True:
                choice = input("Which storm are you inquiring about? ")
                if choice.isnumeric() \
                and 1 <= int(choice) <= len(matchlist[:5]):
                    if info is True:
                        return matchlist[int(choice) - 1][0].info()
                    else:
                        return matchlist[int(choice) - 1][0]
                else:
                    print("* OOPS! Invalid Entry! Try again.")

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
        climo = self.rank_climo(10,"tracks",climatology=climo_len,increment=1,op=True)
        with open(ofn, "w", newline="") as w:
            out = csv.writer(w)
            out.writerow([
                "Climatology", "TC Qty", "Trk Dist", "Landfalls (Acc.)",
                "TC Landfall", "TS Landfall", "HU Landfall", "MHU Landfall",
                "TC Trk Dist", "TS", "ACE", "TS Trk Dist", "TS-Excl", "HU",
                "HDP", "HU Trk Dist", "HU-1and2", "MHU", "MHDP", "MHU Trk Dist"
            ])
            for clmt in climo.items():
                out.writerow([
                    "{}-{}".format(
                        clmt[0][0],
                        clmt[0][1]
                    ),
                    clmt[1].tracks,
                    clmt[1].track_distance,
                    clmt[1].landfalls,
                    clmt[1].landfall_TC,
                    clmt[1].landfall_TS,
                    clmt[1].landfall_HU,
                    clmt[1].landfall_MHU,
                    clmt[1].track_distance_TC,
                    clmt[1].TSreach,
                    clmt[1].ACE,
                    clmt[1].track_distance_TS,
                    clmt[1].TSonly,
                    clmt[1].HUreach,
                    clmt[1].HDP,
                    clmt[1].track_distance_HU,
                    clmt[1].HUonly,
                    clmt[1].MHUreach,
                    clmt[1].MHDP,
                    clmt[1].track_distance_MHU
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
        pass

    @staticmethod
    def coord_contains(testcoord, ux, lx):
        """Returns True or False whether the coordinates (testcoord) would be
        contained in a box defined by 'upper' coordinates (ux) and 'lower'
        coordinates (lx).
        """
        if lx[0] <= testcoord[0] <= ux[0] and ux[1] <= testcoord[1] <= lx[1]: return True
        else: return False

    @property
    def record_range(self):
        """Returns a tuple containing the beginning and end seasons covered by
        the Hurdat2 object.
        """
        ylist = [int(yrkey[4:]) for yrkey in self.tc.keys()]
        yfirst = min(ylist)
        ylast = max(ylist)
        return (yfirst,ylast)

class Season:
    """Represents a single hurricane season; represented by its year."""
    def __init__(self,yr):
        self.year = yr
        self.tc = {}

    def __len__(self):
        """Returns the number of tropical cyclones from a particular season."""
        return len(self.tc)

    def __getitem__(self, s):
        # Storm Number passed
        if type(s) == int:
            return self.tc[list(self.tc.keys())[s-1]]
        # ATCFID or NAME or LETTER
        elif type(s) == str:
            ids = [self.tc[trop].atcfid for trop in self.tc]    # ATCF ID List
            nms = [self.tc[trop].name for trop in self.tc]  # Storm Name List
            if str(s).upper() in ids:
                return self.tc[str(s).upper()]
            elif str(s).upper() in nms:
                return self.tc[list(self.tc.keys())[nms.index(str(s).upper())]]
            elif len(str(s)) >= 1:
                match = [tc[1] for tc in self.tc.items() if str(s)[0].upper() == tc[1].name[0]]
                if len(match) == 0:
                    print("* No matches found!")
                elif len(match) == 1:
                    return match[0]
                else:
                    i = itertools.count(1)
                    for opt in match:
                        print("{}. {} - {}{}".format(
                            next(i),
                            opt.atcfid,
                            "{} ".format(
                                opt.status_highest if opt.name != "UNNAMED" else ""
                            ),
                            opt.name.title() if opt.name != "UNNAMED" else opt.name
                        ))
                    while True:
                        choice = input("Which storm are you inquiring about? ")
                        if choice.isnumeric() \
                        and 1 <= int(choice) <= len(match):
                            return match[int(choice) - 1]
                        else:
                            print("* OOPS! Invalid Entry! Try again.")
            else:
                return self.tc[s]   # invalid key; will raise error
        else: return self.tc[s]   # invalid key; will raise error

    def info(self):
        """Returns a basic report of accumulated information from all storms
        specific to the tropical cyclone season.
        """
        print("")
        print("{:-^40}".format(""))
        print("{:^40}".format("Tropical Cyclone Stats for {}".format(self.year)))
        print("{:^40}".format(
            "Atlantic Basin" if list(self.tc.keys())[0][0] == "A" else "East/Central Pacific Basin"
        ))
        print("")
        print("{:^40}".format(
            "* TS-related Statistics include"
        ))
        print("{:^40}".format(
            "Hurricanes in their totals"
        ))
        print("{:^40}".format(
            "except for landfall data"
        ))
        print("{:-^40}".format(""))
        print("* Tracked Systems: {}".format(len(self)))
        print("* TC Track Distance: {:.1f} nmi".format(self.track_distance_TC))
        print("  -- TS Distance: {:.1f} nmi".format(self.track_distance_TS))
        print("  -- HU Distance: {:.1f} nmi".format(self.track_distance_HU))
        print("  -- MHU Distance: {:.1f} nmi".format(self.track_distance_MHU))
        print("* Tropical Storms: {}".format(self.TSreach))
        print("* ACE: {:.3f} * 10^4 kt^2".format(self.ACE * math.pow(10,-4))) if self.ACE > 0 else None
        print("* Hurricanes: {}".format(self.HUreach))
        print("* HDP: {:.3f} * 10^4 kt^2".format(self.HDP * math.pow(10,-4))) if self.HDP > 0 else None
        print("* Major Hurricanes: {}".format(self.MHUreach))
        print("* MHDP: {:.3f} * 10^4 kt^2".format(self.MHDP * math.pow(10,-4))) if self.MHDP > 0 else None
        print("* Total Landfalling TC's: {}".format(self.landfall_TC))
        print("  -- TS Landfalls: {}".format(self.landfall_TS))
        print("  -- HU Landfalls: {}".format(self.landfall_HU))
        print("")

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
            print("{:^67}".format(
                "Atlantic Basin" if list(self.tc.keys())[0][0] == "A" else "East/Central Pacific Basin"
            ))
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
                entiretrack = [self.tc[trop].entry[trk].location_rev for trk in range(len(self.tc[trop].entry))]
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
                        gis.line([[TC.entry[track].location_rev,TC.entry[track+1].location_rev]])
                    else:
                        gis.null()

    def output_geojson(self, INDENT=None):
        """Uses the geojson module to output a GIS-compatible geojson of the
        tracks of all storms documented during a particular season. It is
        output to the current directory.

        Default Argument:
            INDENT = None; used to provide indention to the output. Though it
                makes the output prettier and easier to read, it increases the
                file size.
        """
        ofn = "{}_{}_tracks.geojson".format(
            self.year,
            "ATL" if list(self.tc.keys())[0][:2] == "AL" else "PAC"
        )
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
                "ACE (x10^4)": round(TC.MHDP * math.pow(10,-4), 3),
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

    def output_geojson_segmented(self, INDENT=None):
        """Uses the geojson module to output a GIS-compatible geojson of
        individual segments (as separate geometries) of each system from the
        season. Use this if you'd like the idea of coloring the tracks by
        saffir-simpson strength controlled by the segments.

        Default Argument:
            INDENT = None; used to provide indention to the output. Though it
                makes the output prettier and easier to read, it increases the
                file size.
        """
        ofn = "{}_{}_tracks_segmented.geojson".format(
            self.year,
            "ATL" if list(self.tc.keys())[0][:2] == "AL" else "PAC"
        )
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
    def track_distance(self):
        """Returns the accumulated track distances (in nmi) of all systems
        during the season, regardless of the systems' status.
        """
        return sum([self.tc[TC].track_distance for TC in self.tc])

    @property
    def track_distance_TC(self):
        """Returns the accumulated track distances (in nmi) of all systems
        during the season, while the systems were designated as tropical
        cyclones ("SD","SS","TD","TS","HU").
        """
        return sum([self.tc[TC].track_distance_TC for TC in self.tc])

    @property
    def ACE(self):
        """Returns the accumulated cyclone energy (ACE) for the entire season,
        being the sum of all individual tropical cyclone ACE's.
        """
        return sum([self.tc[trop].ACE for trop in self.tc])

    @property
    def track_distance_TS(self):
        """Returns the sum of track distances (in nmi) of all tropical
        cyclones while they were designated as at-least tropical storms (SS,
        TS, or HU).
        """
        return sum([self.tc[TC].track_distance_TS for TC in self.tc])

    @property
    def HDP(self):
        """Returns the hurricane destruction potential (HDP) for the entire
        season, being the sum of all individual tropical cyclone HDP's.
        """
        return sum([self.tc[trop].HDP for trop in self.tc])

    @property
    def track_distance_HU(self):
        """Returns the sum of track distances (in nmi) of all tropical
        cyclones while they were of hurricane status.
        """
        return sum([self.tc[TC].track_distance_HU for TC in self.tc])

    @property
    def MHDP(self):
        """Returns the major hurricane destruction potential (MHDP) for the
        entire season, being the sum of all individual tropical cyclone MHDP's.
        """
        return sum([self.tc[trop].MHDP for trop in self.tc])

    @property
    def track_distance_MHU(self):
        """Returns the sum of track distances (in nmi) of all tropical
        cyclones when the storms were designated as major hurricanes.
        """
        return sum([self.tc[TC].track_distance_MHU for TC in self.tc])

class TropicalCyclone:
    """Object holding data for an individual tropical cyclone."""
    def __init__(self,storm_id,storm_name):
        self.atcfid = storm_id
        self.atcf_num = int(storm_id[2:4])
        self.year = int(storm_id[4:])
        self.name = storm_name
        self.entry = []     # List to keep track of indiv time entries

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

    def _add_entry(self,tcrecord):
        """Adds a time-entry record for a particular storm. This method should
        not be accessed by users directly.
        """
        self.entry.append(TCRecordEntry(tcrecord))
        #self.gps.append(self.entry[-1].location)

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
                    gis.line([[self.entry[track].location_rev,self.entry[track+1].location_rev]])
                else: gis.null()

    def output_geojson(self, INDENT=None):
        """Uses the geojson module to output a geojson file of the tropical
        cyclone.

        Default Argument:
            INDENT = None; used to provide indention to the output. Though it
                makes the output prettier and easier to read, it increases the
                file size.
        """
        ofn = "{}_{}_tracks.geojson".format(self.atcfid,self.name)
        feats = []
        for trk in range(len(self.entry)):
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
    def track_distance(self):
        """Returns the distance (in nmi) traversed by the system, regardless of
        status (whether or not the system is designated as a tropical cyclone).
        """
        d = 0
        for trk in range(1,len(self.entry)):
            d += haversine(self.entry[trk-1].location, self.entry[trk].location)
        return d

    @property
    def track_distance_TC(self):
        """The distance (in nmi) trekked by the system when a designated
        tropical cyclone (status as a tropical or sub-tropical depression, a
        tropical or sub-tropical storm, or a hurricane).
        """
        d = 0
        for trk in range(1,len(self.entry)):
            if self.entry[trk-1].status in ("SD","TD","SS","TS","HU"):
                d += haversine(self.entry[trk-1].location, self.entry[trk].location)
        return d

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
            [math.pow(t.wind,2) for t in self.entry \
                if t.wind >= 34 \
                and t.entryhour in [0,6,12,18] \
                and t.entryminute == 0 \
                and t.status in ("SS","TS","HU")]
        )

    @property
    def track_distance_TS(self):
        """The distance (in nmi) trekked by the system while a tropical storm
        or hurricane.
        """
        d = 0
        for trk in range(1,len(self.entry)):
            if self.entry[trk-1].status in ("SS","TS","HU"):
                d += haversine(self.entry[trk-1].location, self.entry[trk].location)
        return d

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
            [math.pow(t.wind,2) for t in self.entry \
                if t.wind >= 64 \
                and t.entryhour in [0,6,12,18] \
                and t.entryminute == 0 \
                and t.status == "HU"]
        )

    @property
    def track_distance_HU(self):
        """The distance (in nmi) trekked by the system while a hurricane."""
        d = 0
        for trk in range(1,len(self.entry)):
            if self.entry[trk-1].status == "HU":
                d += haversine(self.entry[trk-1].location, self.entry[trk].location)
        return d

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
            [math.pow(t.wind,2) for t in self.entry \
                if t.wind >= 96 \
                and t.entryhour in [0,6,12,18] \
                and t.entryminute == 0 \
                and t.status == "HU"]
        )

    @property
    def track_distance_MHU(self):
        """The distance (in nmi) trekked by the system while a major
        hurricane.
        """
        d = 0
        for trk in range(1,len(self.entry)):
            if self.entry[trk-1].status == "HU" and self.entry[trk-1].wind >= 96:
                d += haversine(self.entry[trk-1].location, self.entry[trk].location)
        return d

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

class TCRecordEntry:
    """Object that holds information from one individual (one line) HURDAT2
    entry.
    """
    def __init__(self,tc_entry):
        self.entryday = datetime.date(
            int(tc_entry[0][:4]),
            int(tc_entry[0][4:6]),
            int(tc_entry[0][6:])
        )
        self.entryhour = int(tc_entry[1][:2])
        self.entryminute = int(tc_entry[1][2:])
        self.entrytime = datetime.datetime(
            self.entryday.year,
            self.entryday.month,
            self.entryday.day,
            hour=self.entryhour,
            minute=self.entryminute
        )
        self.hour_minute_tuple = (self.entryhour, self.entryminute)
        self.month_day_tuple = (self.entrytime.month,self.entrytime.day)
        self.record_identifier = tc_entry[2] if tc_entry[2] != '' else None
        self.status = tc_entry[3]
        self.lat_str = tc_entry[4]
        self.lon_str = tc_entry[5]
        self.location = coord(self.lat_str,self.lon_str)
        self.lat = self.location[0]
        self.lon = self.location[1]
        self.location_rev = (self.lon,self.lat)
        self.wind = int(tc_entry[6])
        self.status_desc = format_status(self.status,self.wind)
        self.saffir_equiv = saffir_simpson(self.wind)
        self.mslp = int(tc_entry[7]) if tc_entry[7] != '-999' else None
        # Extent Indices - 0 = NE, 1 = SE, 2 = SW, 3 = NW
        self.extent_TS = [
            int(tc_entry[8]) if tc_entry[8] != '-999' else None,
            int(tc_entry[9]) if tc_entry[9] != '-999' else None,
            int(tc_entry[10]) if tc_entry[10] != '-999' else None,
            int(tc_entry[11]) if tc_entry[11] != '-999' else None,
        ]
        self.extent_TS50 = [
            int(tc_entry[12]) if tc_entry[12] != '-999' else None,
            int(tc_entry[13]) if tc_entry[13] != '-999' else None,
            int(tc_entry[14]) if tc_entry[14] != '-999' else None,
            int(tc_entry[15]) if tc_entry[15] != '-999' else None,
        ]
        self.extent_HU = [
            int(tc_entry[16]) if tc_entry[16] != '-999' else None,
            int(tc_entry[17]) if tc_entry[17] != '-999' else None,
            int(tc_entry[18]) if tc_entry[18] != '-999' else None,
            int(tc_entry[19]) if tc_entry[19] != '-999' else None,
        ]

    def dump(self):
        """Dumps a one-line summary of the most-essential aspects of the
        entry.
        """
        print("{} :: {} :: {:1} :: {:>5}, {:>5} :: {:>3} kts :: {}".format(
            self.entrytime,
            self.status,
            self.record_identifier if self.record_identifier is not None else "",
            self.lat_str,
            self.lon_str,
            self.wind,
            "{:>4} hPa".format(self.mslp) if self.mslp is not None else "N/A"
        ))

    def dump_hurdat2(self):
        """Dumps a hurdat2-formatted line of the entry information. It should
        be identical to the corresponding entry in the actual Hurdat2 record.
        """
        print("{:>8},{:>5},{:>2},{:>3},{:>6},{:>7},{:>4},{:>5},{:>5},{:>5},{:>5},{:>5},{:>5},{:>5},{:>5},{:>5},{:>5},{:>5},{:>5},{:>5},".format(
            "{:%Y%m%d}".format(self.entrytime),
            "{:%H%M}".format(self.entrytime),
            "" if self.record_identifier is not "L" else "L",
            self.status, self.lat_str, self.lon_str,
            self.wind, self.mslp,
            self.extent_TS[0] if self.extent_TS[0] is not None else "-999",
            self.extent_TS[1] if self.extent_TS[1] is not None else "-999",
            self.extent_TS[2] if self.extent_TS[2] is not None else "-999",
            self.extent_TS[3] if self.extent_TS[3] is not None else "-999",
            self.extent_TS50[0] if self.extent_TS50[0] is not None else "-999",
            self.extent_TS50[1] if self.extent_TS50[1] is not None else "-999",
            self.extent_TS50[2] if self.extent_TS50[2] is not None else "-999",
            self.extent_TS50[3] if self.extent_TS50[3] is not None else "-999",
            self.extent_HU[0] if self.extent_HU[0] is not None else "-999",
            self.extent_HU[1] if self.extent_HU[1] is not None else "-999",
            self.extent_HU[2] if self.extent_HU[2] is not None else "-999",
            self.extent_HU[3] if self.extent_HU[3] is not None else "-999",
            # self.tsNE, self.tsSE, self.tsSW, self.tsNW,
            # self.ts50NE, self.ts50SE, self.ts50SW, self.ts50NW,
            # self.huNE, self.huSE, self.huSW, self.huNW
        ))

    @property
    def avg_wind_extent_TS(self):
        """Returns the average extent of at-least tropical storm winds."""
        return statistics.mean(extent_TS)

    @property
    def avg_wind_extent_TS50(self):
        """Returns the average extent of at-least gale winds."""
        return statistics.mean(extent_TS50)

    @property
    def avg_wind_extent_HU(self):
        """Returns the average extent of hurricane-strength winds."""
        return statistics.mean(extent_HU)

def haversine(startpos,endpos):
    """Returns the distance between two tupled GPS coordinates.

    Args:
        startpos: the starting gps-coordinate point; in tuple form of 
            (latitude, longitude). Both need to be an int or float.
        endpos: the starting gps-coordinate point; in tuple form of (latitude,
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

def saffir_simpson(spd):
    """Static method that returns the equivalent saffir-simpson scale rating,
    based on wind-speed in knots.

    This is the most-common index used to generalize tropical cyclone
    intensity.

    Example: saffir_simpson(100) --> 3 (implying category 3).
    """
    if 34 <= spd <= 63:     return 0
    elif 64 <= spd <= 82:   return 1
    elif 83 <= spd <= 95:   return 2
    elif 96 <= spd <= 113:  return 3
    elif 114 <= spd <= 135: return 4
    elif int(spd) >= 136:   return 5
    else: return -1

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