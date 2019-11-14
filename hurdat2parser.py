# hurdat2parser.py -- By Kyle Gentry
# This site showed me the basis of nesting objects (classes): https://www.novixys.com/blog/nested-inner-classes-python/

import datetime
import math

storm = []

class NewStorm:
    # The following entries will be amended during successive time Entry process
    maxwind = -1           # Peak Max-Sustained Winds; -1 is a placeholder; will be adjusted during time-series Entry
    ACE = 0                # Accumulated Cyclone Energy; If peak winds(v) >= TS-strength, sum of 6-hr-interval v^2 are taken
    HDP = 0                 # Hurricane Destruction Potential; If peak winds(v) >= HU strength, sum of 6-hr-interval v^2 are taken
    MHDP = 0                # Major Hurricane Destruction Potential; Winds counted if >= MHU strength
    minmslp = 9999         # Minimum MSLP during life of storm; 9999 is just a placeholder
    landfalls = 0          # Will store the quantity of recorded landfall entries
    LTSstrength = False     # Indicates if a landfall at TS strength was made
    LHUstrength = False     # Indicates if storm ever records a landfall at HU strength
    TSreach = False         # declares if non-EX TS status is ever reached
    strengthTSreach = False # regardless of status, did storm reach TS strength at some point during its life
    HUreach = False         # determines if non-EX HU status is ever reached
    strengthHUreach = False # regardless of status, did storm reach HU strength at some point during its life
    MHUreach = False        # determines if storm ever reached Major Hurricane status
    
    #duration = ""         # Stores track entry duration

    def __init__(self,atcfid,name):
        self.atcfid = atcfid    # Record ATCFID
        self.year = atcfid[4:8]     # Year (extracts from ATCFID)
        self.name = name            # Name issued (Depressions will generally only have a number)
        self.maxwindstatus = ""     # Records the storm-status (TS,HU,etc) at the time of peak wind
        self.Entry = []             # Empty list which will hold nested objects of each time-entry per storm

    def addTime(self,rawdata):
        self.Entry.append(NewTime(rawdata))

    def addLandfall(self):
        self.landfalls += 1

    def addACE(self,v2):
        self.ACE += v2

    def addHDP(self,v2):
        self.HDP += v2

    def addMHDP(self,v2):
        self.MHDP += v2

class NewTime:

    def __init__(self,raw):
        self.entryday = raw[0].strip(" ")          # Date --> '20050608'
        self.entryhour = raw[1].strip(" ")          # Time --> '1800'
        self.entrytime = datetime.datetime(int(self.entryday[0:4]), \
                                           int(self.entryday[4:6]), \
                                           int(self.entryday[6:8]), \
                                           hour=int(self.entryhour[0:2]))
        self.recidentifier = raw[2].strip(" ")      # Record Identifier (L, W, P, etc)
        if self.recidentifier == "L": storm[len(storm)-1].addLandfall()     # Adds a Landfall record
        self.status = raw[3].strip(" ")             # Storm Designation (Hurricane, TS, etc)
        if self.status == "TS": storm[len(storm)-1].TSreach = True
        if self.status == "HU": storm[len(storm)-1].HUreach = True
        
        self.lat = raw[4].strip(" ")                # Latitude
        if self.lat[len(self.lat)-1] == "N":
            self.latdec = float(self.lat[:len(self.lat)-1])    # Latitude in decimal (float) form
        else: self.latdec = float("-" + self.lat[:len(self.lat)-1])
        self.lon = raw[5].strip(" ")                # Longitude
        if self.lon[len(self.lon)-1] == "W":
            self.londec = float("-" + self.lon[:len(self.lon)-1])  # Longitude in decimal (float) form
        else: self.londec = float(self.lon[:len(self.lon)-1])
        self.wind = raw[6].strip(" ")               # Wind Speed
        # These lines handle a marker which determines landfall at at-least TS or Hurricane Strength
        if self.recidentifier == "L" and int(self.wind) >= 34: storm[len(storm)-1].LTSstrength = True
        if self.recidentifier == "L" and int(self.wind) >= 64: storm[len(storm)-1].LHUstrength = True
        # ------------------------------------------------------------------------------
        if int(self.wind) >= 34 and self.entryhour in ["0000","0600","1200","1800"]:
            storm[len(storm)-1].addACE(int(self.wind)**2)  # Aggregate ACE if wind-speeds are TS-strength or greater
        if int(self.wind) >= 64 and self.entryhour in ["0000","0600","1200","1800"]:
            storm[len(storm)-1].addHDP(int(self.wind)**2)  # Aggregate HDP if wind-speeds are HU-strength or greater
        if int(self.wind) >= 96 and self.entryhour in ["0000","0600","1200","1800"]:
            storm[len(storm)-1].addMHDP(int(self.wind)**2)  # Aggregate MHDP if wind-speeds are MHU-strength or greater
        if int(self.wind) > storm[len(storm)-1].maxwind:
            storm[len(storm)-1].maxwind = int(self.wind)   # Max Wind Speed
            storm[len(storm)-1].maxwindstatus = self.status     # Status at Max Wind Speed
        if int(self.wind) >= 34: storm[len(storm)-1].strengthTSreach = True
        if int(self.wind) >= 64: storm[len(storm)-1].strengthHUreach = True
        if int(self.wind) >= 96: storm[len(storm)-1].MHUreach = True
        self.ss_scale = ssdet(self.wind)            # Saffir-Simpson Scale Equiv rating
        self.mslp = raw[7].strip(" ")               # Pressure
        try:                                        # MINIMUM MSLP
            if int(self.mslp) < storm[len(storm)-1].minmslp and int(self.mslp) != -999:
                storm[len(storm)-1].minmslp = int(self.mslp)    # MIN MSLP
        except:
            storm[len(storm)-1].minmslp = storm[len(storm)-1].minmslp   # *** This is here since 'continue' is not allowed
            
        self.tsNE = raw[8].strip(" ")           # NE extent of TS-force winds
        self.tsSE = raw[9].strip(" ")           # SE extent of TS-force winds
        self.tsSW = raw[10].strip(" ")          # SW extent of TS-force winds
        self.tsNW = raw[11].strip(" ")          # NW extent of TS-force winds
        self.ts50NE = raw[12].strip(" ")            # NE extent of strong (50kt / 58mph) TS-force winds
        self.ts50SE = raw[13].strip(" ")            # SE extent of strong TS-force winds
        self.ts50SW = raw[14].strip(" ")            # SW extent of strong TS-force winds
        self.ts50NW = raw[15].strip(" ")            # NW extent of strong TS-force winds
        self.huNE = raw[16].strip(" ")                  # NE extent of TS-force winds
        self.huSE = raw[17].strip(" ")                  # SE extent of TS-force winds
        self.huSW = raw[18].strip(" ")                  # SW extent of TS-force winds
        self.huNW = raw[19].strip(" ")                  # NW extent of TS-force winds

