
# hurdat2parser

HURDAT2 ([https://www.nhc.noaa.gov/data/#hurdat](https://www.nhc.noaa.gov/data/#hurdat)) is a collection of records from individual Tropical Cyclones. The Atlantic is focused here, but the NW Pacific HURDAT could easily be implemented via editing of string in parser file. The record goes from 1851 to the last complete season, typically released in May of each year. Storms in the record include subrecords of different times which yields a storm-track. Each of which have important data like center coordinates,wind speeds, pressures, designation status, landfalls, and more.

Each storm is treated like its own object. Every time-entry is treated like a sub-object within each storm. This allows easier work with the data. Included is `hurdat_all_05012019.txt` which is the latest (as of release) of the HURDAT2 data. A secondary script, `hurdat2custom.py`, is included. The intent is to allow running of the script or further manipulation of the data to fit your needs, without the clutter of the main parser file. I like CSV's. Excel (and like-programs) are amazing at quick analysis. So outputting to CSV's enables a lot of possibilities, like placing maxwinds, minmslp, and ACE in one spreadsheet, enabling easy GUI sorting of the data.

When working with data attributes already in the parser script, you can iterate through each storm via:
```python
for x in storm:
	# place code here
```
- storm attributes can be accessed via x.attributeName or getattr(x,"attributeName")

If you want to iterate through every entry in each storm, simply use the syntax:
```python
for x in storm:
	for y in Entry:
		# place code here
```
- entry attributes can be accessed via y.attributeName or getattr(y,"attributeName")

- !!! WARNING !!! - TS-related tallies, right now, are inclusive of hurricane-strength storms. This will likely be changed in the future.

## Included Console Functions
#### stormStats()
```
>>> stormStats(str)
```
This function searches the hurdat2 record for matches to the provided string. Its intent is to return individual storm data. It can also be used to return all data from a specific year or name. Even partial name matching is supported.

```
>>> stormStats("AL122005")
```
- Using the ATCFID syntax (AL##YYYY), you can return information based on a specific storm in the archive

```
>>> stormStats("2005")
```
- Simply using a year (still as a string), you can return all individual storm data from the specified year

```
>>> stormStats("KATRINA")
```
- Searching via name will return (if it exists) all storms in the record that were issued that name
- Searching partials, for example, "Ka", or "Hu" would return all storms in the record with names that start with "KA" or "HU"

#### seasonStats()
```
>>> seasonStats(int,*int)
```
This function collects and reports basic statistics from an entire TC season(s). Simply put a valid search year in the field

```
>>> seasonStats(2005)
```
- This will return some stats on TC year, 2005.
```
>>> seasonStats(2006,2015)
```
- This will return combined stats for years within the 2006 and 2015 range

#### rankStats()
```
>>> rankStats(int,str,*int,*int)
```
This function directly compares individual storms to one another, returning ranks, including ties.
- It should be thought of as more of a rank of stats, than of storms, but alas.
- If not careful, the returned report could be really long. If comparing winds, there are a lot of duplicate entries due to official measurements being in 5kt increments.
```
>>> rankStats(10,"minmslp")
```
- This would return the storms in the record with the top 10 unique, lowest mslp values

Optional arguments can be placed to window the rank results to certain years
```
>>> rankStats(10,"maxwind",2000)
```
- This would return the top 10 values of maxwind ONLY from the 2000 season
```
>>> rankStats(20,"minmslp",1967,2018)
```
- This would return storms with the top 20 values of minimum MSLP within the range of 1967 and 2018

*As of this release, possible attributes available for ranking include: "maxwind", "minmslp", "landfalls", "MHDP", "HDP, or "ACE"*

## Console Function Output Examples

```
>>> stormStats("AL122005")
-----------------------
* ATCF Id: AL122005
* Name: KATRINA
* Entries: 34
* Peak Wind: 77.17 m/s; 150 kts; 172 mph
* Status at Peak Wind: Major Hurricane
* Minimum MSLP: 902 mb
* Major HDP: 13.65 * 10^4 * kt^2
* HDP: 18.2 * 10^4 * kt^2
* ACE: 20.01 * 10^4 * kt^2
* Start Date: 2005-08-23 18Z
* End Date: 2005-08-31 06Z
* Storm Track Period: 7 days, 12 hrs
* Landfall: Yes, 3 Record(s)
```

```
>>> seasonStats(2006,2014)
--------------------------------------------------------
Tropical Cyclone Stats, Between Years 2006-2014
--------------------------------------------------------
Total Tracks: 139
Tropical Storms: 68
Tropical Storm-Strength Storms: 69
Hurricanes: 59
Hurricane-Strength Storms: 61
Major Hurricanes: 24
Major HDP: 203.8 * 10^4 * kt^2
HDP: 574.2 * 10^4 * kt^2
ACE: 987.1 * 10^4 * kt^2
Total Landfalling Systems: 65
Tropical Storm-strength Landfalling Systems: 32
Hurricane-strength Landfalling Systems: 25
--
```

```
>>> rankStats(10,"minmslp",1967,2018)
Storms Ranked by minmslp, 1967-2018
Rank  YEAR  NAME      minmslp
-----------------------------------
   1  2005  WILMA       882
   2  1988  GILBERT     888
   3  2005  RITA        895
   4  1980  ALLEN       899
   5  1969  CAMILLE     900
   6  2005  KATRINA     902
   7  1998  MITCH       905
      2007  DEAN        905
   8  2017  MARIA       908
   9  2004  IVAN        910
  10  2017  IRMA        914
```

## Storm and Entry Attributes w/Explanations
Storm Attributes:
```
maxwind			--> Storm's maximum max-sustained winds (int)
MHDP			--> Storm's Major-Hurricane Destruction Potential
HDP 			--> Storm's Hurricane Destruction Potential (float)
ACE				--> Storm's Accumulated Cyclone Energy (float)
minmslp 		--> Storm's Lowest MSLP entry (int)
landfalls 		--> Quantity (int) of landfalls in the storm's record
LTSStrength		--> bool indicating if a landfall was made at TS (or greater) strength
LHUStrength		--> bool indicating if a landfall was made at hurricane-strength
TSreach 		--> bool indicating if TC ever reached Tropical Storm (TS) designation
strengthTSreach	--> bool indicating if TC ever reached TS strength or greater
HUreach 		--> bool indicating if TC ever reached Hurricane (HU) designation
strengthHUreach --> bool indicating if TC ever reached Hurricane strength
MHUreach 		--> bool indicating if TC ever reached Major Hurricane Status
atcfid 			--> the unique ATCFID of the storm in HURDAT2 (format: "AL##YYYY") (str)
year 			--> Season (year) that the TC took place in (str)
name 			--> Given name of the storm (str)
maxwindstatus	--> Records status of storm during the time of its peak winds (str)
Entry 			--> list of objects corresponding to specific entries for the storm
```

per-Entry Attributes:
```
entryday 		--> raw string of the observation date in the format YYYYMMDD (str)
entryhour 		--> raw string of the observation time in UTC (ex. "0600") (str)
entrytime 		--> Python datetime object of the entry
recidentifier 	--> Special marker (if any) for the entry (ex. "L"-landfall) (str)
status			--> TC designation at time of observation (str)
lat 			--> raw latitude (ex. "25.5N") (str)
latdec 			--> latitude in decimal form (ex. 25.5) (float)
lon 			--> raw longitude (ex. "70.2W") (str)
londec 			--> longitude in decimal form (ex. -70.2) (float)
wind 			--> max sustained winds at the time of obs (str)
ss_scale 		--> the Saffir-Simpson equivalent solely based on wind-speed (str)

* The following attributes indicate observed extent of threshold winds at entrytime
* Cardinal direction abbreviations are used
tsNE	tsSE	tsSW	tsNW 	--> Radii of tropical-storm force winds (str)
ts50NE	ts50SE	ts50SW	ts50NW	--> Radii of strong (50kt) tropical-storm force winds (str)
huNE	huSE	huSW	huNW	--> Radii of hurricane-strength winds (str)
```
- Yes, all that data is held in or derived from HURDAT2!
- Not all data attributes are defined for all storms, especially older storms

season Attributes (all attributes refer to a particular TC season):
```
tracks				--> quantity of tracked systems (int)
tracksTS			--> quantity of tracked systems that reached TS designation (inclusive of Hurricanes) (int)
tracksTSstrength	--> quantity of storms that reached TS-strength (inclusive of hurricane strength storms) (int)
tracksHS			--> quantity of tracked systems that reached HU designation (int)
tracksHSstrength	--> quantity of storms that reached hurricane-strength (int)
tracksMHU 			--> quantity of tracked systems that reached Major Hurricane strength (int)
MHDP				--> Aggregated Major HDP for the season (float)
HDP					--> Aggregated HDP for the season (float)
ACE					--> Aggregated ACE for the season (float)
landfalls			--> tallied storms that have at least 1 landfall on record (int)
landfallsTS			--> tallied storms that have at least 1 landfall at least at TS-strength (inclusive of hurricane-strength landfalls) (int)
landfallsHU			--> tallied storms that have at least 1 landfall at hurricane strength (int)
year				--> TC season (str)
```

## Calculation Explanations
##### HDP (Hurricane Destruction Potential) 
- values were calculated via squaring max-sustained winds, then summed if winds were >= 64 knots (Hurricane force). Furthermore, they were only summed if the observation time was 0Z, 6Z, 12Z, or 18Z. This is because each storm should have data entries at these specific times for its life (official report times). It is also to avoid inclusion of special entries, such as landfalls. This is to keep a more objective standard of space of time. According to Bell, the ACE method was an off-shoot of HDP, with the technique being adopted from William M. Gray and colleagues. Values are then scaled (except for in rankStats)
- *Bell, "Climate Assessment for 1999", Bulletin of the American Meteorological Society, p.S19*

##### ACE (Accumulated Cyclone Energy)
- values were calculated using similar convention as HDP. Except values where winds were >= 34kts (TS-force) were used. Values are then scaled (except for in rankStats)

##### MHDP (Major Hurricane Destruction Potential)
- This parameter has the same convention as HDP, except only values where the storm met or exceeded Category 3 strength (>= 96kts), were used

##### Saffir-Simpson scale (.ss_scale)
- values are solely based on max-sustained winds at the time of observation.
	-	Missing wind data returns a "-1"
	-	TS strength returns "0"

##### seasonStats()
- Hurricane quantities are exclusive of tropical storm quantities, but are inclusive of Major Hurricane quantities
- Seasonal Landfalls are irrespective to geographic locale. Maybe in a future release, US landfalls can be decifered from the data (feel free to work on your own)
- Seasonal landfall quantities are irrespective to the quantity of landfalls a single storm makes. So storms only contribute a max of 1 to the seasonal landfall total

##### storm and season objects
- CAREFUL! In almost all cases, TS tallies are **inclusive** of hurricane strength storms. But in the seasonStats() function, and as noted, they are reported as exlcusive amounts


## Usage / Attribution
- License is GNUv3. Feel free to use/inspect/modify/improve however you wish. If you'd like, let me know how you used it in a project/research you're doing.

## Roadmap
##### Function Tweaking
- Add SS scale duration

##### GIS Function
- Text-delimited format for import in GIS programs
- Inclusion of ID's and lat/long points; and other attributes
- KML output for Google Earth or other GIS viewing

##### Various
- Change TS-related tallies, within storm and season objects, to be exclusive of hurricanes or hurricane-strength storms
- Comment script better to match extent of readme
- investigate seasonal landfall totals. It's possible for storms to make 1 landfall at TS strength, and another at hurricane strength. Currently, TS-strength landfalls are assumed inclusive of HU-strength landfalls. Although likely minor in effect, the aformentioned intention to change TS tallies to be exclusive is more likely to be undertaken

## Changes / Fixes
v1.1 (unreleased)
- Fixed formatting on print(guide) command
- Added readouts to assist user to know what script is formulating at the time
- Added season object (see documentation for attributes)
- Modified seasonStats() to reflect addition of season object
- Fixed note in 'Calculation Explanations' that in seasonStats(), TS and HU quantities were only added if they were thus designated and non-ET at the time; and that all with sub-tropical designation were included in calculation of TS
- Minor tweaks to output of stormStats()

v1.2
- Added Landfalls at TS-strength to storm objects and season objects and seasonStats()
- Added storm and season objects to reflect if a storms reach at least TS and HU strength during their life cycles; to reflect HDP and ACE calculations in v1, and to denote extratropical and subtropical storms.
- Modified TSreach storm attr to remove SS designation as Sub-tropical storms can exceed HU-strength. It now only reflects if a "TS" status exists in the storm's record
- Added Major HDP to storm and season objects, and stat functions. It's the same as HDP, only reflecting times that a hurricane is at Major (Cat 3,4,5) strength
- Add notes to readme / Calculation Explanations about how TS calcs include HU strength storms

## Contact / Comments
- Questions/Corrections/Issues/Ideas/Explanations/Comments can all be made via my github
- Kyle S. Gentry, UNCC '17
