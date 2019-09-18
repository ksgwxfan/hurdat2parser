# This site showed me the basis of nesting objects (classes): https://www.novixys.com/blog/nested-inner-classes-python/

import datetime
import math

storm = []

class NewStorm:
    # The following entries will be amended during successive time Entry process
    maxwind = -1           # Peak Max-Sustained Winds; -1 is a placeholder; will be adjusted during time-series Entry
    ACE = 0                # Accumulated Cyclone Energy; If peak winds(v) >= TS-strength, sum of 6-hr-interval v^2 are taken
    HDP = 0                 # Hurricane Destruction Potential; If peak winds(v) >= HU strength, sum of 6-hr-interval v^2 are taken
    minmslp = 9999         # Minimum MSLP during life of storm; 9999 is just a placeholder
    landfalls = 0          # Will store the quantity of recorded landfall entries
    LHUstrength = False     # Indicates if storm ever records a landfall at HU strength
    TSreach = False         # declares if non-EX TS status is ever reached
    HUreach = False         # determines if non-EX HU status is ever reached
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
        if self.status == "TS" or self.status == "SS": storm[len(storm)-1].TSreach = True
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
        # These lines handle a marker which determines landfall at at-least Hurricane Strength
        if self.recidentifier == "L" and int(self.wind) >= 64: storm[len(storm)-1].LHUstrength = True
        # ------------------------------------------------------------------------------
        if int(self.wind) >= 34 and self.entryhour in ["0000","0600","1200","1800"]:
            storm[len(storm)-1].addACE(int(self.wind)**2)  # Aggregate ACE if wind-speeds are TS-strength or greater
        if int(self.wind) >= 64 and self.entryhour in ["0000","0600","1200","1800"]:
            storm[len(storm)-1].addHDP(int(self.wind)**2)  # Aggregate HDP if wind-speeds are HU-strength or greater
        if int(self.wind) > storm[len(storm)-1].maxwind:
            storm[len(storm)-1].maxwind = int(self.wind)   # Max Wind Speed
            storm[len(storm)-1].maxwindstatus = self.status     # Status at Max Wind Speed
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
            print("* ACE: " + str(round(x.ACE * 10**(-4),2)) + " * 10^4 * kt^2")
            print("* HDP: " + str(round(x.HDP * 10**(-4),2)) + " * 10^4 * kt^2")
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
    seasonStorms = 0
    seasonTS = 0
    seasonHU = 0
    seasonMHU = 0
    seasonHDP = 0
    seasonACE = 0
    seasonLandfalls = 0
    seasonLHU = 0
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
    for x in storm:
        if int(x.atcfid[4:8]) >= yr and int(x.atcfid[4:8]) <= yr2:
            seasonStorms += 1
            if x.TSreach == True: seasonTS += 1
            if x.HUreach == True: seasonHU += 1
            if x.MHUreach == True: seasonMHU += 1
            seasonHDP += x.HDP
            seasonACE += x.ACE
            if x.landfalls > 0: seasonLandfalls += 1
            if x.LHUstrength == True: seasonLHU += 1
    # Print Report
    if len(args) > 0:
        print("--------------------------------------------------------")
        print("Tropical Cyclone Stats, Between Years {}-{}".format(yr,yr2))
        print("--------------------------------------------------------")
    else:
        print("----------------------------------------")
        print("Tropical Cyclone Stats for {}".format(yr))
        print("----------------------------------------")
    print("Total Tracks: {}".format(seasonStorms))
    print("Tropical Storms: {}".format(seasonTS-seasonHU))
    print("Hurricanes: {}".format(seasonHU))
    print("Major Hurricanes: {}".format(seasonMHU))
    print("HDP: {} * 10^4 * kt^2".format(round(seasonHDP*10**(-4),1)))
    print("ACE: {} * 10^4 * kt^2".format(round(seasonACE*10**(-4),1)))
    print("Total Landfalling Systems: {}".format(seasonLandfalls))
    print("Hurricane-strength Landfalling Systems: {}".format(seasonLHU))
    print("--")

def rankStats(tcqty,st_attribute,*args):
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
            validstorms.append(x)
    if st_attribute == "minmslp":   # If we're dealing with minmslp, don't include reverse (we want lowest to highest)
        rank = sorted(validstorms, key=lambda st: getattr(st,st_attribute))
    else:
        rank = sorted(validstorms, key=lambda st: getattr(st,st_attribute), reverse=True)
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
    if len(args) == 1: print("Storms Ranked by {}, {}".format(st_attribute,year1))
    else: print("Storms Ranked by {}, {}-{}".format(st_attribute,year1,year2))
    print("Rank  YEAR  NAME      {}\n-----------------------------------".format(st_attribute))
    rank_ind = 0     # Will be used for in format of ranking (to place rank numbers)
    for x in range(len(rank)):
        if getattr(rank[x],st_attribute) in uniquevalues:
            if rankadded[uniquevalues.index(getattr(rank[x],st_attribute))] == False:
                print("{:>4}  {}  {:10}  {}".format(rank_ind + 1,rank[x].year,rank[x].name,getattr(rank[x],st_attribute)))
                rankadded[uniquevalues.index(getattr(rank[x],st_attribute))] = True
                rank_ind += 1
            else:
                print("{:>4}  {}  {:10}  {}".format(" ",rank[x].year,rank[x].name,getattr(rank[x],st_attribute)))

# MAIN PROGRAM -------------------------------------------------------------------

with open("hurdat_all_05012019.txt","r") as f:
    for each in f.readlines():
        templine = each.split(",")
        if templine[0][0:2] == "AL":     # NEW STORM
            # Creates new storm object, and applying the ATCFID and Name
            storm.append(NewStorm(templine[0].strip(" "),templine[1].strip(" ")))
            curr_index = len(storm) - 1
        else:   # Need to add a time-based data-entry record for the storm
            storm[curr_index].addTime(templine)
# --------------------------------------------------------------------------------