def ssdet(spd):
    if int(spd) >= 34 and int(spd) <= 63:   return "0"
    elif int(spd) >= 64 and int(spd) <= 82:   return "1"
    elif int(spd) >= 83 and int(spd) <= 95:   return "2"
    elif int(spd) >= 96 and int(spd) <= 112:   return "3"
    elif int(spd) >= 113 and int(spd) <= 136:   return "4"
    elif int(spd) >= 137 and int(spd) <= 500:   return "5"
    else: return "-1"

def formatStatus(status,wind):
    if status == "DB" or status == "LO" or status == "WV": return "Disturbance, Low, or Tropical Wave"
    elif status == "SD": return "Subtropical Depression"
    elif status == "TD": return "Tropical Depression"
    elif status == "SS": return "Subtropical Storm"
    elif status == "TS": return "Tropical Storm"
    elif status == "EX": return "Extratropical Cyclone"
    elif status == "HU" and wind < 96: return "Hurricane"
    elif status == "HU" and wind >= 96: return "Major Hurricane"
    else: return "Unknown"

def stormStats(id_atcf):
    if type(id_atcf) != str: return print("OOPS! input must be a string (even if just wanting yearly storm stats)")
    id_atcf = id_atcf.upper()
    if len(id_atcf) > 2:
        if id_atcf[2].isalpha() == False:   # If searched string has a number in 2nd index (3rd Char)
            if id_atcf[0].isalpha() == True: search_att = "atcfid"  # If first index is alpha, it's interpreted as an ATCF ID
            elif len(id_atcf) == 4: search_att = "year"   # If the first character is numeric, the string is interpreted as a year
            elif len(id_atcf) < 4: return print("*** Partial year searches not supported. Try again ***")
        else: search_att = "name"   # If search has a letter in 2nd index, it must be a name search
    elif len(id_atcf) > 0:  # If the search string meets: 0 < chars < 3
        if id_atcf[0].isalpha() == False:   # If a number / partial year has been entered
            return print("*** 2-Digit or less numerics or partial years are not accepted. Try again ***")
        else: search_att = "name"     # This enables partial name searches
    elif len(id_atcf) == 0: return print("*** Looks like you forgot to input a string. Try again! ***")
        
    foundstorm = False
    for x in storm:
        if getattr(x,search_att)[0:len(id_atcf)] == id_atcf:
            print("-----------------------")
            print("* ATCF Id: " + x.atcfid)
            print("* Name: " + x.name)
            print("* Entries: " + str(len(x.Entry)))
            print("* Peak Wind: " + str(round(x.maxwind*0.514444,2)) + " m/s; " + str(x.maxwind) + " kts; " + str(int(x.maxwind*1.15078)) + " mph")
            print("* Status at Peak Wind: " + formatStatus(x.maxwindstatus,x.maxwind))
            if x.minmslp == 9999 or x.minmslp == -999: print("* Minimum MSLP: N/A")
            else: print("* Minimum MSLP: " + str(x.minmslp) + " mb")
            print("* Major HDP: " + str(round(x.MHDP * 10**(-4),2)) + " * 10^4 * kt^2")
            print("* HDP: " + str(round(x.HDP * 10**(-4),2)) + " * 10^4 * kt^2")
            print("* ACE: " + str(round(x.ACE * 10**(-4),2)) + " * 10^4 * kt^2")
            print("* Start Date: " + x.Entry[0].entryday[0:4] + "-" + x.Entry[0].entryday[4:6] + "-" + x.Entry[0].entryday[6:8] + " " + x.Entry[0].entryhour[0:2] + "Z")
            print("* End Date: " + x.Entry[len(x.Entry)-1].entryday[0:4] + "-" + x.Entry[len(x.Entry)-1].entryday[4:6] + "-" + x.Entry[len(x.Entry)-1].entryday[6:8] + " " + x.Entry[len(x.Entry)-1].entryhour[0:2] + "Z")
            storm_totaltime = x.Entry[len(x.Entry)-1].entrytime - x.Entry[0].entrytime
            print("* Storm Track Period: " + str(math.floor(float(storm_totaltime.total_seconds()) / 60 / 60 / 24)) + " days, " + str(int(float(storm_totaltime.total_seconds()) / 60 / 60 % 24)) + " hrs")
            if x.landfalls == 0: print("* Landfall: No Record")
            else: print("* Landfall: Yes, " + str(x.landfalls) + " Record(s)")
            foundstorm = True
            if search_att == "atcfid": break
    if foundstorm == False:
        print("'" + id_atcf + "' NOT FOUND")

