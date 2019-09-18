# hurdat2parser

HURDAT2 [https://www.nhc.noaa.gov/data/#hurdat](https://www.nhc.noaa.gov/data/#hurdat) is a collection of individual records of Tropical Cyclones (the Atlantic is focused here), pieced together all in one file. The record goes from 1851 to the last complete season, typically released in May of each year. Storms in the record include subrecords of different times which yields a storm-track. Each of which have important data like center coordinates,wind speeds, pressures, designation status, landfalls, and more.

This script was made by analyzing the HURDAT2 record. Each storm is treated like an object. Each time-entry is treated like a sub-object within the storm. This allows easier work with the data. Included is 'hurdat_all_05012019.txt' which is the latest (as of release) of the HURDAT2 data. A secondary script, 'hurdat2custom.py', is included. The intent is to allow further manipulation of the data to fit your needs, without the clutter of the main parser file. I like CSV's. Excel (and like-programs) are amazing at quick analysis. So outputting to CSV's enables a lot of possibilities, like placing maxwinds, minmslp, and ACE in one spreadsheet, enabling easy GUI sorting of the data. You could output the data to GIS or KML formats for mapping analysis and visualization. I included a simple function in the file demonstrating use.

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

### Included Console Functions
#### stormStats()
```python
>>> stormStats(str)
```
This function searches the hurdat2 record for matches to the provided string. Its intent is to return individual storm data. It can also be used to return all data from a specific year or name. Even partial name matching is supported.

```python
>>> stormStats("AL122005")
```
- Using the ATCFID syntax (AL##YYYY), you can return information based on a specific storm in the archive

```python
>>> stormStats("2005")
```
- Simply using a year (still as a string), you can return all individual storm data from the specified year

```python
>>> stormStats("KATRINA")
```
- Searching via name will return (if it exists) all storms in the record that were issued that name
- Searching partials, for example, "Ka", or "Hu" would return all storms in the record with names that start with "KA" or "HU"

#### seasonStats()
```python
>>> seasonStats(int,*int)
```
This function collects and reports basic statistics from an entire TC season(s). Simply put a valid search year in the field

```python
>>> seasonStats(2005)
```
- This will return some stats on TC year, 2005.
```python
>>> seasonStats(2006,2015)
```
- This will return combined stats for years within the 2006 and 2015 range

#### rankStats()
```python
>>> rankStats(int,str,*int,*int)
```
This function directly compares individual storms to one another, returning ranks, including ties.
- It should be thought of as more of a rank of stats, than of storms, but alas.
- If not careful, the returned report could be really long. If comparing winds, there are a lot of duplicate entries due to official measurements being in 5kt increments.
```python
>>> rankStats(10,"minmslp")
```
- This would return the storms in the record with the top 10 unique, lowest mslp values

Optional arguments can be placed to window the rank results to certain years
```python
>>> rankStats(10,"maxwind",2000)
```
- This would return the top 10 values of maxwind ONLY from the 2000 season


```python
>>> rankStats(20,"minmslp",1967,2018)
```
- This would return storms with the top 20 values of minimum MSLP within the range of 1967 and 2018

*As of this release, possible attributes available for ranking include: "maxwind", "minmslp", "landfalls", "HDP, "ACE"*

### Console Function Output Examples

```python
>>> stormStats("AL122005")
-----------------------
* ATCF Id: AL122005
* Name: KATRINA
* Entries: 34
* Peak Wind: 77.17 m/s; 150 kts; 172 mph
* Status at Peak Wind: Major Hurricane
* Minimum MSLP: 902 mb
* ACE: 20.01 * 10^4 * kt^2
* HDP: 18.2 * 10^4 * kt^2
* Start Date: 2005-08-23 18Z
* End Date: 2005-08-31 06Z
* Storm Track Period: 7 days, 12 hrs
* Landfall: Yes, 3 Record(s)
```

```python
>>> seasonStats(2006,2014)
--------------------------------------------------------
Tropical Cyclone Stats, Between Years 2006-2014
--------------------------------------------------------
Total Tracks: 139
Tropical Storms: 70
Hurricanes: 59
Major Hurricanes: 24
HDP: 574.2 * 10^4 * kt^2
ACE: 987.1 * 10^4 * kt^2
Total Landfalling Systems: 65
Hurricane-strength Landfalling Systems: 25
--
```

```python
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

### Storm and Entry Attributes w/Explanations
Storm Attributes:
```python
maxwind			--> Storm's maximum max-sustained winds (int)
HDP 			--> Storm's Hurricane Destruction Potential (float)
ACE				--> Storm's Accumulated Cyclone Energy (float)
minmslp 		--> Storm's Lowest MSLP entry (int)
landfalls 		--> Quantity (int) of landfalls in the storm's record
LHUStrength		--> bool indicating if a landfall was made at hurricane-strength
TSreach 		--> bool indicating if TC ever reached non-extratropical Tropical Storm Status; includes Subtropical designation
HUreach 		--> bool indicating if TC ever reached non-extratropical Hurricane Status
MHUreach 		--> bool indicating if TC ever reached Major Hurricane Status
atcfid 			--> the unique ATCFID of the storm in HURDAT2 (format: "AL##YYYY") (str)
year 			--> Season (year) that the TC took place in (str)
name 			--> Given name of the storm (str)
maxwindstatus	--> Records status of storm during the time of its peak winds (str)
Entry 			--> list of objects corresponding to specific entries for the storm
```

Entry Attributes:
```python
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









