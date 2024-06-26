## `hurdat2parser` Change Log

\* Extra details of changes are located within `README.md`.

### Contents

- [v2.3 and v2.3.0.1](#v23-and-v2301)
- [v2.2.3.1](#v2231)
- [v2.2.3](#v223)
- [v2.2.2](#v222)
- [v2.2](#v22)
- [v2.1.1](#v211)
- [v2.1](#v21)
- [v2.0.1](#v201)

## v2.3 and v2.3.0.1
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

## v2.2.3.1
- Hotfix for `<TropicalCyclone>.track_map()` that simply skips over `tkinter`-dependent lines upon error (will occur if user does not have `tkinter` installed).

## v2.2.3
- Accounts for the possibility of typos/errors in the actual database.
  - Notifies the user if a storm has already been ingested, but does overwrite the previous `TropicalCyclone` entry.
  - Will skip a `TCRecordEntry` and notify the user if an error occurs whilst trying to generate it.
- fix for `track_map()` to work for cyclones prior to 1900. There was an issue with the label formatting I was using.
- fix for rankings for empty partial seasons in `rank_seasons_thru` where quantity of ranks were being returned as one too many.

## v2.2.2
- Hotfix for `<TCRecordEntry>` vars `previous_entries` and `next_entries`. These vars were introduced in `v2.2`. I thought I had confirmed that they worked, but I was getting issues with trying to call. Fixed now though.
- small formatting tweak (wasn't throwing errors) of a (mostly) internal method `_season_stats_str`.

## v2.2
- Docstring'd `TCRecordEntry` properties
- Changes to the `<Hurdat2>` object:
  - when reading-in files on `__init__`, multiple local files are now supported.
  - enabled download of the most-recent hurdat2 dataset through the `basin` kwarg.
  - added a `urlcheck` kwarg. If `True`, the "file-path"s listed will be treated like URLs and a download attempt will be made.
  - removed the `_filesappended` attribute
  - Searching for notoriously-named storms can be done by a dash (`"-"`) prefix to the search string in addition to an underscore (see [Example Calls](#example-calls) section)
  - Revamped `output_climo_csv`, `output_season_csv`, and `output_storms_csv` methods
    - simplified code; updated and unified attributes used in the reports and made it significantly easier for future maintenance.
  - moved `multi_season_info` method to `_reports`
- New properties for both `Season` and `TropicalCyclone`:
  - `duration`
    - `Season` version reports time between the first and last day of the season (see further in the document for explanation)
	- `TropicalCyclone` version just reports the track-life in days, regardless of status. More useful status-based duration properties were created too. Keep reading (a few lines down).
  - `tc_entries` returns a list of `TCRecordEntry`s where a storm was a designated tropical cyclone.
  - `start_date`, `start_ordinal`, and `end_date`, `end_ordinal` report the starting/ending dates and/or days of the year
- New `TropicalCyclone` variables:
  - `ACE_no_landfall`
  - `duration_<TC, TS, HU, MHU>` - These properties report the aggregate time in days that a tropical cyclone was designated that status or stronger, accounting for fluxuations in storm statuses and strengths.
  - removed `coord_list` method. It was redundant as it was like a shortened combination of the `summary` method.
- New `TCRecordEntry` variables:
  - tweaked how location variables are defined. `location` and `location_reversed` are now properties that depend on the express definition of the variables `lat` and `lon` rather than the other way around.
  - tweak of not-available wind-extent data. As of the moment typing this, wind-extent data is only provided for storms since 2004. All previous wind-extent data is `-999`, meaning its unavailable. But if a storm has max winds of `<` 64, its Hurricane wind extent has to be 0. So when ingesting the data, this determination is made.
  - tweaked ingest of data to prevent errors due to possible new Hurdat2 categories introduced in future versions. This was the problem with `v2.1` that was responsible for the need for a `v2.11` release. This particular version wouldn't be able to read-in the new variables in such a situation, but it would still be functional with the newer database (unless order of variables are switched around).
  - the formerly-called variable `wind_radii` from `v2.11` is now called `maxwind_radius`. I don't know why I called it `radii`, as in plural of radius. I guess it sounded science-y or smart. haha. But the change is also more readable.
  - Surface Area (coverage)-based variables `areal_extent_TS`, `areal_extent_TS50`, and `areal_extent_HU`.
    - These are calculated from reported wind-extents in the database.
  - `track_distance`: the track distance of the cyclone up to the point of the respective entry; this does not account for storm status
  - `previous_entries` and `next_entries`: lists of the previous and next recorded entries, respectively, in the `TropicalCyclone`'s record
  - `previous_entry` and `next_entry`: the previous and next recorded entry, respectively, in the `TropicalCyclone`'s record
  - `direction()`: the `TropicalCyclone`'s heading in degrees (or cardinal, if desired...see docstring)
  - `speed`: the `TropicalCyclone`'s forward speed in knots.
  - Properties to simplify coding and reduce probability of coding errors.
    - `is_TC`: `bool` indicating whether or not a storm was designated as a tropical cyclone at the `<TCRecordEntry>.entrytime`.
    - `is_synoptic`: `bool` indicating whether or not an entry occurred at a synoptic time (0Z, 6Z, 12Z, 18Z).
- Added `report_type` default keyword argument to the `<Season>.stats` method. User can dictate if report prints to the console or gets back a string version of the report.
- Fixed an exclusion of `maxwind_radius` (formerly called `wind_radii`) from `<TCRecordEntry>.hurdat2()` calls. (which was only introduced in the previous version).
- Tweaked landfall-disclaimer in `<Season>.stats()` output to reflect the April 2022 release of the Hurdat2 database.
- Changed `<Season>.__getitem__` method to account for the possibility of merged basin databases, giving the user a choice between mulitple storms that occurred in the same year, but in different geographical basins with shared cyclone numbers. The East Pacific Hurdat2 is an example, natively including storms from the East and Central Pacific Basins.
- `<TropicalCyclone>.track_map()` tweaks:
  - focuses on the part of the track where the storm was designated a tropical cyclone.
  - now fills more of the screen, offering a better user experience, and lessens the likelihood of the user feeling compelled to resize the initial window.
  - added legend. By default, it will display. But if you'd rather it not display, there is a keyword to turn it off
  - I believe it may be slightly faster now, thanks to performance tips in matplotlib docs.
  - map coordinate lists used now significantly smaller.
- tweaked a very minor syntax quirk. Somewhere in the code I had used `is not` instead of the more-proper `!=`.
- `basin` tweaks
  - introduced a new method `<Hurdat2>.basin_abbr()` which returns a list of basin abbreviations used; will be used in report outputs.
- Fixed memory-location identification in `__repr__` methods

## v2.1.1
- \*\*\* This version used to be `v2.11`. I changed it because it was conflicting with PyPI recognizing `v2.2` as the newest.
- Patched to enable compatibility with the May 2022 release of the Hurdat2 database
- Added a `TCRecordEntry` variable called `wind_radii` (the new variable included in the May 2022 Hurdat2 release. There may be some future potential in expanding the use of this variable, but its availability is currently limited to the 2021 Hurricane Season
- Fixed calls to `TCRecordEntry` variables `avg_wind_extent_<STATUS>`
- `info()` method for `Season` objects removed (use the `stats()` method instead)
- modification of `<Hurdat2>.basin()`; now a method instead of property.
- Fixed `rank_seasons_thru()` where a call without keywords (becoming a wrapper for `rank_seasons`) had an ill-advised direct call to a dictionary key instead of the get method

## v2.1
- Restructured module for easier reading/comprehension including addition of 'read-only' variables
- Read-in slightly faster (eliminated separate `for` loop for season read-in).
- Addition of `<Hurdat2>.basin` property, a human-readable string that reports the region/location of the hurdat2 file, based on the storms within the record.
- Added a `stats` method for reporting on full or partial statistics and ranks for individual seasons.
- Changed former Rank keyword `ascending` to `descending`, so that it has the same meaning of the `reverse` keyword of sorting functions.
- Clean-up of ranking methods; concision (generally) and readability improved; significant performance reduction in `rank_climo` as it now only collects data that will be reported.
- Addition of Season and Tropical Cyclone attributes `cat45reach` and `cat5reach`
- fixed small issue in `rank_seasons_thru` that produced minute inaccuracies with track distance related calculations, which was, in-part, incomplete due to an overseen exclusion of a valid distance segment.
- shifted `thru` argument on `rank_seasons_thru` to a keyword argument so the positional default keyword parameters would match up to `rank_seasons`
- added `hurdat2()` methods to `Season` and `TropicalCylone` objects, printing Hurdat2-formatted output.
- added `__getitem__` method to `TropicalCyclones`; a shortcut to call `TCRecordEntry` objects
- added flexibility to `TropicalCyclone` `output_geojson` method by allowing user to select the type of feature output: point-based or linestring-based.
- generated geoJSON files now default to an indention of 2
- fixed typo in code for `Season` `geoJSON` method where it was substituting MHDP values for ACE.
- included `matplotlib`-based track maps for individual storms! It's considered experimental, but quite functional. Right now, good for Atlantic and other basins not split by 180deg Longitude. Currently does not include a legend. That is in the plans for the future though.
- changed behavior of `__getitem__` methods
- `TropicalCyclone`s and `TCRecordEntry`s are now "self-aware" of parent objects, `Season`, `TropicalCyclone` respectively.
- Added representation (`__repr__`) magic methods that describe their objects beyond class type and memory address
- added `index` property for `TCRecordEntry` objects; returns the respective `<TropicalCyclone>.entry.index()` for the entry
- gave control to `rank_storms`s `coordextent` behavior using a keyword `contains_method`.

## v2.0.1
- fixed a method call-related error within `rank_seasons_thru`. So it works nice now.