def seasonStats(yr,*args):
    # Manual Error handling
    if type(yr) != int: return print("OOPS! '{}' is not a valid year or is not in the right format (ensure it is an integer)".format(yr))
    else:
        if yr < 1851 or yr > int(storm[len(storm)-1].year): return print("OOPS! '{}' is not between 1851 and {}".format(yr,int(storm[len(storm)-1].year)))
    if len(args) > 1:
        return print("OOPS! Too many values entered into function")
    elif len(args) == 1:
        if type(args[0]) != int: return print("OOPS! '{}' is not in the right format".format(args[0]))
        if yr == args[0] or args[0] < yr: return print("OOPS! Ensure Year1 < Year2")
        if args[0] > int(storm[len(storm)-1].year): return print("OOPS! '{}' is not between 1851 and {}".format(args[0],int(storm[len(storm)-1].year)))
    # Function work
    if len(args) == 1:
        yr2 = args[0]
    else: yr2 = yr
    #season1index = season.index(str(yr))
    #season2index = season.index(str(yr2))
    totalStorms = 0
    totalTS = 0
    totalTSstrength = 0
    totalHU = 0
    totalHUstrength = 0
    totalMHU = 0
    totalHDP = 0
    totalMHDP = 0
    totalACE = 0
    totalLandfalls = 0
    totalLTS = 0
    totalLHU = 0
    for x in season:
        if int(x.year) >= yr and int(x.year) <= yr2:
            totalStorms += x.tracks
            totalTS += x.tracksTS
            totalTSstrength += x.tracksTSstrength
            totalHU += x.tracksHU
            totalHUstrength += x.tracksHUstrength
            totalMHU += x.tracksMHU
            totalMHDP += x.MHDP
            totalHDP += x.HDP
            totalACE += x.ACE
            totalLandfalls += x.landfalls
            totalLTS += x.landfallsTS
            totalLHU += x.landfallsHU
    # Print Report
    if len(args) > 0:
        print("--------------------------------------------------------")
        print("Tropical Cyclone Stats, Between Years {}-{}".format(yr,yr2))
        print("--------------------------------------------------------")
    else:
        print("----------------------------------------")
        print("Tropical Cyclone Stats for {}".format(yr))
        print("----------------------------------------")
    print("Total Tracks: {}".format(totalStorms))
    print("Tropical Storms: {}".format(totalTS-totalHU))
    print("Tropical Storm-Strength Storms: {}".format(totalTSstrength-totalHUstrength))
    print("Hurricanes: {}".format(totalHU))
    print("Hurricane-Strength Storms: {}".format(totalHUstrength))
    print("Major Hurricanes: {}".format(totalMHU))
    print("Major HDP: {} * 10^4 * kt^2".format(round(totalMHDP*10**(-4),1)))
    print("HDP: {} * 10^4 * kt^2".format(round(totalHDP*10**(-4),1)))
    print("ACE: {} * 10^4 * kt^2".format(round(totalACE*10**(-4),1)))
    print("Total Landfalling Systems: {}".format(totalLandfalls))
    print("Tropical Storm-strength Landfalling Systems: {}".format(totalLTS-totalLHU))
    print("Hurricane-strength Landfalling Systems: {}".format(totalLHU))
    print("--")

