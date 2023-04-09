## `hurdat2parser` Change Log

\* Extra details of changes are located within `README.md`.

### Contents

- [v2.2](#v22)
- [v2.1.1](#v211)
- [v2.1](#v21)
- [v2.0.1](#v201)

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