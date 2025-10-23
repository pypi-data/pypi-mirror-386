# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions workflow for building and publishing wheels

### Changed
- Migrated default branch from `master` to `main`

### Fixed

### Removed

## [0.1.0] - 2025-10-23

### Added
- Initial release of dwd_opendata_client library
- Download functionality for meteorological data from DWD open data platform
- Support for multiple stations and variables
- Station mapping functionality with geographic filtering
- Support for hourly, daily, and 10-minute time resolutions
- Automatic data caching to `~/.local/share/opendata_dwd`

### Features
- Load data from multiple stations and variables into xarray DataArrays
- Station mapping functionality to identify which stations provide specific variables
- Automatic handling of DWD data structure idiosyncrasies

[Unreleased]: https://github.com/iskur/dwd_opendata/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/iskur/dwd_opendata/releases/tag/v0.1.0