def rankStorms(tcqty,st_attribute,*args,**kwargs):
    """rankStorms(10,"ACE",1967,2018,**reverse=False)
             (quantity,attribute,year1(optional),year2(optional))
             Valid Attributes: "maxwind","minmslp","landfalls","MHDP","HDP","ACE"
             ** UNSTABLE ** OPTIONAL kwarg: reverse=bool ... set to True to invert the ranking results
    """
    if len(args) > 3: return print("* OOPS! 3 seperate year values entered instead of 2. Try again *")
    # Enables user to dictate what years ranked values will be drawn from
    if len(args) == 2:
        year1 = args[0]
        year2 = args[1]
        if year1 > year2 or year1 < 1851 or year2 > int(storm[len(storm)-1].year):
            return print("* OOPS! Double-check your dates. Try again. *")
    # If only one year is submitted, it is treated as the start year (year1) for the analysis
    elif len(args) == 1:
        year1 = args[0]
        year2 = args[0]
        if year1 < 1851 or year1 > year2:
            return print("* OOPS! Begin year invalid *")
    else:
        year1 = 1851
        year2 = int(storm[len(storm)-1].year)
    #return str(year1) + ", " + str(year2)
    if type(tcqty) != int or tcqty >= 0 and tcqty < 5 or tcqty < 0 or tcqty > 9999:
        return print("* OOPS! '{}' is an invalid entry. Only integers (int), between 5 and 9999, are allowed in 1st argument slot. Try again. *".format(tcqty))
    if hasattr(NewStorm,st_attribute) == False:
        return print("* OOPS! No storm attribute suitable for ranking named '{}'".format(st_attribute))

    validstorms = []    # List that will hold the storms valid in our search
                        # tcqty tells us how many to keep in the list
    for x in storm:
        if int(x.atcfid[4:8]) >= year1 and int(x.atcfid[4:8]) <= year2:
            if st_attribute == "minmslp":
                if x.minmslp != 9999: validstorms.append(x)
    if st_attribute == "minmslp":   # If we're dealing with minmslp, don't include reverse (we want lowest to highest)
        if "reverse" in kwargs: rank = sorted(validstorms, key=lambda st: getattr(st,st_attribute),reverse=kwargs["reverse"])
        else: rank = sorted(validstorms, key=lambda st: getattr(st,st_attribute))
    elif st_attribute in ["maxwind","minmslp","landfalls","MHDP","HDP","ACE"]:
        if "reverse" in kwargs:
            if kwargs["reverse"] == True: rank = sorted(validstorms, key=lambda st: getattr(st,st_attribute))
            else: rank = sorted(validstorms, key=lambda st: getattr(st,st_attribute),reverse=kwargs["reverse"])
        else: rank = sorted(validstorms, key=lambda st: getattr(st,st_attribute), reverse=True)
    else: return print("OOPS! '{}' is not a supported attribute for ranking".format(st_attribute))
    # This block will help us list storms that have equal values (so list will return storms with same values
    #   giving us a list of storms with the top # of unique values of attribute)
    uniquevalues = []
    # 'rankadded' will be a parallel-array marker to 'uniquevalues' to know when to add a rank to the output
    rankadded = []
    for x in rank:
        if getattr(x,st_attribute) not in uniquevalues: uniquevalues.append(getattr(x,st_attribute))
    uniquevalues = uniquevalues[0:tcqty]    # only keeps the top x values
    for x in range(len(uniquevalues)):
        rankadded.append(False)    # Just in case #storms < TC qty; and if args == 1 year, all storms from that year will be printed
    if len(rank) < tcqty or len(args) == 1: tcqty = len(rank)

    # PRINT OUT REPORT
    print("{:-^35}".format(""))
    if len(args) == 1: print("{:^35}".format("Storms Ranked by {}, {}".format(st_attribute,year1)))
    else: print("{:^35}".format("Storms Ranked by {}, {}-{}".format(st_attribute,year1,year2)))
    print("{:4}  {:4}  {:^12}  {:^10}".format("Rank","Year","Name","Value"))
    print("{:-^4}  {:-^4}  {:-^12}  {:-^10}".format("","","",""))
    rank_ind = 0     # Will be used for in format of ranking (to place rank numbers)
    for x in range(len(rank)):
        if getattr(rank[x],st_attribute) in uniquevalues:
            if rankadded[uniquevalues.index(getattr(rank[x],st_attribute))] == False:
                print("{:>4}  {:4}  {:12}  {:^10}".format(rank_ind + 1,rank[x].year,rank[x].name,getattr(rank[x],st_attribute)))
                rankadded[uniquevalues.index(getattr(rank[x],st_attribute))] = True
                rank_ind += 1
            else:
                print("{:>4}  {:4}  {:<12}  {:^10}".format(" ",rank[x].year,rank[x].name,getattr(rank[x],st_attribute)))


