# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/)
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.7] - 2025-10-24

### Added
* Updated print statements for multi-window to show the max number of pre-images per year.


## [1.0.6] - 2025-10-09

### Added
* Tests for MGRS tiles and burst geometries ensuring they overlap the antimeridian if and only if they are multipolygons.
* Updated readme with information about these mgrs/burst geometries and the dateline.
* Updated burst geometries using geopackage geometry from opera_adt/burst_db. See this issue: https://github.com/opera-adt/burst_db/issues/120 - some dateline geometries were cut off. The new geometries are larger and the table went from 24 MB to 37 MB. See this notebook: https://github.com/OPERA-Cal-Val/dist-s1-research/blob/dev/marshak/Zb_update_burst_table/Update%20Burst%20Geometries%20Using%20Geopackage.ipynb

## [1.0.5] - 2025-09-29

### Fixed
* CMR metadata does not have correctly migrated urls from ASF datapool to ASF cumulus - see https://github.com/opera-adt/dist-s1/issues/158.


## [1.0.4] - 2025-09-29

### Added
* Update time-series enumeration for multiple polarizations within an MGRS tile.
   - We now ensure that for each MGRS tile, a single fixed spatial burst creates a baseline (set of pre-images) for a given RTC-S1 burst product. That is, if the recent data was VV+VH in a burst, then the baseline for that burst VV+VH. Multiple dual polarization (i.e. both VV+VH and HH+HV) data can be used within a single MGRS tile.
* We now ensure that single polarization data is excluded from baselines and not used in the creation of the post-image set.

### Fixed
* Bug in enumerating 1 product - we did not ensure spatial bursts were consistent between pre-/post-image sets.


## [1.0.3] - 2025-09-09

### Fixed
* Defaults for `lookback_delta_days` from 0 to 365 in enumeration of multiple products. Leading to submission of jobs that had no baseline (see Issue: https://github.com/opera-adt/dist-s1-enumerator/issues/44)
* Renamed variables for easier tracking in `enumerat_dist_s1_products`.

## [1.0.2] - 2025-09-09

### Changed
* `backoff` library is removed and we now use `tenacity`

### Added
* Uses sessions and adapters to handle mutiple concurrent requests more reliably.

## [1.0.1] - 2025-08-07

### Added
* Improved tqdm outputs for enumeration of 1 dist-s1 product with multiwindow
* Added back more print statements

## [1.0.0] - 2025-08-05

### Changed
- `multi_window` is now the default parameter
- Consolidated `*_mw` and other parameters for single API.
- Assumes 3 anniversary dates for multi_window strategy

### Fixed
- New pandera import works only on 0.24.0
- Allow for acquisition metadata to be obtained around anniversary date 
- Typing of functions.

### Removed
- print statements

### Added
- `reorder_columns` can accept empty dataframes and creates empty table with schema (important for longer number of pre-image anniversaries), where there may be no acquisitions available.
- More docstring information on the enumeration functions
- pydantic models for updating/validating with `immediate_lookback` and `multi_window` strategy
- Function to get inputs for triggering `dist-s1` workflow (not necessarily all the RTC input data).
- Tests for multi-window lookback strategy
- Tests for workflow inputs


## [0.0.9] - 2025-06-06

### Fixed
- Pandera imports are changing and currently raising lots of warnings. We resolve these warnings.

## [0.0.8] - 2025-05-27

### Added
* Implemented `lookback_strategy` in `dist_enum`
* Use option `immediate_lookback` to search for the pre dates immediatelly before the `post_date`
* Use option `multi_window` to search for pre dates as windows defined by `max_pre_imgs_per_burst_mw` and `delta_lookback_days_mw` 


## [0.0.7] - 2025-01-16

### Fixed
* Fixed bug where RTC-S1 data was not being sorted by `jpl_burst_id` and `acq_dt` - this was causing us to establish baseline imagery from incorrect position


## [0.0.6] - 2025-01-16
  
## Changed
* Renamed `disable_tqdm` to `tqdm_enabled` in `localize_rtc_s1_ts`

## Added
* Description to `tqdm` progress bar in `localize_rtc_s1_ts`.
* Use `tqdm.auto` to automatically determine how `tqdm` should be displayed (either via CLI or in a notebook).

## [0.0.5] - 2025-01-16

* Dummy release due to expired github token.

## [0.0.4] - 2024-12-30

### Removed
* Removed `papermill` from environment.yml as it is not supported by 3.13

### Added
* Added `localize_rtc_s1_ts` to top-level imports
* Allowed `post_date` to be a string in the form of 'YYYY-MM-DD' for one product enumeration
* Schema for localized inputs to ensure columns for local paths: `loc_path_copol` and `loc_path_crosspol`

### Changed
* Added print date in notebook for clarity.
* Remove schema check from `append_pass_data` and enforce only certain columns to be present. 


## [0.0.3] - 2024-12-12

### Added
* Support for Python 3.13
* Explicit error messages when no data is retrieved from various tables (e.g. burst data, MGRS/burst LUT data, etc.)
* Suite of tests for enumeration
   * Unit tests - tests that can be run in a quick fashion and will be run on each PR to main/dev
   * Integration tests - in our case, hitting the DAAC API and downloading data when necessary; these also include running the Notebooks.
   * The latter is marked with `@pytest.mark.integration` and will be run on PRs to main (i.e. release PRs)
* Schema with Pandera to explicitly define and validate columns and their types
* Flexibility to retrieve either HH+HV or VV+VH or target one particular dual polarization type (currently does not support mixtures of dual polarized data).
* Expose the primary functions via the `__init__.py` file
* Updated environment.yml for Papermill tests

## Fixed
* `epsg` (now `utm_epsg`) was a string (with extra spacing) and now it's an integer

## Changed
* For the MGRS table, we renamed `epsg` to `utm_epsg` (to be in line with `utm_wkt`) and cast it as an int

## [0.0.2]

### Added
1. Minimum working example of enumeration of DIST-S1 products from MGRS tiles and (optionally) a track number in said MGRS tiles.

### Changed
API is *very* much in flux to support enumeration of large spatial areas and to support the localization of RTC-S1 data. Will likely continue to change to promote changing.

## [0.0.1]

The initial release of this library. This library provides:

1. Enumeration of DIST-S1-ALERT products. A DIST-S1-ALERT product can be uniquely identified (assuming a pre-image selection process is fixed)by:
   + MGRS tile
   + Acquisition time of the post-image
   + Track of the post-image
2. Ability to localize OPERA RTC-S1 data for the creation of the DIST-S1 product.
