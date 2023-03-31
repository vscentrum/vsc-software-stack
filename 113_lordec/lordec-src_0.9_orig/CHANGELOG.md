# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) 
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
## 0.9 – 2018-05-29
### Added
- HPC script to parallelize lordec-correct on HPC clusters

### Changed
- improved progression display : estimated remaining time, speed, time spent
- Makefile : always compile with local boost lib
- no more maximum read length limit

### Fixed
- small memory leaks, memory cleaning

## 0.8 – 2018-03-07
### Added
- Makefile : add option to use local boost lib
- scripts to parallelize LoRDEC on HPC clusters by splitting long read file (compatible with SGE and SLURM)
- add -p option to lordec-correct to display progress
- use continuous integration to perform blackbox tests and unit tests

### Changed
- compatibility with GATB v1.4.1

### Fixed
- fix bug when using absolute paths with multiple coma-separated short read files
- fix bug when no write access near short read file to save graph file

## 0.7 – 2017-02-22
### Added
- Conda package
- Debian package
- MacOSX binaries
- Makefile compatibility for source compilation on MacOSX
- Compilation with GATB v1.3.0