def rankSeasons(seasonqty,sn_attribute,*args):
    """rankSeasons(10,"tracksHU",1950,2000)
             (quantity,attribute,year1(optional),year2(optional))
             Valid Attributes (sn_attribute): "tracks","tracksTS","tracksTSstrength","tracksHU",
                                            "tracksHUstrength","tracksMHU","MHDP","HDP","ACE",
                                            "landfalls","landfallsTS","landfallsHU"
    """
    validseasons = []
    if len(args) > 3: return print("* OOPS! 3 seperate year values entered instead of 2. Try again *")
    # Enables user to dictate what years ranked values will be drawn from
    if len(args) == 2:
        try:
            year1 = int(args[0])
            year2 = int(args[1])
            if year1 > year2 or year1 < 1851 or year2 > int(storm[len(storm)-1].year) or year2-year1 < 4:
                return print("* OOPS! Double-check your years. Try again. Valid years range from {}-{}, and must be 9+ years apart *".format(1851,int(storm[len(storm)-1].year)))
        except:
            return print("* OOPS! Your years must numeric!")
    # If only one year is submitted, it is treated as the start year (year1) for the analysis
    elif len(args) == 1:
        try:
            year1 = int(args[0])
            year2 = int(storm[len(storm)-1].year)
            if year1 < 1851 or year1 > year2 or year2-year1 < 4:
                return print("* OOPS! Year invalid. It must be <= {} *".format(int(storm[len(storm)-1].year) - 9))
        except:
            return print("* OOPS! Year must be numeric!")
    else:
        year1 = 1851
        year2 = int(storm[len(storm)-1].year)
    #return str(year1) + ", " + str(year2)
    if type(seasonqty) != int:
        try:
            seasonqty = int(seasonqty)
        except:
            return print("* OOPS! The season rank quantity must be numeric! *")
    if seasonqty > year2-year1+1:
        oldseasonqty = seasonqty
        seasonqty = year2-year1+1
        print("* Rank quantities changed from {} to {}".format(oldseasonqty,seasonqty))
    if seasonqty > 50:
        seasonqty = 50
        print("* Rank quantities reduced to 50")

    for x in season:
        if int(x.year) in range(year1,year2+1):
            validseasons.append(x)

    validattr = ["tracks","tracksTS","tracksTSstrength","tracksHU","tracksHUstrength","tracksMHU","MHDP","HDP","ACE","landfalls","landfallsTS","landfallsHU"]
    titles = {"tracks": "Storm Tracks",
              "tracksTS": "Tropical Storms",
              "tracksTSstrength": "Tropical Storm-Strength Tracks",
              "tracksHU": "Hurricanes",
              "tracksHUstrength":"Hurricane-Strength Storms",
              "tracksMHU":"Major Hurricanes",
              "MHDP":"Major-Hurricane Destruction Potential",
              "HDP":"Hurricane Destruction Potential",
              "ACE":"Accumulated Cyclone Energy",
              "landfalls":"Landfalling Systems",
              "landfallsTS":"Landfalling Tropical Storm-Strength Systems",
              "landfallsHU":"Landfalling Hurricane-Strength Systems"}
    
    if sn_attribute not in validattr: return print("* OOPS! Attributes are case-sensitive. Valid attributes: {} *".format(validattr))

    rank_desc = sorted(validseasons,key=lambda sn: getattr(sn,sn_attribute),reverse=True)
    rank_asc = sorted(validseasons,key=lambda sn: getattr(sn,sn_attribute))

    # Print Report
    print("{:-^39}".format(""))
    print("{:^39}".format(titles[sn_attribute]))
    print("{:^39}".format("Top {} Seasons, {}-{}".format(seasonqty,year1,year2)))
    print("{:-^39}".format(""))
    print("{:^19}|{:^19}".format("MOST","LEAST"))
    print("{:-^19}|{:-^19}".format("",""))
    i = 1
    j = 1
    ranked_i = []
    ranked_j = []
    for x in range(len(rank_desc)):
        if x == 0:
            print(" {:2}{} {:4}  {:<7} | {:2}{} {:4}  {:<7} ".format(1,".",
                                                                     rank_desc[x].year,getattr(rank_desc[x],sn_attribute),
                                                                     1,".",
                                                                     rank_asc[x].year,getattr(rank_asc[x],sn_attribute)))
            ranked_i.append(i)
            ranked_j.append(j)
        else:
            if i not in ranked_i and i <= seasonqty: ranked_i.append(i)
            if j not in ranked_j and j <= seasonqty: ranked_j.append(j)
            if getattr(rank_desc[x],sn_attribute) != getattr(rank_desc[x-1],sn_attribute): i += 1
            if getattr(rank_asc[x],sn_attribute) != getattr(rank_asc[x-1],sn_attribute): j += 1
            if i <= seasonqty or j <= seasonqty:
                print(" {:2}{} {:4}  {:<7} | {:2}{} {:4}  {:<7} ".format(i if i not in ranked_i and i <= seasonqty else "",
                                                                         "." if i not in ranked_i and i <= seasonqty else " ",
                                                                         rank_desc[x].year if i <= seasonqty else "",
                                                                         getattr(rank_desc[x],sn_attribute) if i <= seasonqty else "",
                                                                         j if j not in ranked_j and j <= seasonqty else "",
                                                                         "." if j not in ranked_j and j <= seasonqty else " ",
                                                                         rank_asc[x].year if j <= seasonqty else "",
                                                                         getattr(rank_asc[x],sn_attribute) if j <= seasonqty else ""))
        if i > seasonqty and j > seasonqty: break

