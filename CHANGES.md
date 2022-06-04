## `hurdat2parser` Change Log

\* Extra details of changes are located within `README.md`.

### Contents

- [v2.11](#v211)
- [v2.1](#v21)
- [v2.0.1](#v201)

## v2.11
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