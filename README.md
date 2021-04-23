# hurdat2parser -- v2.0.0
---
### *An Object-Oriented Approach to Viewing Tropical Cyclone Data*

HURDAT2 ([https://www.nhc.noaa.gov/data/#hurdat](https://www.nhc.noaa.gov/data/#hurdat)) is a collection of records from individual Tropical Cyclones. The two primary HURDAT2 records are for the Atlantic (since 1850) and East/Central-Pacific Oceans (since 1949).

The purpose of this module is to provide a quick way to analyze the HURDAT2 datasets. It includes methods for retrieving, inspecting, ranking, or even exporting data for seasons, individual storms, or climatological eras.

PyPI Link: [https://pypi.org/project/hurdat2parser/](https://pypi.org/project/hurdat2parser/)

## Contents
* [Requirements, Installation, and getting the data](#installation)
* [Importing the module](#importing-the-module)
* [HURDAT2 Object Structure](#hurdat2-object-structure)
* [Methods &amp; Attributes](#methods-and-attributes)
* [Note on Landfall Data](#landfall-data)
* [Roadmap](#roadmap)
* [Credits](#credits)
* [Copyright/License](#copyright)

## Installation

- At the command prompt, run `pip install hurdat2parser`
  - When installing, packages `pyshp` and `geojson` will be downloaded as dependencies
- You'll then need the actual Hurdat2 Data. You can get it [HERE](https://www.nhc.noaa.gov/data/#hurdat). It's a text file. HURDAT2 files for the Atlantic Basin and East/Central Pacific Basins are available and compatible with the package.

[&#8679; back to Contents](#contents)

## Importing the Module

- Import the module and invoke a call to the `Hurdat2` class while passing the file-name of the HURDAT2 dataset

```python
>>> import hurdat2parser
>>> atl = hurdat2parser.Hurdat2("path_to_hurdat2.txt")
```
- * For the `Hurdat2` object, I highly recommend to use something shortened and readable for the parent object name (like `atl` or `al` for the Atlantic database and `ep`, `cp`, or `pac` for the East/Central Pacific)*

After a few seconds you'll be ready to dive into the data! Subsequent examples imply the use of the Atlantic Hurdat2.

[&#8679; back to Contents](#contents)

## Hurdat2 Object Structure

- The structure of a `Hurdat2` object is hierarchal. It has two primary dictionaries:
  - `<Hurdat2>.tc` - A dictionary containing all `TropicalCyclone` objects compiled from the record.
    - Individual storms can be accessed using their ATCF ID, a unique 8-character id for each tropical cyclone <u>OR</u> a name of a storm.
	  - `atl["AL200512"]` - Call for Hurricane Katrina's Data using its ATCFID (it being the 12th storm from the 2005 Atlantic Season).
	  - `atl["Name"]` - Use this if you know the name, but the year is unknown. A partial search is okay, but may receive less accurate results. It uses the `difflib` package to calculate close matches and outputs a list (if applicable) that you then can select from.
  - `<Hurdat2>.season` - A dictionary holding `Season` objects (yearly data).
    - A Season's data is accessed via a simple year key of type `int`.
	  - `atl[1995]` retrieves the object associated with the 1995 hurricane season.
- `Season` objects also have a dictionary (`<Season>.tc`) that holds `TropicalCyclone` objects, specific to the year.
  - There are 4 different ways to access individual storm data:
    1. `atl[1995]["Opal"]` - Storm Name; Useful if you know the name a storm was issued and the season in which it occurred.
    2. `atl[1992]["A"]` - Storm Name first-letter; I'm not saying you'd forget a named-storm like Hurricane Andrew, but this capability would grab the storm whose first-letter matched the one passed. This primarily works for modern storms (since the beginning of the satellite era), as most in the past were not named. In the HURDAT2 record, storms that were never issued a name are given "UNNAMED" for that field.
    3. TC Number: `atl[1988][8]` - Use the storm number (type `int`) from the season. This is defined by using the ATCF ID.
    4. ATCF ID: `atl[1980]["AL041980"]` - This isn't recommended because of redundancy (it can be done without the initial call to the `1980` object).
- `TropicalCyclone` objects contain a `list` of `TCRecordEntry` objects in time-ascending order.
  - Though the user probably wouldn't have general/typical need to access `TCRecordEntry`-level data, it can be done via the desired index from the `<TropicalCyclone>.entry` list: `atl[2004]["ivan"][0]` - This would grab the first entry associated with the track of Hurricane Ivan.

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
`rank_seasons_thru(...)` | Print a ranking of seasons where you can use part of the season; a way to rank attributes up to or between certain dates. A special positional keyword argument `thru=[12, 31]`, a tuple that represents the end month and day (ex. \[9, 6\] for September 6), must be passed. An <u>optional</u> keyword argument `start` can be included as well. If both are excluded from the call, by default this just becomes a wrapper for the above method. | `atl.rank_seasons_thru(10,"TSreach",[9,15],1967)`
`rank_climo(...)` | Yet another useful ranking method. This allows one to rank attributes assessed over several to many years (climatological periods) to one another. Optional keyword argument `climatology` (default is 30 years) controls the span of time that data is collected and `increment` (default is 5 years) dictates the temporal distance between periods | `atl.rank_climo(20,"track_distance_TC", climatology=10, increment=1)`
`rank_storms(...)` | Print a report that compares storms and their attributes to each other. Similar to the above methods, other data is included in the report. | `atl.rank_storms(20,"HDP",1967)`
`multi_season_info(...)` | Prints a report a gathered statistics based on a range of years. This is similar to the `info()` methods referenced in the next section. This could be thought of as an info method for a climatological period | `atl.multi_season_info(1991, 2000)`<br />`atl[2010, 2019]`
`storm_name_search(...)` | Search through the entire HURDAT2 record for storms issued a name. If the positional keyword `info` is `True`, the matching storm's info method will print. | `atl.storm_name_search("Hugo")`
`output_climo(...)` | outputs a .csv file using the `csv` package of 1-year incremented climatological periods. This csv file can then be opened in a spreadsheet program. To compare or rank, the spreadsheet GUI layout is much easier to use especially due to instant sorting and filtering. This accepts a positional keyword argument (`climatology=30`). | `atl.output_climo(15)`
`output_seasons_csv(...)` | Similar to the above, but for seasons. It takes no arguments. In other words, it would be redundant to run it multiple times, because as the `hurdat2parser` package doesn't natively allow modification of the data, it would just output the same data over and over. The only exception would be when the HURDAT2 database is updated by the NHC. With this in mind, it will automatically write-over the csv if it already exists (file-name is auto-generated within the method). | `atl.output_seasons_csv()`
`output_storms_csv(...)` | Similar to above, but for individual storms. | `atl.output_storms_csv()`
`coord_contains(...)` | Takes 3 tupled lat-lon coordinates. The purpose is to inquire whether the first arg (the test coordinate) is contained within a bounding box formed by the other two coordinates passed (returns a `bool`. This is generally just accessed via the ranking methods | `atl.coord_contains(`<br />&nbsp;&nbsp;&nbsp;&nbsp;`[30.4,-85.0]`,<br />&nbsp;&nbsp;&nbsp;&nbsp;`[31.5, 86.0],`<br />&nbsp;&nbsp;&nbsp;&nbsp;`[29.0, 84.0]`<br />`) -> True`
`record_range()` | Returns a tuple of the beginning year and end year of the HURDAT2 record | `atl.record_range() -> (1851, 2019)`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### Shared Methods and Attributes for `Season` and `TropicalCyclone`

Attributes | Description | Examples
:---: | :---: | :---:
`output_shp()` | Generate a GIS-compatible Shapefile using the `shapefile` package | `atl[1988]["Gilbert"].output_shp()`
`output_geojson()` | Generate a GIS-compatible and text-readable `.geojson` file via the `geojson` package; can also be used in GIS applications | `atl[2000].output_geojson()`
`info()` | Prints basic stats | `atl[2005].info()`
`summary()` | Prints detailed statistics for the season or life of the TC | `atl[2019]["dorian"].summary()`
`landfalls`<br /> | \*SEE [DISCLAIMER FOR LANDFALL INFO](#landfall-data)\* Sum of all landfalls (remember, a storm can make multiple landfalls). `<Season>.landfalls` is also an unfiltered aggregate of its storms landfalls. At the seasonal level, you'd probably be more interested in the attribute `landfall_TC` (see following section) | `atl[1960]["doNnA"].landfalls`
`landfall_<STATUS>`<br />*\-can be TC, TD, TS, HU, or MHU* | `Season`: qty of TC's that made landfall as the inquired status; `TropicalCyclone`: `bool` indicating if the storm made landfall while the inquired status<br />*\-CAUTION: These attrs are exclusive of landfalls made while of stronger designation\-* | `atl[1996].landfall_TS -> 2`<br />`atl[2011]["I"].landfall_HU -> True`
`<STATUS>reach`<br />*\-can be TC, TD, TS, HU, or MHU* | `Season`: qty of TC's that reached <u>at least</u> the inquired status; `TropicalCyclone`: `bool` indicating if the storm ever was designated as the inquired status | `atl[2010].HUreach -> 12`<br />`atl[1991]["danny"].HUreach -> False`
`ACE`, `HDP`, or `MHDP` | Returns the specified Energy Index reading associated with the season or storm. Note that the MHDP is one you likely won't see elsewhere. It's formula is the same as ACE and HDP but for major-hurricanes only | `atl[1966].HDP`
`track_distance` | The calculated distance (in nmi) for the entire track of the storm (or aggregate of the season), regardless of status | `atl[1954]["hazel"].track_distance`
`track_distance_<STATUS>`<br>*\-can be TC, TD, TS, HU, or MHU* | The distance traversed while storm(s) was(were) <u>at least</u> the status designation | `atl[1961].track_distance_MHU`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### `Season` Only Methods and Attributes
Attribute | Description | Example
:---: | :---: | :---:
`output_shp_segmented()` | Generates a shapefile including each segment from each tropical-cyclone from a given season; each individual segment from each individual storm will be represented | `atl[1932].output_shp_segmented()`
`output_geojson_segmented()` | Generates a geojson including each segment from each tropical-cyclone from a given season; each individual segment from each individual storm will be representeds | `atl[2003].output_geojson_segmented()`
`tracks` | Returns the quantity of tropical cyclones from a season | `atl[1995].tracks`
`<STATUS>only`<br />*\-can be TD, TS, or HU* | Returns the quantity of TC's from a season that made were given the inquired designation, but never strengthened beyond it. `HUonly` implies Category 1 and 2 storms only. To inquire about `MHU`, use the `MHUreach` attr | `atl[1950].TDonly`<br />`atl[2017].HUonly`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### `TropicalCyclone` Only Methods and Attributes
| Attribute | Description | Example
:---: | :---: | :---:
`coord_list()` | Prints a report with entry dates and the associated Latitude and Longitude | `atl[2005]["rita"].coord_list()`
`gps` | Returns a `list` of tupled latitude and Longitude coordinates | `atl[1998]["MITCH"].coord_list()`
`minmslp` | Returns the lowest recorded pressure of the TC | `atl[1955][10].minmslp`
`<EI>_per_nmi`<br />*\-can be ACE, HDP, or MHDP* | Returns the inquired energy index divided by the track distance covered while the energy index was being contributed to (`ACE` &rarr; `track_distance_TS` or `HDP` &rarr; `track_distance_HU` as examples). WARNING! These attributes do not have any kind of threshold controls, so storms which were short-lived can have high values | `atl[1964][10].HDP_per_nmi`<br />`atl[2016]["matthew"].ACE_per_nmi`
`<EI>_perc_ACE` &rarr; *\-can be HDP or MHDP*<br />`HDP_perc_MHDP` | Simply the storm's HDP or MHDP divided by ACE or the MHDP divided by the HDP. Look at this as the <u>percentage</u> (as a float between 0 and 1) of the storm's ACE or HDP that was contributed to while a Hurricane or Major Hurricane, respectively | `atl[2017]["IRMA"].HDP_perc_ACE`
`track_<EI1>_perc_<EI2>`<br />*\-&lt;EI1&gt; can be TS, HU, or MHU*<br />*\-&lt;EI2&gt; can be TC, TS, HU, or MHU* | Returns the the storm's &lt;EI2&gt; track_distance divided by the track distance while of status &lt;EI1&gt;. &lt;EI1&gt; must be of higher hierarchal status than &lt;EI2&gt; | `atl[2005][25].track_HU_perc_TC`<br />`atl[2003]["Fabian"].track_MHU_perc_TS`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### `TCRecordEntry` Attributes

- As mentioned earlier, there's generally no need to access`TCRecordEntry` objects directly. Only the most-common attributes will be referenced in this document. A comprehensive list is available via `help`

| Attribute | Description
:---: | :---:
`entrytime` | A `datetime.datetime` object of the entry's timestamp
`status` | The designated 2-letter abbreviation representing the storm's status
`location`<br />`location_rev` | A tuple of the latitude/longitude coordinates; `location_rev` is reversed in order, a longitude/latitude tuple; seemingly favored for GIS use.
`wind` | The maximum-sustained winds at the time of entry-recording
`mslp` | The Mean Sea-Level Pressure (in hPa or mb) at the time of entry-recording
`dump_hurdat2()` | Returns a reassembled Hurdat2-formatted string, identical to the one parsed to create the entry

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)<br />
[&#8679; back to Contents](#contents)

## Landfall Data

An important point to keep in mind when viewing data and ranking, HURDAT2's landfall data is incomplete. It is progressively being updated in conjunction with the yearly release of the dataset. Please see the documentation  [HURDAT2 Format Guide](https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-nov2019.pdf) for more detail on currently-available landfall data temporal scope.

[&#8679; back to Contents](#contents)

## Roadmap

- [ ] Inclusion of `matplotlib` methods
- [ ] View track methods
- [ ] POSSIBLY will include ranking in info methods

[&#8679; back to Contents](#contents)

## Credits

- [Haversine Formula (via Wikipedia)](https://en.wikipedia.org/wiki/Haversine_formula)
- Bell, et. al. Climate Assessment for 1999. *Bulletin of the American Meteorological Society.* Vol 81, No. 6. June 2000. S19.
- <span>G. Bell, M. Chelliah.</span> *Journal of Climate.* Vol. 19, Issue 4. pg 593. 15 February 2006.
- [HURDAT2 Format Guide](https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-nov2019.pdf)

[&#8679; back to Contents](#contents)

## Copyright

**Author**: Kyle S. Gentry<br />
Copyright &copy; 2019-2021, Kyle Gentry (KyleSGentry@outlook.com)<br />
**License**: MIT<br />
**GitHub**: [https://github.com/ksgwxfan/hurdat2parser](https://github.com/ksgwxfan/hurdat2parser)<br />
**Author's Webpages**:
 - [https://ksgwxfan.github.io/](https://ksgwxfan.github.io/)<br />
 - [http://echotops.blogspot.com/](http://echotops.blogspot.com/)

[&#8679; back to Contents](#contents)