def stormCSV():
    stormatts = ["ATCFID",
                 "Year",
                 "Name",
                 "Track Duration (hrs)",
                 "Peak MSLP (lowest)",
                 "Peak Max-Sustained Winds",
                 "Major-Hurricane Destruction Potental (MHDP) (kts^2 * 10^(-4))",
                 "Hurricane Destruction Potential (HDP) (kts^2 * 10^(-4))",
                 "Accumulated Cyclone Energy (ACE) (kts^2 * 10^(-4))",
                 "Landfalls (total)",
                 "Landfall at TS strength?",
                 "Landfall at HU strength?"]
    
    with open("hurdat2STORMoutput.csv","w") as w:
        for x in range(len(stormatts)):
            w.write(stormatts[x]+ "," if stormatts.index(stormatts[x]) != len(stormatts)-1 else stormatts[x] + "\n")
        for x in storm:
            w.write(x.atcfid + ",")
            w.write(x.year + ",")
            w.write(x.name + ",")
            st = x.Entry[0].entrytime
            en = x.Entry[len(x.Entry)-1].entrytime
            duration_in_hrs = (en - st).days * 24 + (en - st).seconds / 60 / 60
            w.write("{},".format(duration_in_hrs))
            w.write("{},".format(x.minmslp) if x.minmslp != 9999 else "N/A,")
            w.write("{},".format(x.maxwind) if x.maxwind != -1 else "N/A,")
            w.write("{},".format(round(x.MHDP*10**(-4),2)))
            w.write("{},".format(round(x.HDP*10**(-4),2)))
            w.write("{},".format(round(x.ACE*10**(-4),2)))
            w.write("{},".format(x.landfalls))
            w.write("{},".format(x.LTSstrength))
            w.write("{}\n".format(x.LHUstrength))

def seasonCSV():
    stormatts = ["Season",
                 "Tracked Systems",
                 "Tropical Storms",
                 "Tropical Storm Strength Systems",
                 "Hurricanes",
                 "Hurricane-Strength Systems",
                 "Major Hurricanes",
                 "Major Hurricane Destruction Potential (MHDP) (kts^2 * 10^(-4))",
                 "Hurricane Destruction Potential (HDP) (kts^2 * 10^(-4))",
                 "Accumulated Cyclone Energy (ACE) (kts^2 * 10^(-4))",
                 "Landfalling Systems",
                 "Landfalling Systems at Tropical Storm Strength",
                 "Landfalling Systems at Hurricane Srength"]
    
    with open("hurdat2SEASONoutput.csv","w") as w:
        for x in range(len(stormatts)):
            w.write(stormatts[x]+ "," if stormatts.index(stormatts[x]) != len(stormatts)-1 else stormatts[x] + "\n")
        for x in season:
            w.write("{},".format(x.year))
            w.write("{},".format(x.tracks))
            w.write("{},".format(x.tracksTSstrength-x.tracksHUstrength))
            w.write("{},".format(x.tracksHUstrength))
            w.write("{},".format(x.tracksMHU))
            w.write("{},".format(round(x.MHDP*10**(-4),2)))
            w.write("{},".format(round(x.HDP*10**(-4),2)))
            w.write("{},".format(round(x.ACE*10**(-4),2)))
            w.write("{},".format(x.landfalls))
            w.write("{},".format(x.landfallsTS))
            w.write("{}\n".format(x.landfallsHU))

