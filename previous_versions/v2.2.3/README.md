# hurdat2parser -- v2.2.3
---
### *Interpreting the Hurdat2 Tropical Cyclone Dataset using Python*

Hurdat2 ([https://www.nhc.noaa.gov/data/#hurdat](https://www.nhc.noaa.gov/data/#hurdat)) is a collection of records from individual Tropical Cyclones. The two primary Hurdat2 records are for the Atlantic (since 1850) and East/Central-Pacific Oceans (since 1949).

The purpose of this module is to provide a quick way to analyze the Hurdat2 datasets. It includes methods for retrieving, inspecting, ranking, or even exporting data for seasons, individual storms, or climatological eras.

PyPI Link: [https://pypi.org/project/hurdat2parser/](https://pypi.org/project/hurdat2parser/)

## Contents
* [Changes/Fixes in this Version (2.2.3)](#changes-in-this-version-223)
* [Requirements, Installation, and getting the data](#installation)
* [Importing the module](#importing-the-module)
* [Example Calls](#example-calls)
* [Hurdat2 Object Structure](#hurdat2-object-structure)
* [Methods &amp; Attributes](#methods-and-attributes)
* [Note on Landfall Data](#landfall-data)
* [Future/Under-Development/Unreleased Methods](#access-to-future-methods)
* [Roadmap](#roadmap)
* [Credits](#credits)
* [Copyright/License](#copyright)

## Changes in this Version (2.2.3)
- Accounts for the possibility of typos/errors in the acutal database.
  - Notifies the user if a storm has already been ingested, but does overwrite the previous `TropicalCyclone` entry.
  - Will skip a `TCRecordEntry` and notify the user if an error occurs whilst trying to generate it.
- fix for `track_map()` to work for cyclones prior to 1900. There was an issue with the label formatting I was using.
- fix for rankings for empty partial seasons in `rank_seasons_thru` where quantity of ranks were being returned as one too many.

[&#8679; back to Contents](#contents)

## Installation

- At the command prompt, run `pip install hurdat2parser`
  - When installing, packages `pyshp`, `geojson`, and `matplotlib` will be downloaded as dependencies (if necessary). From scratch, it's around 30MB total of dependency downloads.

[&#8679; back to Contents](#contents)

## Importing the Module

Follow these commands for genesis!

```python
>>> import hurdat2parser
#or if you're lazy like me...
>>> import hurdat2parser as hd2
```

- If you want a local copy of a hurdat2file, got to [https://www.nhc.noaa.gov/data/#hurdat](https://www.nhc.noaa.gov/data/#hurdat) to download. It's a text file. Hurdat2 files for the Atlantic Basin and East/Central Pacific Basins are available and compatible with the package. 
  - As of `v2.2` this isn't 100% necessary as the datasets can be automatic retrieval can be attempted (keep reading). This method does not keep a local copy though (as of this version).

To read-in a local file:<br/>`>>> atl = hurdat2parser.Hurdat2("path_to_hurdat2.txt")`

And/Or to let the module download and ingest the data for you:

- North Atlantic Basin<br/>`>>> atl = hurdat2parser.Hurdat2(basin="atl")`
  - Any of the following will be recognized: `"al"`, `"atl"`, or `"atlantic"`
- NE/CEN Pacific Basin<br/>`>>> pac = hurdat2parser.Hurdat2(basin="pac")`
  - Any of the following will be recognized: `"pac"`, `"nepac"`, or `"pacific"`
- Of note, the above commands do not keep a local copy for next time

To include a url to download, set the kwarg `urlcheck` to `True`. This generally will not be needed unless you want to use my (shameless plug) daily-updated current-season hurdat2 during the year (on my website; see [Copyright](#copyright) section)<br/>
`>>> atl = hurdat2parser.Hurdat2("http://crazygonuts.aboutweatherstuff/myhurdat2file.txt", urlcheck=True)`

These various ways can be mixed/matched too.

* For the `Hurdat2` object, I highly recommend to use something shortened and readable for the parent object name (like `atl` or `al` for the Atlantic database and `ep`, `cp`, or `pac` for the East/Central Pacific)*

After a few seconds (a little longer if downloading) you'll be ready to dive into the data! Subsequent examples imply the use of the Atlantic Hurdat2 (`atl`).

[&#8679; back to Contents](#contents)

## Example calls

There are several ways to invoke a call to a `Season` or `TropicalCyclone` object. These ways are detailed in the [next section](#hurdat2-object-structure), indirectly in the [Methods and Attribute](#methods-and-attributes) tables, and in a large portion of method docstrings. This brief section will demonstrate the ways I navigate the dataset with this module when coding and testing.

- `Season` objects (just the year)
  - `atl[1995]`
- `TropicalCyclone` objects
  - by atcfid number
    - `atl[2005,12]` -- returns the object for hurricane katrina (`AL200512`)
  - by name
    - `atl["danny"]` -- shows a list of storms in the record given the name of Danny, allowing the user to select which one they desire
    - `atl["_rita"]`, or `atl["-rita"]` -- beginning the name with an underscore or dash shows the most-recent storm named as such (this returns the most-notorious storms as well since storm names can be retired according to the destruction they cause)
- `TCRecordEntry` calls
  - `atl[1980,4,29]` -- The entry at index 29 (30th total entry) for Hurricane Allen
  - or `atl["_allen", 29]`

[&#8679; back to Contents](#contents)

## Hurdat2 Object Structure

- The structure of a `Hurdat2` object is hierarchal. It has two primary dictionaries:
  - `<Hurdat2>.tc` - A dictionary containing all `TropicalCyclone` objects compiled from the record.
    - Individual storms can be accessed using their ATCF ID, a unique 8-character id for each tropical cyclone <u>OR</u> a name of a storm.
	  - `atl["AL122005"]` - Call for Hurricane Katrina's Data using its ATCFID (it being the 12th storm from the 2005 Atlantic Season).
	  - `atl["Name"]` - Use this if you know the name, but the year is unknown. A partial search is okay, but may receive less accurate results. It uses the `difflib` package to calculate close matches and outputs a list (if applicable) that you then can select from.
	  - `atl["_Name"]` or `atl["-Name"]` - including an underscore or dash at the beginning of the name will return the **NEWEST** storm by a name that matches. Use this for the most-notorious storms, as retired names would be the newest.
  - `<Hurdat2>.season` - A dictionary holding `Season` objects (yearly data).
    - A Season's data is accessed via a simple year key of type `int`.
	  - `atl[1995]` retrieves the object associated with the 1995 hurricane season.
- `Season` objects also have a dictionary (`<Season>.tc`) that holds `TropicalCyclone` objects, specific to the year. Some different ways to call these objects:
  - TC Number: `atl[1988,8]` or `atl[1988][8]` - Use the storm number (type `int`) from the season. This is defined by using the ATCF ID.
  - Storm starting letter (or name): `atl[1995, "o"]` or `atl[1995, "opal"]` or `atl[1995]["Opal"]` - This method works for most modern tropical storms, as they have been issued names. So in these cases, you wouldn't need to know the atcfid number. Also of note, because tropical depressions aren't issued names, the id numbers do not always correlate with the co-inciding letter of the alphabet. For example, Hurricane Andrew's ATCFID is `AL041992`.
- `TropicalCyclone` objects contain a `list` of `TCRecordEntry` objects in time-ascending order. To access these:
  - `atl[2005, 12, 21]` would grab the `TCRecordEntry` for Hurricane Katrina at index 21.

[&#8679; back to Contents](#contents)

## Methods and Attributes

Now that you know how to call a particular object of interest, you can now access its data, using methods and attributes. The docstrings (accessed via `help()`) are quite detailed and methods that take arguments have example calls listed. But here is a quick reference to what is available, along with some shortcuts and example calls to assist navigating while in this document.

- [`Hurdat2` Methods &amp; Attributes](#hurdat2-methods-and-attributes)
- [`Season` and `TropicalCyclone` Shared Methods &amp; Attributes](#shared-methods-and-attributes-for-season-and-tropicalcyclone)
- [`Season`-only Methods &amp; Attributes](#season-only-methods-and-attributes)
- [`TropicalCyclone`-only Methods &amp; Attributes](#tropicalcyclone-only-methods-and-attributes)
- [`TCRecordEntry` Attributes](#tcrecordentry-attributes)

#### `Hurdat2` Methods and Attributes

Attributes | Description | Examples
:---: | :---: | :---:
`rank_seasons(...)` | Print a report that lists a ranking of seasons based on an inquired attribute. Other details are included in the report as well, but they'll be ordered according to the attribute passed. Though not all attributes are represented in the printed report, the ordering will be correct based on the inquired attribute. It also takes positional keyword arguments for `year1=None` and `year2=None`, allowing optional ranking to limit the scope of the report to a range of years (this also applies to subsequent ranking methods). | `atl.rank_seasons(5, "track_distance_TS", 1971, 2000, True)`
`rank_seasons_thru(...)` | Print a ranking of seasons where you can use part of the season; a way to rank attributes up to or between certain dates. Special keyword arguments, `start` (internal default of `(1,1)`) and  `thru` (default of `(12, 31)`), tuples representing a month and day, (ex. `(9,6)` for September 6) enable ranking of partial seasons.<br>\*As a side note, exclusion of these keywords just make this a wrapper for the above `rank_seasons` method. | `atl.rank_seasons_thru(10, "TSreach", 1967, thru=(9,30))`
`rank_climo(...)` | Yet another useful ranking method. This allows one to rank attributes assessed over several to many years (climatological periods) to one another. Optional keyword argument `climatology` (default is 30 years) controls the span of time that data is collected and `increment` (default is 5 years) dictates the temporal distance between periods | `atl.rank_climo(20,"track_distance_TC", climatology=10, increment=1)`
`rank_storms(...)` | Print a report that compares storms and their attributes to each other. Similar to the above methods, other data is included in the report. See the docstring for info on `coordextent` kw usage | `atl.rank_storms(20,"HDP",1967)`
`multi_season_info(...)` | Prints a report a gathered statistics based on a range of years. This is similar to the `info()` methods referenced in the next section. This could be thought of as an info method for a climatological period | `atl.multi_season_info(1991, 2000)`<br />`atl[2010, 2019]`
`storm_name_search(...)` | Search through the entire Hurdat2 record for storms issued a name. If the positional keyword `info` is `True`, the matching storm's info method will print. | `atl.storm_name_search("Hugo")`
`output_climo(...)` | outputs a .csv file using the `csv` package of 1-year incremented climatological periods. This csv file can then be opened in a spreadsheet program. To compare or rank, the spreadsheet GUI layout is much easier to use especially due to instant sorting and filtering. This accepts a positional keyword argument (`climatology=30`). | `atl.output_climo(15)`
`output_seasons_csv(...)` | Similar to the above, but for seasons. It takes no arguments. In other words, it would be redundant to run it multiple times, because as the `hurdat2parser` package doesn't natively allow modification of the data, it would just output the same data over and over. The only exception would be when the Hurdat2 database is updated by the NHC. With this in mind, it will automatically write-over the csv if it already exists (file-name is auto-generated within the method). | `atl.output_seasons_csv()`
`output_storms_csv(...)` | Similar to above, but for individual storms. | `atl.output_storms_csv()`
`climograph()` | displays a graph of the climatological tendency of a variable over multiple seasons (see docstring for a how-to) | `atl.climograph("ACE", 10, 1, year1=1967)`
`coord_contains(...)` | Takes 3 tupled lat-lon coordinates. The purpose is to inquire whether the first arg (the test coordinate) is contained within a bounding box formed by the other two coordinates passed (returns a `bool`. This is generally just accessed via the ranking methods | `atl.coord_contains(`<br />&nbsp;&nbsp;&nbsp;&nbsp;`[30.4,-85.0]`,<br />&nbsp;&nbsp;&nbsp;&nbsp;`[31.5, 86.0],`<br />&nbsp;&nbsp;&nbsp;&nbsp;`[29.0, 84.0]`<br />`) -> True`
`BASIN_DICT` | A dictionary containing abbreviations (keys) and definitions (values) of various basins around the world that hurricane data is kept. This is referenced via the `basin()` method. The data used to form this object came from IBTrACS | `atl.BASIN_DICT`
`basin(season=None)` | Interprets and returns a readable string identifying the TC basin based on the storms within the record. This allows support of dynamically-created singular OR multiple Hurdat2 datasets OR individual seasons (if a `Season` object is passed to the method). The data used to form this property came from IBTrACS | `atl.basin() -> "North Atlantic Basin"
`record_range` | Returns a tuple of the beginning year and end year of the Hurdat2 record | `atl.record_range -> (1851, 2020)`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### Shared Methods and Attributes for `Season` and `TropicalCyclone`

Attributes | Description | Examples
:---: | :---: | :---:
`output_shp()` | Generate a GIS-compatible Shapefile using the `shapefile` package | `atl[1988]["Gilbert"].output_shp()`
`output_geojson()` | Generate a GIS-compatible and text-readable `.geojson` file via the `geojson` package; can also be used in GIS applications | `atl[2000].output_geojson()`
`summary()` | Prints detailed statistics for the season or life of the TC | `atl[2019]["dorian"].summary()`
`landfalls`<br /> | \*SEE [DISCLAIMER FOR LANDFALL INFO](#landfall-data)\* Sum of all landfalls (remember, a storm can make multiple landfalls). `<Season>.landfalls` is also an unfiltered aggregate of its storms landfalls. At the seasonal level, you'd probably be more interested in the attribute `landfall_TC` (see following section) | `atl[1960]["doNnA"].landfalls`
`landfall_<STATUS>`<br />*\-can be TC, TD, TS, HU, or MHU* | `Season`: qty of TC's that made landfall as the inquired status; `TropicalCyclone`: `bool` indicating if the storm made landfall while the inquired status<br />*\-CAUTION: These attrs are exclusive of landfalls made while of stronger designation\-* | `atl[1996].landfall_TS -> 2`<br />`atl[2011]["I"].landfall_HU -> True`
`<STATUS>reach`<br />*\-can be TC, TD, TS, HU, or MHU* | `Season`: qty of TC's that reached <u>at least</u> the inquired status; `TropicalCyclone`: `bool` indicating if the storm ever was designated as the inquired status | `atl[2010].HUreach -> 12`<br />`atl[1991]["danny"].HUreach -> False`
`ACE`, `HDP`, or `MHDP` | Returns the specified Energy Index reading associated with the season or storm. Note that the MHDP is one you likely won't see elsewhere. It's formula is the same as ACE and HDP but for major-hurricanes only | `atl[1966].HDP`
`track_distance` | The calculated distance (in nmi) for the entire track of the storm (or aggregate of the season), regardless of status | `atl[1954]["hazel"].track_distance`
`track_distance_<STATUS>`<br>*\-can be TC, TD, TS, HU, or MHU* | The distance traversed while storm(s) was(were) <u>at least</u> the status designation | `atl[1961].track_distance_MHU`
`cat45reach`<br>`cat5reach` | For `Season` objects, returns the quantity of storms that reached category 4+ status or category 5 status (respectively)<br>For `TropicalCyclone` objects, returns a `bool`, indicating if the TC ever achieved cat 4+ or 5 status (respectively) | `atl[2020].cat45reach -> 5`<br>`atl[2020].cat5reach -> 0`<br>`atl[2020]["Iota"].cat5reach -> False`
`hurdat2()` | This method prints a hurdat2-formatted output of the storms's data, emulating the actual hurdat2 record from which it (the Season or Tropical Cyclone) was created | `atl[2005].hurdat2()`
`duration` | Returns the length of the Season or life of the cyclone (Of note, the `TropicalCyclone` property disregards storm status) | `atl[2022].duration`
`tc_entries` | Returns a list of `TCRecordEntry`'s from where a storm was designated as a tropical cyclone | `atl["_katrina"].tc_entries`
`start_date` | The beginning moment of the Season or storm | `atl[1938].start_date`
`start_ordinal` | The quantified day of the year of the beginning moment of the Season or storm | `atl[1938].start_ordinal`
`end_date` | The ending date of the Season or storm | `atl[1954, 16].end_date`
`end_ordinal` | The quantified day of the year of the ending date of the Season or storm | `atl[1954].end_ordinal`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### `Season` Only Methods and Attributes
Attribute | Description | Example
:---: | :---: | :---:
`output_shp_segmented()` | Generates a shapefile including each segment from each tropical-cyclone from a given season; each individual segment from each individual storm will be represented | `atl[1932].output_shp_segmented()`
`output_geojson_segmented()` | Generates a geojson including each segment from each tropical-cyclone from a given season; each individual segment from each individual storm will be representeds | `atl[2003].output_geojson_segmented()`
`tracks` | Returns the quantity of tropical cyclones from a season | `atl[1995].tracks`
`<STATUS>only`<br />*\-can be TD, TS, or HU* | Returns the quantity of TC's from a season that made were given the inquired designation, but never strengthened beyond it. `HUonly` implies Category 1 and 2 storms only. To inquire about `MHU`, use the `MHUreach` attr | `atl[1950].TDonly`<br />`atl[2017].HUonly`
`stats()` | prints a report filled with statistics and ranks for the season, optionally compared with a subset of seasons and/or partial seasons. Though it technically exists as a  `TropicalCyclone` method, its iteration is a mirror-method of `.info()` | `atl[2020].stats()`<br>`atl[2005].stats(thru=(9,30))`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### `TropicalCyclone` Only Methods and Attributes
| Attribute | Description | Example
:---: | :---: | :---:
`gps` | Returns a `list` of tupled latitude and Longitude coordinates | `atl[1998]["MITCH"].gps`
`maxwind` | Returns the highest maximum sustained wind-speed observed in the tropical cyclone | `atl["_katrina"].maxwind`
`minmslp` | Returns the lowest recorded pressure of the TC | `atl[1955][10].minmslp`
`maxwind_mslp`<br>`minmslp_wind` | Returns the MSLP (wind) occurring at the time of peak-winds (minimum MSLP) respectively. These attributes were included because peak winds and minimum MSLP do not necessarily occur at the same time. | `atl[2015]["joaquin"].maxwind_mslp -> 934`<br>`atl[2015]["joaquin"].minmslp_wind -> 120`<br>\* This example was given as Joaquin's peak winds (135) were not observed at the time of Joaquin's minimum MSLP (931)
`<EI>_per_nmi`<br />*\-can be ACE, HDP, or MHDP* | Returns the inquired energy index divided by the track distance covered while the energy index was being contributed to (`ACE` &rarr; `track_distance_TS` or `HDP` &rarr; `track_distance_HU` as examples). WARNING! These attributes do not have any kind of threshold controls, so storms which were short-lived can have high values | `atl[1964][10].HDP_per_nmi`<br />`atl[2016]["matthew"].ACE_per_nmi`
`<EI>_perc_ACE` &rarr; *\-can be HDP or MHDP*<br />`HDP_perc_MHDP` | Simply the storm's HDP or MHDP divided by ACE or the MHDP divided by the HDP. Look at this as the <u>percentage</u> (as a float between 0 and 1) of the storm's ACE or HDP that was contributed to while a Hurricane or Major Hurricane, respectively | `atl[2017]["IRMA"].HDP_perc_ACE`
`track_<EI1>_perc_<EI2>`<br />*\-&lt;EI1&gt; can be TS, HU, or MHU*<br />*\-&lt;EI2&gt; can be TC, TS, HU, or MHU* | Returns the the storm's &lt;EI2&gt; track_distance divided by the track distance while of status &lt;EI1&gt;. &lt;EI1&gt; must be of higher hierarchal status than &lt;EI2&gt; | `atl[2005][25].track_HU_perc_TC`<br />`atl[2003]["Fabian"].track_MHU_perc_TS`
`track_map()` | Generates a map of the storm's track using `matplotlib`. Check the docstring for ways to modify the output to your liking. | `atl["_katrina"].track_map()`
`perc_ACE`<br>`perc_HDP`<br>`perc_MHDP` | Return the percentage (in decimal form) of the contribution of the storm's ACE, HDP, or MHDP value to the season's value | `atl["_matthew"].perc_MHDP
`info()` | Prints basic stats for the tropical cyclone | `atl[2005][12].info()`
`ACE_no_landfall` | Returns the ACE of the storm prior to any landfall made | `atl["_ivan"].ACE_no_landfall
`duration_<SUFFIX>`<br />*\*&lt;SUFFIX&gt; can be TC, TS, HU, MHU* | Returns the aggregated length in days that the cyclone spent as on of the given statuses. These do account for storm status loss and possible reaquisition | `atl["_irma"].duration_MHU`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### `TCRecordEntry` Attributes

- Only the most-common attributes will be referenced in this document. A comprehensive list is available via `help`

| Attribute | Description
:---: | :---:
`entrytime` | A `datetime.datetime` object of the entry's timestamp
`status` | The designated 2-letter abbreviation representing the storm's status
`location`<br />`location_rev` | A tuple of the latitude/longitude coordinates; `location_rev` is reversed in order, a longitude/latitude tuple; seemingly favored for GIS use.
`wind` | The maximum-sustained winds at the time of entry-recording
`mslp` | The Mean Sea-Level Pressure (in hPa or mb) at the time of entry-recording
`hurdat2()` | Returns a reassembled Hurdat2-formatted string, identical to the one parsed to create the entry
`maxwind_radius` | The Radius of Maximum Winds. Currently, it is only available for storms since 2021, and is assumed that in subsequent releases, this variable will continue to be updated. It is unknown if this data for previous seasons will (or can) be back-filled.
`avg_wind_extent_<SUFFIX>`<br/>Suffix can be `TS`, `TS50`, or `HU` | The statistical mean of the reported wind-extents (quadrants). Wind extents are only available for storms since 2004 
`areal_extent_<SUFFIX>`<br/>Suffix can be `TS`, `TS50`, or `HU` | The calculated area covered by the extent of winds of specified strengths (of note, wind extents are only available for storms since 2004)
`track_distance`<br/>`track_distance_<SUFFIX>`<br/>Suffix can be `TC`, `TS`, `HU`, or `MHU` | returns the distance tracked by the system from its genesist to the point of the entry. The variables with suffixes do account for status in their calculations
`previous_entry`<br/>`next_entry` | Returns the entry prior-to or after the `TCRecordEntry` that it is called from
`direction()` | Returns the heading in degrees that the storm is going. A readable cardinal direction can be returned if `True` is passed to the method
`speed` | The average speed between the previous entry and this one in nm/h<br/>Of Note, remember that the `Hurdat2` spatial resolution is 0.1 degrees latitude/longitude. So some appreciable error may be present

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)<br />
[&#8679; back to Contents](#contents)

## Landfall Data

An important point to keep in mind when viewing data and ranking, Hurdat2's landfall data is incomplete. It is progressively being updated in conjunction with the yearly release of the dataset. Please see the documentation  [Hurdat2 Format Guide](https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-atl-1851-2021.pdf) for more detail on currently-available landfall data temporal scope.

[&#8679; back to Contents](#contents)

## Access to Future Methods

In `_future.py`, I have some stuff that I've started to develop but not ready/sure to release. The methods are functional though. The quickest way of accessing it is:

```python
>>> import hurdat2parser._future as future
```

Valid classes reflect those of the main `hurdat2parser` object, namely `future.Hurdat2`, `future.Season`, `future.TropicalCyclone`, or `future.TCRecordEntry`. They'll be empty if I don't have anything I'm currently developing for that respective class/object. You can see what methods I have available by running `dir()` on the class.

When calling, you will need to manually pass a valid object (a substitute for `self`). For example:
```python
>>> future.Season.track_map(atl[1984])
```

[&#8679; back to Contents](#contents)

## Roadmap

- [ ] Include more `Season.duration`-related properties based on status
- [ ] Speed-up `<Season>.stats()` report; because it employs `rank_seasons_thru`, and since that is quite snappy, I think the `stats()` method should be quick too. I'll investigate.
- [ ] Develop matplotlib-based graphs located in `_future`
- [ ] Comparison methods to directly compare one season to another or specific storms to another.
- [ ] Revamp `hurdat2()` method of `TropicalCyclone` and `Season` objects to optionally return a string instead of merely printing to console
- [ ] Formulate a `stats()` method for `TropicalCyclone`s (to eventually replace their `info` method); including ranking/comparing to storms across the record or a subset of seasons (right now, this method is just a wrapper for the `info()` method.
- [ ] Track distance percentage of season total for `TropicalCyclone`s
- [ ] Maybe simpler rank methods so values sought for ranking will guarantee to show
- [ ] add maps files for Pacific-centric storms
- [ ] investigate adding a minmslp_entry or maxwind_entry property for TropicalCyclone objects. It is acknowledged though that multiple entries can have the same minimum mslp or max wind.
- [ ] a `genesis` property, returning the first entry from a `TropicalCyclone` earning the TC designation. Not sure the feasability of this. I'll think about it.
- [x] Include legends for `<TropicalCyclone>.track_map()`
- [x] Account for absent season starts when using stats thru certain time

[&#8679; back to Contents](#contents)

## Credits

- HURDAT Reference: `Landsea, C. W. and J. L. Franklin, 2013: Atlantic Hurricane Database Uncertainty and Presentation of a New Database Format. Mon. Wea. Rev., 141, 3576-3592.`
- [Haversine Formula (via Wikipedia)](https://en.wikipedia.org/wiki/Haversine_formula)
- Bell, et. al. Climate Assessment for 1999. *Bulletin of the American Meteorological Society.* Vol 81, No. 6. June 2000. S19.
- <span>G. Bell, M. Chelliah.</span> *Journal of Climate.* Vol. 19, Issue 4. pg 593. 15 February 2006.
- [Hurdat2 Format Guide (PDF)](https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-atl-1851-2021.pdf)
- [Natural Earth](https://www.naturalearthdata.com/) GIS Data (data extracted there-from to display maps)

[&#8679; back to Contents](#contents)

## Copyright

**Author**: Kyle S. Gentry<br />
Copyright &copy; 2019-2023, Kyle Gentry (KyleSGentry@outlook.com)<br />
**License**: MIT<br />
**GitHub**: [https://github.com/ksgwxfan/hurdat2parser](https://github.com/ksgwxfan/hurdat2parser)<br />
**Author's Webpages**:
 - [https://ksgwxfan.github.io/](https://ksgwxfan.github.io/)<br />
 - [http://echotops.blogspot.com/](http://echotops.blogspot.com/)

[&#8679; back to Contents](#contents)












