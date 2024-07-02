# hurdat2parser -- v2.3.0.1

### *Interpreting the Hurdat2 Tropical Cyclone Dataset using Python*

Hurdat2 ([https://www.nhc.noaa.gov/data/#hurdat](https://www.nhc.noaa.gov/data/#hurdat)) is a text file containing extensive time-stamped data from individual Tropical Cyclones. The two primary Hurdat2 records are for the Atlantic (since 1850) and East/Central-Pacific Oceans (since 1949).

The purpose of this module is to provide a quick way to analyze the Hurdat2 datasets. It includes methods for retrieving, inspecting, ranking, or even exporting data for seasons, individual storms, or climatological eras.

PyPI Link: [https://pypi.org/project/hurdat2parser/](https://pypi.org/project/hurdat2parser/)

## Contents
* [Changes/Fixes in this Version (2.3 and 2.3.0.1)](#changes-in-this-version-23-and-2301)
* [Requirements, Installation, and getting the data](#installation)
* [Importing the module](#importing-the-module)
* [Hurdat2 Object Structure](#hurdat2-object-structure)
* [Example Calls](#example-calls)
* [Methods &amp; Attributes](#methods-and-attributes)
  * [`Hurdat2` Methods &amp; Attributes](#hurdat2-methods-and-attributes)
  * [`Season` and `TropicalCyclone` Shared Methods &amp; Attributes](#shared-methods-and-attributes-for-season-and-tropicalcyclone)
  * [`Season`-only Methods &amp; Attributes](#season-only-methods-and-attributes)
  * [`TropicalCyclone`-only Methods &amp; Attributes](#tropicalcyclone-only-methods-and-attributes)
  * [`TCRecordEntry` Attributes](#tcrecordentry-attributes)
* [Note on Landfall Data](#landfall-data)
* [How to Use crosses()](#how-to-use-crosses)
  * [Included Coastlines with this Module](#included-coastlines-with-this-module)
* [Note on Ranking Methods](#note-on-ranking-methods)
* [Future/Under-Development/Unreleased Methods](#access-to-future-methods)
* [Roadmap](#roadmap)
* [Credits](#credits)
* [Copyright/License](#copyright)

## Changes in this Version (2.3 and 2.3.0.1)
- for `v2.3.0.1`
  - in `from_map()`, I ordered returned data to be in python's `float` form rather than of type `numpy.float64` (probably from a newer version of mpl that I didn't have installed while developing).
  - removed a `__main__.py` file that I use only for development/testing purposes.
- `Hurdat2` tweaks
  - online retrieval now attempts to download to a local file.
    - IMPORTANT! Versions `< 2.3` are not guaranteed to see the newest hurdat2 releases due to url-name structure change and too-strict regex code (my fault).
  - Call/Retrieval improvements
    - Attribute-like access to individual cyclones
	  - named cyclones (ex: `atl.hugo`, `atl.rita`, etc).
	    - This will return the most recent cyclone assigned a particular name. This guarantees that most-notorious cyclones with retired names will be returned
	  - Assigned ATCFID's (a basin prefix, cyclone number, and the season) ... (ex: `atl.al171995` or `atl.AL171995`)
	- recognizance of interchangeable order of season and cyclone number (`atl[1995,17]` or `atl[17,1995]` return the same `TropicalCyclone`. In addition, ATCF-ids without the basin prefix are recognized (`atl[171995]` or `atl[199517]`)
  - added `random()` method that returns a random `TropicalCyclone` object.
  - uniform `rank_seasons()` that allows part-season ranking
    - added `method` keyword that allows one to choose the desired ranking method. The options are `D` for dense rankings (default) (1,2,2,3) or `C` for competition-based ranking (1,2,2,4).
	- deprecated `rank_seasons_thru()` method.
  - uniform `_season_stats` handler/wrapper method that supports printing to console or as `str`.
    - deprecated `_season_stats_str` method
  - added `from_map` method that uses `matplotlib` to draw polylines, returning them as tupled coordinates.
    - added coastline coordinate constants
	  - Click [Here](#included-coastlines-with-this-module) for a list of included coastlines.
    - the purpose for these are to be used with the `<TropicalCyclone>.crosses` method (also new this version).
- `Season` tweaks
  - updated `stats()` method to now report densely-based <u>and</u> competition-based rankings.
- `TropicalCyclone` tweaks
  - added vector info and saffir-simpson ratings to `.summary()`
  - added `crosses` method that allows comparing a system's track to a coordinate list to see if it crossed the path. Click [Here](#how-to-use-crosses) for a guide on how to use.
  - removed/changed verbiage where I erroneously had indicated 50kt winds as "gale force".
  - `.info()` temporal data are now status-based
  - `track_map()` tweaks and improvements
    - legend is no longer draggable by default. See keyword below
    - removed auto-resizing that inadvertently required `tkinter` in previous versions.
    - tweaked placement of NaturalEarth accreditation
    - added keyboard shortcuts for Zooming (`SHIFT` &plus; arrows) and Panning (`CTRL` &plus; arrows) and toggle of legend (`N`)
	- temporal labels no longer inadvertently alter the size of the Axes when panning.
	- added some interaction. Clicking on a segment will reveal some basic `TCRecordEntry` (segment) information in the lower left corner of the display (may be buggy. Try toggling the maximize screen option and see if it appears).
    - default behavior more-so mimics the `matplotlib` (mpl) defaults
	- small visual improvements including default map extent, sub-tropical cyclone discrimination on map and legend, and bolder tracks for major hurricanes, and Natural Earth map citation
	- higher resolution maps
	- new supported keywords
	  - removed `aspect_ratio` kw
	  - added `width`, `height`; these are used in the figsize keyword when creating the figure.
	  - added `dpi`, and `block`. These mimic their `mpl` counterparts
	  - added `draggable` kw that indicates if the displayed legend should be able to be interacted with.
	  - added `extents` kw that can show generalized quadrant-based TS, 50kt, and Hurricane force wind extents. As of the most recent hurdat2 release, this is only available for cyclones `>=` 2004.
	  - added `padding` kw to allow modification of the default focal scope on the track itself. The higher this number, the more "zoomed-out" it will appear.
	  - added `saveonly` kw that saves an image locally instead of showing the plot on screen. This also respects the aforementioned `width`, `height`, and `dpi` kw's
	  - added `backend` to allow the user to dictate which mpl backend to use
- `TCRecordEntry` tweaks
  - formalized `entrytime`s as UTC/Zulu timezone (won't change calculated stats any)
  - added `category` property as an alias for `saffir_simpson`
- made small tweaks to Saffir-simpson scale to reflect data from [](http://nhc.noaa.gov/aboutsshws.php). Some of the scale I had was off by one or two knots. As reported data is rounded to the nearest 20th (0, 5, 10, 15, 20, etc), the tweaks are inconsequential.
- added `gis` keyword to `_calculations.haversine`. This allows the use of coordinates in (lon, lat) format (`True`; common in GIS programs) or (lat, lon) (`False`; default). In future releases, I may go to the (lon, lat) format as default and uniform throughout.
- `hurdat2()` methods made uniform by returning a string. You can optionally use the original line from the database instead of the default of objectively-formed wind-extent data.
- inclusion of `BoundingBox` and `Coordinate` classes in `_gis` module. These are what enable functionality to the `from_map` and `crosses` methods.

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

### Different ways to ingest data

There are a few different ways to load hurdat2 formatted files. These approaches can be mixed/matched too.

#### Local / Offline

If you want a local copy of a hurdat2file, got to [https://www.nhc.noaa.gov/data/#hurdat](https://www.nhc.noaa.gov/data/#hurdat) to download. It's a text file. Hurdat2 files for the Atlantic Basin and East/Central Pacific Basins are available and compatible with the package. They are updated every year around the start of a new Hurricane Season. Hotfix updates can be released occasionally if there are typos/errors etc. found.

To read-in a local file:<br/>`>>> atl = hurdat2parser.Hurdat2("path_to_hurdat2.txt")`

#### Online Retrieval

As of `v2.2`, datasets can be retrieved from online. As of `v2.3`, an attempt is made to save a copy locally.

The downside is versions prior to `v2.3` won't be able to see the newest hurdat2 releases. So going forward, `v2.3+` will be needed if using this feature. Otherwise, just follow instructions in the prior section to download and ingest a local copy. No biggie since, generally-speaking, the databases are updated once per year.

- North Atlantic Basin<br/>`>>> atl = hurdat2parser.Hurdat2(basin="atl")`
  - Any of the following will be recognized: `"al"`, `"atl"`, or `"atlantic"`
- NE/CEN Pacific Basin<br/>`>>> pac = hurdat2parser.Hurdat2(basin="pac")`
  - Any of the following will be recognized: `"pac"`, `"nepac"`, or `"pacific"`

#### Alternate URL (experimental)

If you are aware of a frequently updated dataset in Hurdat2 format, you can pass a URL and set the kwarg `urlcheck` to `True` and retrieval will be tried<br/>
`>>> atl = hurdat2parser.Hurdat2("http://crazygonuts.aboutweatherstuff/myhurdat2file.txt", urlcheck=True)`

If you want you could combine it with a local file also:

```python
# Atlantic
>>> atl = hurdat2parser.Hurdat2("local_atl_hurdat2_filename.txt", "https://weblink/to/otherhurdat2file.txt", urlcheck=True)
```

### Readable Object Names

* For the `Hurdat2` object, I highly recommend to use something shortened and readable for the parent object name (like `atl` or `al` for the Atlantic database and `ep`, `cp`, or `pac` for the East/Central Pacific)*

After a few seconds (a little longer if downloading) you'll be ready to dive into the data! Subsequent examples imply the use of the Atlantic Hurdat2 (`atl`).

[&#8679; back to Contents](#contents)

## Hurdat2 Object Structure

- The structure of a `Hurdat2` object is hierarchal. It has two primary dictionaries:
  - `<Hurdat2>.tc` - A dictionary containing all `TropicalCyclone` objects compiled from the record.
  - `<Hurdat2>.season` - A dictionary holding `Season` objects (yearly data).
    - A Season's data is accessed via a simple year key of type `int`.
	  - `atl[1995]` retrieves the object associated with the 1995 hurricane season.
- `Season` objects are a container for cyclones occurring in that particular year.
  - `<Season>.tc` - mirroring its above counterpart, it is a dictionary that holds `TropicalCyclone`s, keyed by their atcfid., specific to the year. Some different ways to call these objects:
- `TropicalCyclone` objects represent an individual cyclone in the Hurdat2 record.
  - `<TropicalCyclone>.entry` is a list containing temporal and, in some cases, event-based records
    - The members of the list are `TCRecordEntry`s
- `TCRecordEntry`s represent a cyclone's data recorded at a specific time.
  - These are what holds the actual data from the Hurdat2.
  - Though the "lowest" class in the heirarchy, a large majority of attributes for `TropicalCyclone`s and therefor `Season`s depend on this class and are calculated and derived from these individual storm entries.

## Example calls

Read-on to see several ways to invoke a call to a `Season` or `TropicalCyclone` objects. You'll also find these type of references throughout the document and even a large portion of docstrings.

- `Season` objects (just the year)
  - `atl[1995]`
- `TropicalCyclone` objects
  - by ATCFID
    - attribute-like access:
	  - `atl.al171995`
	- ATCF number and season tuple (treated as dictionary keys)
      - `atl[12,2005]` or `atl[2005,12]`
    - leaving out the comma is ok too (just like in ACTFID's):
	  - `atl[122005]` or `atl[200512]`
	- Storm starting letter (or name):
	  - `atl[1995, "o"]` - This method works for most modern tropical storms, as they have been issued names. So in these cases, you wouldn't need to know the atcfid number. Also of note, because tropical depressions aren't issued names, the id numbers do not always correlate with the co-inciding letter of the alphabet. For example, Hurricane Andrew's ATCFID is `AL041992`.
  - by Name
    - `atl.rita` or `atl["_rita"]`, or `atl["-rita"]` -- Attribute-like access or beginning the name with an underscore or dash shows the most-recent storm named as such (this returns the most-notorious storms as well since storm names can be retired according to the destruction they cause).
    - `atl["danny"]` -- shows a list of storms in the record given the name of Danny (or something similar), allowing the user to select which one they desire
- `TCRecordEntry` calls
  - Example for the entry at index 29 (30th total entry) for Hurricane Allen
    - `atl[1980,4,29]` or `atl.allen[29]`

Other examples of calls of interest

- Iterate through all cyclones
  - `>>> for tc in atl.tc.values():`
  - list comprehension form example grouping all Category 3+ cyclones:
    - `[tc for tc in atl.tc.values() if tc.maxwind >= 96]`
  - all category 3+ cyclones occuring since 1967 that experienced a minimum MSLP of <= 910hPa
	- `[tc for tc in atl.tc.values() if tc.year >= 1967 and tc.maxwind >= 96 and tc.minmslp <= 910]`
  - all cyclones which made a landfall as a Hurricane along the US Gulf Coast during October or later, since 1967
    - `[tc for tc in atl.tc.values() if tc.year >= 1967 and tc.start_date.month >= 10 and tc.crosses(atl.us_gulf_coast, landfall=True, category=1, is_TC=True)]`
- Multi-Season Statistical Report (can also be used to get a climatology)
  - `atl.multi_season_info(1991, 2020)` or `atl[1991:2021]`.
    - if you use a `slice`, be aware it will behave like a `list`, and the end will be decremented by 1. 

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
`from_map()` | Displays an interactive map where the user can plot a polyline of geographic coordinates. When completed, the list of `lon, lat` tupled coordinates are returned. This method was designed to supplement and ease the use of the `<TropicalCyclone>.crosses` method. See docstring for keywords<br /><br />Use keyboard shortcuts to move around:<br/>Zoom: `SHIFT` &plus; arrows<br />Pan: `CTRL` &plus; arrows<br />`L` toggles `landfall_assist` arrows. If using `landfall=True` in the aforementioned `crosses()` method, the arrows will show you the general direction that a cyclone's path must cross the segment from to be guaranteed as a "landfall". | `atl.from_map()`
`multi_season_info(...)` | Prints a report a gathered statistics based on a range of years. This is similar to the `info()` methods referenced in the next section. This could be thought of as an info method for a climatological period | `atl.multi_season_info(1991, 2000)`<br />`atl[2010, 2019]`
`storm_name_search(...)` | Search through the entire Hurdat2 record for storms issued a name. If the positional keyword `info` is `True`, the matching storm's info method will print. | `atl.storm_name_search("Hugo")`
`output_climo(...)` | outputs a .csv file using the `csv` package of 1-year incremented climatological periods. This csv file can then be opened in a spreadsheet program. To compare or rank, the spreadsheet GUI layout is much easier to use especially due to instant sorting and filtering. This accepts a positional keyword argument (`climatology=30`). | `atl.output_climo(15)`
`output_seasons_csv(...)` | Similar to the above, but for seasons. It takes no arguments. In other words, it would be redundant to run it multiple times, because as the `hurdat2parser` package doesn't natively allow modification of the data, it would just output the same data over and over. The only exception would be when the Hurdat2 database is updated by the NHC. With this in mind, it will automatically write-over the csv if it already exists (file-name is auto-generated within the method). | `atl.output_seasons_csv()`
`output_storms_csv(...)` | Similar to above, but for individual storms. | `atl.output_storms_csv()`
`random()` | Returns a random `TropicalCyclone` object | `atl.random()`
`climograph()` | displays a graph of the climatological tendency of a variable over multiple seasons (see docstring for a how-to) | `atl.climograph("ACE", 10, 1, year1=1967)`
`coord_contains(...)` | Takes 3 tupled lat-lon coordinates. The purpose is to inquire whether the first arg (the test coordinate) is contained within a bounding box formed by the other two coordinates passed (returns a `bool`. This is generally just accessed via the ranking methods | `atl.coord_contains(`<br />&nbsp;&nbsp;&nbsp;&nbsp;`[30.4,-85.0]`,<br />&nbsp;&nbsp;&nbsp;&nbsp;`[31.5, 86.0],`<br />&nbsp;&nbsp;&nbsp;&nbsp;`[29.0, 84.0]`<br />`) -> True`
`BASIN_DICT` | A dictionary containing abbreviations (keys) and definitions (values) of various basins around the world that hurricane data is kept. This is referenced via the `basin()` method. The data used to form this object came from IBTrACS | `atl.BASIN_DICT`
`basin(season=None)` | Interprets and returns a readable string identifying the TC basin based on the storms within the record. This allows support of dynamically-created singular OR multiple Hurdat2 datasets OR individual seasons (if a `Season` object is passed to the method). The data used to form this property came from IBTrACS | `atl.basin() -> "North Atlantic Basin"
`record_range` | Returns a tuple of the beginning year and end year of the Hurdat2 record | `atl.record_range -> (1851, 2020)`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### Shared Methods and Attributes for `Season` and `TropicalCyclone`

Attributes | Description | Examples
:---: | :---: | :---:
`ACE`, `HDP`, or `MHDP`<br />`ace`, `hdp`, or `mhdp` | Returns the specified Energy Index reading associated with the season or storm. The formula is very similar to ACE and HDP but for major hurricanes | `atl[1966].HDP`<br />`atl.ivan.MHDP`
`cat45reach`<br>`cat5reach` | For `Season` objects, returns the quantity of storms that reached category 4+ status or category 5 status (respectively)<br>For `TropicalCyclone` objects, returns a `bool`, indicating if the TC ever achieved cat 4+ or 5 status (respectively) | `atl[2020].cat45reach -> 5`<br>`atl[2020].cat5reach -> 0`<br>`atl[2020]["Iota"].cat5reach -> False`
`duration` | Returns the length of the Season or life of the cyclone (Of note, the `TropicalCyclone` property disregards storm status but there are additional status-based duration variables available for that) | `atl[2022].duration`
`end_date` | The ending date of the Season or storm | `atl[1954, 16].end_date`
`end_ordinal` | The quantified day of the year of the ending date of the Season or storm | `atl[1954].end_ordinal`
`hurdat2()` | This method returns stringified hurdat2-formatted output of the season or cyclone data. By default, the in-interpreter version (with objective wind-extent data) is used. But you can specify to use the original. | `atl[2005].hurdat2()`
`landfall_<STATUS>`<br />*\-can be TC, TD, TS, HU, or MHU* | `Season`: qty of TC's that made landfall as the inquired status; `TropicalCyclone`: `bool` indicating if the storm made landfall while the inquired status<br />*\-CAUTION: These attrs are exclusive of landfalls made while of stronger designation\-* | `atl[1996].landfall_TS -> 2`<br />`atl[2011]["I"].landfall_HU -> True`
`landfalls`<br /> | \*SEE [DISCLAIMER FOR LANDFALL INFO](#landfall-data)\* Sum of all landfalls (remember, a storm can make multiple landfalls). `<Season>.landfalls` is also an unfiltered aggregate of its storms landfalls. At the seasonal level, you'd probably be more interested in the attribute `landfall_TC` (see following section) | `atl[1960]["doNnA"].landfalls`
`output_shp()` | Generate a GIS-compatible Shapefile using the `shapefile` package | `atl[1988]["Gilbert"].output_shp()`
`output_geojson()` | Generate a GIS-compatible and text-readable `.geojson` file via the `geojson` package; can also be used in GIS applications | `atl[2000].output_geojson()`
`start_date_entry`<br />`genesis_entry` | The`TCRecordEntry` when the season or cyclone began | `atl[1938].start_date`
`start_date`<br />`genesis` | The moment when the season's first tropical cyclone designation occurred or moment the `TropicalCyclone` became a TC | `atl[1938].start_date`
`start_ordinal` | The quantified day of the year of the beginning moment of the Season or storm | `atl[1938].start_ordinal`
`stats()` | This method will display typically-sought-for stats. For `Season`s, it will also report respective ranks compared to all, or a subset of, other seasons. Please run `help` on a season stats method to get an in-depth overview of keywords<br /> For `TropicalCyclone`s, it is just a wrapper for the `.info()` method | `atl[2020].stats(1967)`<br />`atl.hugo.stats()`
`summary()` | Prints detailed statistics for the season or life of the TC | `atl[2019]["dorian"].summary()`
`tc_entries` | Returns a list of `TCRecordEntry`'s from where a storm was designated as a tropical cyclone | `atl["_katrina"].tc_entries`
`track_distance_<STATUS>`<br>*\-can be TC, TD, TS, HU, or MHU* | The distance traversed while storm(s) was(were) <u>at least</u> the status designation | `atl[1961].track_distance_MHU`
`track_distance` | The calculated distance (in nmi) for the entire track of the storm (or aggregate of the season), regardless of status | `atl[1954]["hazel"].track_distance`
`<STATUS>reach`<br />*\-can be TS, HU, or MHU* | `Season`: qty of TC's that reached <u>at least</u> the inquired status; `TropicalCyclone`: `bool` indicating if the storm ever was designated as the inquired status | `atl[2010].HUreach -> 12`<br />`atl[1991]["danny"].HUreach -> False`
`year` | Simply the year of the `Season` or `TropicalCyclone` | ...

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### `Season` Only Methods and Attributes
Attribute | Description | Example
:---: | :---: | :---:
`output_shp_segmented()` | Generates a shapefile including each segment from each tropical-cyclone from a given season; each individual segment from each individual storm will be represented | `atl[1932].output_shp_segmented()`
`output_geojson_segmented()` | Generates a geojson including each segment from each tropical-cyclone from a given season; each individual segment from each individual storm will be representeds | `atl[2003].output_geojson_segmented()`
`<STATUS>only`<br />*\-can be TD, TS, or HU* | Returns the quantity of TC's from a season that made were given the inquired designation, but never strengthened beyond it. `HUonly` implies Category 1 and 2 storms only. To inquire about `MHU`, use the `MHUreach` attr | `atl[1950].TDonly`<br />`atl[2017].HUonly`
`tracks` | Returns the quantity of tropical cyclones from a season | `atl[1995].tracks`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### `TropicalCyclone` Only Methods and Attributes
| Attribute | Description | Example
:---: | :---: | :---:
`ACE_no_landfall` | Returns the ACE of the storm prior to any landfall made | `atl["_ivan"].ACE_no_landfall
`<EI>_per_nmi`<br />*\-can be ACE, HDP, or MHDP* | Returns the inquired energy index divided by the track distance covered while the energy index was being contributed to (`ACE` &rarr; `track_distance_TS` or `HDP` &rarr; `track_distance_HU` as examples). WARNING! These attributes do not have any kind of threshold controls, so storms which were short-lived can have high values | `atl[1964][10].HDP_per_nmi`<br />`atl[2016]["matthew"].ACE_per_nmi`
`atcf_num`<br />`storm_number` | The number part of the TC's ATCFID; does not necessarily coincide with the order of occurrence. | ...
`atcfid` | The issued id consisting of the Basin code, unique zero-padded integer, and season (year) when it occurred | ...
`bounding_box`<br />`bounding_box_<STATUS>` | A `BoundingBox` instance comprising of the maximum/minimum lat/lon extents of the cyclone.<br /><br />With no status suffix, it considers the entire track.<br /><br />With a status suffix, it only considers points where the cyclone had acquired that particular status or greater  | `atl.faith.bounding_box`<br />`atl[3,1896].bounding_box`
`crosses()` | Takes a list of coordinates (think polyline) and compares the track of the system to a polyline formed by the coordinates and determines if the track crossed it. One can optionally specify a range of direction that the cyclone is traversing if a crossing is True. Landfalls can also be detected by formulating the polyline. This feature tests if crossing occurs from the same direction as a landfall would occur. | &star; See [How to Use crosses()](#how-to-use-crosses) for an example.
`duration_<SUFFIX>`<br />*\*&lt;SUFFIX&gt; can be TC, TS, HU, MHU* | Returns the aggregated length in days that the cyclone spent as on of the given statuses. These do account for storm status loss and possible reaquisition | `atl["_irma"].duration_MHU`
`entry` | list of `TCRecordEntry`'s of the storm | ...
`gps` | Returns a `list` of tupled latitude and Longitude coordinates | `atl[1998]["MITCH"].gps`
`<EI>_perc_ACE` &rarr; *\-can be HDP or MHDP*<br />`MHDP_perc_HDP` | Simply the storm's HDP or MHDP divided by ACE or the MHDP divided by the HDP. Look at this as the <u>percentage</u> (as a float between 0 and 1) of the storm's ACE or HDP that was contributed to while a Hurricane or Major Hurricane, respectively | `atl[2017]["IRMA"].HDP_perc_ACE`
`info()` | Prints basic stats for the tropical cyclone | `atl[2005][12].info()`
`max_maxwind_radius`<br />`max_rmw` | The highest observed radius where maximum winds were observed. Remember that this value does not necessarily coincide with when the systems highest maximum winds were observed | `atl.ida.max_maxwind_radius`
`maxwind` | Returns the highest maximum sustained wind-speed observed in the tropical cyclone | `atl["_katrina"].maxwind`
`maxwind_mslp`<br>`minmslp_wind` | Returns the MSLP (wind) occurring at the time of peak-winds (minimum MSLP) respectively. These attributes were included because peak winds and minimum MSLP do not necessarily occur at the same time. | `atl[2015]["joaquin"].maxwind_mslp -> 934`<br>`atl[2015]["joaquin"].minmslp_wind -> 120`<br>\* This example was given as Joaquin's peak winds (135) were not observed at the time of Joaquin's minimum MSLP (931)
`minmslp` | Returns the lowest recorded pressure of the TC | `atl[1955][10].minmslp`
`name` | The name given to the cyclone if reaching Tropical Storm (inc. subtropical) or Hurricane status. Many qualifying cyclones were not issued names in the past. These simply have a name of "UNKNOWN" | ...
`perc_ACE`<br>`perc_HDP`<br>`perc_MHDP` | Return the percentage (in decimal form) of the contribution of the storm's ACE, HDP, or MHDP value to the season's value | `atl["_matthew"].perc_MHDP`
`status_highest` | Returns a formal description of the highest designated status acquired by the cyclone | `atl.sandy.status_highest`
`statuses_reached` | A list of cyclone statuses (as appearing in the hurdat2 record) issued to the cyclone during its life | ...
`track_map()` | Generates a map of the storm's track using `matplotlib`. Check the docstring for ways to modify the output to your liking. This method is compatible with `jupyter notbook`s. It is recommended to use `%matplotlib notebook` at the beginning of your notebook to preserve interactivity.<br />Use keyboard shortcuts to move around:<br/>Zoom: `SHIFT` &plus; arrows<br />Pan: `CTRL` &plus; arrows<br />`L` toggles the legend (things won't work right with this shortcut if using `block=False`) | `atl["_katrina"].track_map()`
`track_<EI1>_perc_<EI2>`<br />*\-&lt;EI1&gt; can be TS, HU, or MHU*<br />*\-&lt;EI2&gt; can be TC, TS, HU, or MHU* | Returns the the storm's &lt;EI2&gt; track_distance divided by the track distance while of status &lt;EI1&gt;. &lt;EI1&gt; must be of higher hierarchal status than &lt;EI2&gt; | `atl[2005][25].track_HU_perc_TC`<br />`atl[2003]["Fabian"].track_MHU_perc_TS`

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)

#### `TCRecordEntry` Attributes

- Only the most-common attributes will be referenced in this document. A comprehensive list is available via `help`

| Attribute | Description
:---: | :---:
`areal_extent_<SUFFIX>`<br/>Suffix can be `TS`, `TS50`, or `HU` | The calculated area covered by the extent of winds of specified strengths. This is just an addition of `pi * r^2` from all quadrants. Units are `nmi^2`.<br />Of note, wind extents are only available for storms since 2004. Also it's not guaranteed to be even a remotely-accurate figure because it's possible that data can be missing for quadrants while being present for others
`avg_wind_extent_<SUFFIX>`<br/>Suffix can be `TS`, `TS50`, or `HU` | The statistical mean of the reported wind-extents (quadrants). Wind extents are only available for storms since 2004 
`direction()` | Returns the heading in degrees that the storm is going. A readable cardinal direction can be returned if `True` is passed to the method
`entrytime` | A `datetime.datetime` object of the entry's timestamp. 
`extent_<STATUS>`<br />Status can be `TS`, `TS50` or `HU` | A list of the entry's respective tropical storm, 50kt, and hurricane NE, SE, SW, and NW wind extents
`hurdat2()` | Returns a reassembled Hurdat2-formatted string. If the keyword `original` is `True`, the returned string will be identical to the line from the actual record used.
`is_TC` | Returns `True` if the system is a designated tropical cyclone at the time of this entry
`lat` or `latitude`<br />`lon` or `longitude` | the lat/lon in `float` format
`lat_str`<br />`lon_str` | The lat/lon in `string` format, reflecting the hurdat2 output (ex. `80.6W`)
`location`<br />`location_rev` | A tuple of the latitude/longitude coordinates; `location_rev` is reversed in order, a longitude/latitude tuple; seemingly favored for GIS use.
`maxwind_radius`<br />`rmw` | The Radius of Maximum Winds. Currently, it is only available for storms since 2021, and is assumed that in subsequent releases, this variable will continue to be updated.<br /><br />Though unknown if this data for previous seasons will (or can) be back-filled, as of Feburary of 2024, select pre-2021 cyclones may have this data included.
`mslp` | The Mean Sea-Level Pressure (in hPa or mb) at the time of entry-recording
`previous_entry`<br/>`next_entry` | Returns the entry prior-to or after the `TCRecordEntry` that it is called from
`saffir_simpson`<br />`category` | The cyclone's Saffir-Simpson category, based soley on wind-strength.<br />Of note, the Saffir-Simpson Scale only goes from 1-5. But for consistency within the module, Tropical Storms will report `0` for this attribute while Depressions (and weaker) will report `-1`
`speed` | The average speed between the previous entry and this one in nm/h<br/>Of Note, remember that the `Hurdat2` spatial resolution is 0.1 degrees latitude/longitude. So some appreciable error may be present
`status` | The designated 2-letter abbreviation representing the storm's status (same format from hurdat2)
`track_distance`<br/>`track_distance_<SUFFIX>`<br/>Suffix can be `TC`, `TS`, `HU`, or `MHU` | returns the distance tracked by the system from its genesis to the point of the entry. The variables with suffixes do account for status in their calculations
`wind` | The maximum-sustained winds at the time of entry-recording

[&#8679; back to Methods &amp; Attributes](#methods-and-attributes)<br />
[&#8679; back to Contents](#contents)

## Landfall Data

An important point to keep in mind when viewing data and ranking, Hurdat2's landfall data is incomplete. It is progressively being updated in conjunction with the yearly release of the dataset. Please see the documentation  [Hurdat2 Format Guide](https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-atl-1851-2021.pdf) for more detail on currently-available landfall data temporal scope.

[&#8679; back to Contents](#contents)

## How to use `.crosses()`

The `crosses()` method of `TropicalCyclone` objects tests if an intersection occurs between the cyclone's track and a polyline formed from a coordinate list. For the following test case, Hurricane Hugo (`atl.hugo` or `atl[1989,11]`) will be used. [Click here for some pre-made coastlines available](#included-coastlines-with-this-module).

#### Formulate coordinate list

Using the convenient `from_map` method simplifies the creation of a custom polyline which can be immediately fed into the `<TropicalCyclone>.crosses` method.
```python
>>> c = atl.from_map()
```

We know that Hugo made landfall along the South Carolina coast. Draw a polyline that parallels the coastline (Hold down `Alt + Left-click` to add points; `Alt + Right-click` removes points). You should see some arrows. These are "landfall assistants" to help you draw the segments in a way that will return `True` if using with the `landfall=True` keyword in the `crosses` method.
- If testing for landfall or direction-dependent crossing, draw the polyline in a way where the arrows are pointing towards land or imaginary barrier

![from_map01.gif](https://ksgwxfan.github.io/unofficial_hurdat2/hd2-readme-images/from_map01.jpg)

When finished, press `Q`. The list of coordinates will be stored in the `c` variable. Go ahead and check it out:

```python
>>> c
[(-78.58, 33.865), (-78.954, 33.612), (-79.216, 33.191), (-79.816, 32.769), (-80.116, 32.582), (-80.378, 32.498), (-80.49, 32.348), (-80.865, 32.03)]
>>> _
```
It is a list of longitude, latitude tuples. Now we are ready to use the `crosses` method.

#### Run the crosses method on the `TropicalCyclone` of interest

To inquire if Hugo's track crossed the polyline, pass the coordinate list to the `crosses` method:
```python
>>> atl.hugo.crosses(c)
True
```

It is important to note, with no `landfall` keyword in the `crosses` call, it was going to return `True` regardless if you drew it North-to-South or South-to-North. Add the landfall keyword.

```python
>>> atl.hugo.crosses(c, landfall=True)
True
```

To show the difference that the keyword makes, draw the polyline again, but this time, draw from the GA border, north to the NC border. Notice how the arrows now point off-shore (below I simply cheated and reversed the polyline I had already made)

![from_map02.gif](https://ksgwxfan.github.io/unofficial_hurdat2/hd2-readme-images/from_map02.jpg)

Now run the above code again.

```python
>>> atl.hugo.crosses(reversed(c), landfall=True)
False
```

It returns `False` because the cyclone's track does not go from on-to-off shore, as indicated by the arrows.

If the arrows get in your way of making your line, feel free to pass `True` to the `from_map` method or simply toggle them off/on at any time by pressing `N`. They are more of a guide anyway.

The use of this method can be quite versatile. The general workflow when creating your own (or a pre-made list) goes like this:

- use `from_map` method to get a coordinate path or use a pre-made coast list (next section).
  - Do you care from what direction the crossing occurred (are you testing for landfall)?
- iterate through all cyclones and use the crosses method:

```python
>>> for tc in atl.tc.values():
        if tc.crosses(my_coordinates, landfall=True):
		    print(tc)
```

- or generate a list that you can reference:

```python
>>> cyclones = [tcyc for tcyc in atl.tc.values() if tcyc.crosses(my_coordinates, landfall=True)]
```

#### Included Coastlines with this Module

As a convenience, I included some polyline lists representing coastlines of interest intended to be used with the `crosses` method. They were prepared with the `landfall=True` of the `crosses` method in mind. These attributes belong to any `Hurdat2` object, regardless of basin. Of note, these are primarily traces of the respective mainland, excluding many small islands. These were prepared with maps from NaturalEarth being a guide.

Coastline | Attribute Name
:---: | :---:
Eastern US (Maine to South Florida)  | `us_east_coast`
US Gulf of Mexico border (South Florida to TX)  | `us_gulf_coast`
Western US | `us_west_coast`
Eastern Mexico | `mexico_east_coast`
Western Mexico | `mexico_west_coast`
Eastern Central America | `centam_east_coast`
Western Central America | `centam_west_coast`
Cuba | `cuba_coast`
Jamaica | `jamaica_coast`
Hispaniola (Haiti and DR) | `hispaniola_coast`
Puerto Rico | `puerto_rico_coast`
Bermuda | `bermuda_coast`

[&#8679; back to Contents](#contents)

## Note on Ranking Methods

In the methods `<Hurdat2>.rank_seasons` and `<Season>.stats`, ranks are displayed via different methods. In particular, the differences are based on how ties (same values) are communicated and treated.

#### Dense Rankings

Dense ranking numbers are strictly value-based. Seasons with the highest value have a rank of #1. Seasons with the 2nd highest value have a rank of #2, no matter how many seasons are tied for #1, and so forth. This is understood briefly as 1-2-2-3 rankings.

#### Competition Rankings

I loosely call these "golf rankings". Ranking numbers are based upon the quantity of seasons that have a higher value than a respective member (in this case, a Season). So a season may have a value that is the 3rd highest (dense ranking of #3), but could have competition rank of #20, implying that 19 seasons had a higher value than it. This is understood as 1-2-2-4 rankings.

Prior to `v2.3`, only dense rankings were reported. The inclusion of competition rankings gives context and more understanding to dense rankings. For more info on ranking types, click here: [Ranking Methods (via Wikipedia)](https://en.wikipedia.org/wiki/Ranking)

[&#8679; back to Contents](#contents)

## Access to Future Methods

In `_future.py`, I have some stuff that I've started to develop no where near ready to release. The methods are functional, but should be considered very unstable and perhaps even unreliable, as I don't maintain it much. The quickest way of accessing it is:

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

- `Hurdat2` object or general
  - [ ] `output_storms_csv` expansion that allows seasonal discrimination or inclusion of only requested cyclones
  - [ ] Speed up `rank_seasons` (or investigate it)
  - [ ] `multi_season_info()` revamp
  - [ ] add a `StormNameWrongFormat` error to track possible errors for storm name lines in database
  - [ ] Unify order of lon, lat throughout the program (like gis programs). But even in the hurdat2 database, it is presented as lat, lon
  - [ ] add maps files for Pacific storms that cross the international dateline (IDL) or occur on the other side of the IDL (beyond the current scope of available Hurdat2 data).
  - [ ] investigate inclusion of other data on NHC's ATCF ftp site.
  - [ ] `from_map` enable ability to alter polyline direction on the fly (just in case user realizes they were drawing in unpreferred direction
- `Season` objects
  - [ ] Track distance percentage of season total for `TropicalCyclone`s
  - [ ] Speed-up `<Season>.stats()` report if possible
  - [ ] `<Season>.track_map()` official inclusion (this is afar off; but I want to add a good one).
    - [ ] include a slider as a moveable timeline
  - [ ] Comparison methods to directly compare one season to another or specific storms to another.
  - [ ] `<Season>.[STATUS]_areal_extent(month1, day1, month2, day2)` - returns the aggregate wind-extent area for the span between m1, d1 and m2, d2
  - [ ] `quiet` methods that return tuples of temporal periods where cyclones (of certain status or not) did not occur
  - [ ] `.thru()` and/or `.from()` method that calculates and returns stats calculated between two times. Similar idea of `<Hurdat2>.rank_seasons` and `<Season>.stats` method, but direct return of a requested stat.
  - [ ] `accumulated_duration_<STATUS>` attr; aggregated time where a system of a particular status was experienced
    - [ ] include these in season summaries?
- `TropicalCyclone` objects
  - [ ] `track_map` addition of equatorial and tropic of cancer/capricorn latitudes
  - [ ] Formulate a `stats()` method for `TropicalCyclone`s (to eventually replace their `info` method); including ranking/comparing to storms across the record or a subset of seasons (right now, this method is just a wrapper for the `info()` method.
  - [ ] create a vector analysis map (twin axes; forward speed vs direction)
- [ ] consider removing `pyshp` and just go with geojson
- [X] Revamp `hurdat2()` method of `TropicalCyclone` and `Season` objects to optionally return a string instead of merely printing to console

[&#8679; back to Contents](#contents)

## Credits

- HURDAT Reference: `Landsea, C. W. and J. L. Franklin, 2013: Atlantic Hurricane Database Uncertainty and Presentation of a New Database Format. Mon. Wea. Rev., 141, 3576-3592.`
- [Haversine Formula (via Wikipedia)](https://en.wikipedia.org/wiki/Haversine_formula)
- Bell, et. al. Climate Assessment for 1999. *Bulletin of the American Meteorological Society.* Vol 81, No. 6. June 2000. S19.
- <span>G. Bell, M. Chelliah.</span> *Journal of Climate.* Vol. 19, Issue 4. pg 593. 15 February 2006.
- [Hurdat2 Format Guide (PDF)](https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-atl-1851-2021.pdf)
- [Natural Earth](https://www.naturalearthdata.com/) GIS Data (data extracted there-from to display maps)
- [Ranking Methods (via Wikipedia)](https://en.wikipedia.org/wiki/Ranking)

[&#8679; back to Contents](#contents)

## Copyright

**Title**: hurdat2parser<br />
**Author**: Kyle S. Gentry<br />
Copyright &copy; 2019-2024, Kyle Gentry<br />
**License**: MIT<br />
**GitHub**: [https://github.com/ksgwxfan/hurdat2parser](https://github.com/ksgwxfan/hurdat2parser)<br />
**Author's Webpages**:
 - [ksgWXfan's Project Page](https://ksgwxfan.github.io/)
 - [https://github.com/ksgwxfan](https://github.com/ksgwxfan)

[&#8679; back to Contents](#contents)