def climoCSV():
    ystart = int(storm[0].year)
    yend = int(storm[len(storm)-1].year)

    climo10yrs = {}
    for x in range(ystart,yend+1-9):
        climo10yrs[(x,x+9)] = {"ystart":x,"yend":x+9,"tracks":0,"tracksTS":0,"tracksTSstrength":0,"tracksHU":0,"tracksHUstrength":0,"tracksMHU":0,
                                "MHDP":0,"HDP":0,"ACE":0,"landfalls":0,"landfallsTS":0,"landfallsHU":0}

    climo30yrs = {}
    for x in range(ystart,yend+1-29):
        climo30yrs[(x,x+29)] = {"ystart":x,"yend":x+29,"tracks":0,"tracksTS":0,"tracksTSstrength":0,"tracksHU":0,"tracksHUstrength":0,"tracksMHU":0,
                                "MHDP":0,"HDP":0,"ACE":0,"landfalls":0,"landfallsTS":0,"landfallsHU":0}

    for x in climo10yrs:
        for y in season:
            if int(y.year) >= climo10yrs[x]["ystart"] and int(y.year) <= climo10yrs[x]["yend"]:
                #input("{} in {}-{}".format(y.year,climo10yrs[x]["ystart"],climo10yrs[x]["yend"]))
                climo10yrs[x]["tracks"] += y.tracks
                climo10yrs[x]["tracksTS"] += y.tracksTS
                climo10yrs[x]["tracksTSstrength"] += y.tracksTSstrength
                climo10yrs[x]["tracksHU"] += y.tracksHU
                climo10yrs[x]["tracksHUstrength"] += y.tracksHUstrength
                climo10yrs[x]["tracksMHU"] += y.tracksMHU
                climo10yrs[x]["MHDP"] += y.MHDP
                climo10yrs[x]["HDP"] += y.HDP
                climo10yrs[x]["ACE"] += y.ACE
                climo10yrs[x]["landfalls"] += y.landfalls
                climo10yrs[x]["landfallsTS"] += y.landfallsTS
                climo10yrs[x]["landfallsHU"] += y.landfallsHU
    #for x in climo10yrs:
        #print("{}-{} - {}".format(climo10yrs[x]["ystart"],climo10yrs[x]["yend"],climo10yrs[x]["tracks"]))

    for x in climo30yrs:
        for y in season:
            if int(y.year) >= climo30yrs[x]["ystart"] and int(y.year) <= climo30yrs[x]["yend"]:
                climo30yrs[x]["tracks"] += y.tracks
                climo30yrs[x]["tracksTSstrength"] += y.tracksTSstrength
                climo30yrs[x]["tracksHUstrength"] += y.tracksHUstrength
                climo30yrs[x]["tracksMHU"] += y.tracksMHU
                climo30yrs[x]["MHDP"] += y.MHDP
                climo30yrs[x]["HDP"] += y.HDP
                climo30yrs[x]["ACE"] += y.ACE
                climo30yrs[x]["landfalls"] += y.landfalls
                climo30yrs[x]["landfallsTS"] += y.landfallsTS
                climo30yrs[x]["landfallsHU"] += y.landfallsHU
                
    stormatts = ["Season",
                 "Tracked Systems",
                 "Tropical Storm Strength Systems",
                 "Hurricane-Strength Systems",
                 "Major Hurricanes",
                 "Major Hurricane Destruction Potential (MHDP) (kts^2 * 10^(-4))",
                 "Hurricane Destruction Potential (HDP) (kts^2 * 10^(-4))",
                 "Accumulated Cyclone Energy (ACE) (kts^2 * 10^(-4))",
                 "Landfalling Systems",
                 "Landfalling Systems at Tropical Storm Strength",
                 "Landfalling Systems at Hurricane Srength"]

    with open("hurdat2CLIMO_10yrs.csv","w") as w:
        for x in range(len(stormatts)):
            w.write(stormatts[x]+ "," if stormatts.index(stormatts[x]) != len(stormatts)-1 else stormatts[x] + "\n")
        for x in climo10yrs:
            w.write("{}-{},".format(climo10yrs[x]["ystart"],climo10yrs[x]["yend"]))
            w.write("{},".format(climo10yrs[x]["tracks"]))
            w.write("{},".format(climo10yrs[x]["tracksTSstrength"]-climo10yrs[x]["tracksHUstrength"]))
            w.write("{},".format(climo10yrs[x]["tracksHUstrength"]))
            w.write("{},".format(climo10yrs[x]["tracksMHU"]))
            w.write("{},".format(round(climo10yrs[x]["MHDP"]*10**(-4),2)))
            w.write("{},".format(round(climo10yrs[x]["HDP"]*10**(-4),2)))
            w.write("{},".format(round(climo10yrs[x]["ACE"]*10**(-4),2)))
            w.write("{},".format(climo10yrs[x]["landfalls"]))
            w.write("{},".format(climo10yrs[x]["landfallsTS"]))
            w.write("{}\n".format(climo10yrs[x]["landfallsHU"]))

    with open("hurdat2CLIMO_30yrs.csv","w") as w:
        for x in range(len(stormatts)):
            w.write(stormatts[x]+ "," if stormatts.index(stormatts[x]) != len(stormatts)-1 else stormatts[x] + "\n")
        for x in climo30yrs:
            w.write("{}-{},".format(climo30yrs[x]["ystart"],climo30yrs[x]["yend"]))
            w.write("{},".format(climo30yrs[x]["tracks"]))
            w.write("{},".format(climo30yrs[x]["tracksTSstrength"]-climo30yrs[x]["tracksHUstrength"]))
            w.write("{},".format(climo30yrs[x]["tracksHUstrength"]))
            w.write("{},".format(climo30yrs[x]["tracksMHU"]))
            w.write("{},".format(round(climo30yrs[x]["MHDP"]*10**(-4),2)))
            w.write("{},".format(round(climo30yrs[x]["HDP"]*10**(-4),2)))
            w.write("{},".format(round(climo30yrs[x]["ACE"]*10**(-4),2)))
            w.write("{},".format(climo30yrs[x]["landfalls"]))
            w.write("{},".format(climo30yrs[x]["landfallsTS"]))
            w.write("{}\n".format(climo30yrs[x]["landfallsHU"]))
                

"""class Season:
    tracks = 0
    tracksTS = 0
    tracksTSstrength = 0
    tracksHU = 0
    tracksHUstrength = 0
    tracksMHU = 0
    MHDP = 0
    HDP = 0
    ACE = 0
    #avgMINmslp
    landfalls = 0
    landfallsTS = 0
    landfallsHU = 0

    def __init__(self,year):
        self.year = year    # year in str form
"""

# MAIN PROGRAM -------------------------------------------------------------------
print("* Now formulating Storm objects *")

with open("hurdat_all_05012019.txt","r") as f:
    for each in f.readlines():
        templine = each.split(",")
        if templine[0][0:2] == "AL":     # NEW STORM
            # Creates new storm object, and applying the ATCFID and Name
            storm.append(NewStorm(templine[0].strip(" "),templine[1].strip(" ")))
            curr_index = len(storm) - 1
        else:   # Need to add a time-based data-entry record for the storm
            storm[curr_index].addTime(templine)

season = []     # Holder of season objects

class Season:
    tracks = 0
    tracksTS = 0
    tracksTSstrength = 0
    tracksHU = 0
    tracksHUstrength = 0
    tracksMHU = 0
    MHDP = 0
    HDP = 0
    ACE = 0
    #avgMINmslp
    landfalls = 0
    landfallsTS = 0
    landfallsHU = 0

    def __init__(self,year):
        self.year = year    # year in str form

print("* Now formulating Seasons Objects *")

for yr in range(1851,int(storm[len(storm)-1].year) + 1):
    season.append(Season(str(yr)))     # Append season to season obj
    for x in storm:
        if int(x.year) == yr:
            season[len(season)-1].tracks += 1
            if x.TSreach == True: season[len(season)-1].tracksTS += 1
            if x.maxwind >= 34: season[len(season)-1].tracksTSstrength += 1
            if x.HUreach == True: season[len(season)-1].tracksHU += 1
            if x.maxwind >= 64: season[len(season)-1].tracksHUstrength += 1
            if x.MHUreach == True: season[len(season)-1].tracksMHU += 1
            if x.landfalls > 0: season[len(season)-1].landfalls += 1
            if x.LTSstrength == True: season[len(season)-1].landfallsTS += 1
            if x.LHUstrength == True: season[len(season)-1].landfallsHU += 1
            season[len(season)-1].MHDP += x.MHDP
            season[len(season)-1].HDP += x.HDP
            season[len(season)-1].ACE += x.ACE

def guide():
    print("-----------------------------------------------------------------------------------------")
    print("* Basic Storm Report available via stormStats(str) function.")
    print("    >>> stormStats('AL##YYYY') -- Search for specific ATCFID")
    print("    >>> stormStats('Name') -- Search via Storm Name; returns all matches")
    print("        - PARTIAL name searches are supported, even if just one character ")
    print("        - At least two characters are recommended due to likely high-volume of results using one")
    print("    >>> stormStats('YYYY') -- Search and return records for an entire season\n")
    print("* Basic Seasonal Stats available via seasonStats(year1,*year2) function.")
    print("    >>> seasonStats(2005,2010) -- Example of input")
    print("    - 2nd year is optional. If included, it will aggregate stats from the range of seasons\n")
    print("* Basic Storm Rankings available via rankStorms(intqty,'attribute',*year1,*year2) function.")
    print("    >>> rankStorms(5,'maxwind',1967,2018,**reverse=False) -- Example of input")
    print("                   ^     ^      ^    ^          ^")
    print("                Report  Attr-   Yr1  Yr2     reverse")
    print("                 QTY   ibute  (opt) (opt)     (opt)")
    print("    - The above syntax would give you the storms between 1967 and 2018 that have values equal to ")
    print("      the top 5 values of desired attribute.")
    print("    - ** UNSTABLE** OPTIONAL kwarg of reverse is there if you want to attempt ot invert the rankings")
    print("* Basic Season Rankings available via rankSeasons(intqty,'attribute',*year1,*year2) function.")
    print("    >>> rankSeasons(10,'tracksHU',1971,2000)     -- Example of input")
    print("                     ^     ^       ^    ^")
    print("                  Report  Attr-   Yr1  Yr2")
    print("                   QTY    ibute  (opt) (opt)")
    print("    - The above syntax would give you the top 10 seasons of most and least hurricane activity")
    print("       between 1971 and 2000")
    print('    - Valid attributes (as of this release) are "tracks","tracksTS","tracksTSstrength","tracksHU"')
    print('      "tracksHUstrength","tracksMHU","MHDP","HDP","ACE","landfalls","landfallsTS", and "landfallsHU"')
    print("* Output CSV Format of Data -- Allows simplified intake of parsed-data into a spreadsheet program")
    print("    >>> stormCSV()    This will output a CSV containing all of the storms in the HURDAT2 record and")
    print("                          sortable attributes")
    print("    >>> seasonCSV()   Outputs a CSV with every season in HURDAT2 and their sortable stats")
    print("-----------------------------------------------------------------------------------------")

print("--------------------------------------------------------")
print("* SCRIPT COMPLETE. HURDAT2 record goes from {} to {}".format(storm[0].year,storm[len(storm)-1].year))
print("* Enter guide() to see available internal, console options")
# --------------------------------------------------------------------------------
