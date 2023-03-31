# LoRDEC

- [![Build status](https://gite.lirmm.fr/rivals/lordec/badges/master/build.svg)](https://gite.lirmm.fr/rivals/lordec/commits/master)
- [![coverage report](https://gite.lirmm.fr/rivals/lordec/badges/master/coverage.svg?job=lcov)](http://rivals.lirmm.net/lordec/lcov/builds/rivals/lordec/index.html) with lcov
- [![coverage report](https://gite.lirmm.fr/rivals/lordec/badges/master/coverage.svg?job=gcovr)](http://rivals.lirmm.net/lordec/gcovr/index.html) with gcovr

Program for correcting sequencing errors in PacBio reads using highly accurate short reads (e.g. Illumina).

## Reference

L. Salmela, and E. Rivals. LoRDEC: accurate and efficient long read error correction. Bioinformatics 30(24):3506-3514, 2014.

Access: http://bioinformatics.oxfordjournals.org/content/30/24/3506

## System Requirements

LoRDEC has been tested on Linux. Compiling the program requires gcc version 4.5 or newer, Boost C++ libraries (e.g. libboost1.48-dev package or newer), and GATB Core library.

## Installation

LoRDEC is distributed for GNU/Linux as :

* Debian package
* Conda package
* Binary tarball

and for MacOSX (>=10.9) as :

* Conda package
* Binary tarball

Sources can be easily compiled for both systems as well.

Check the [lordec-release wiki](https://gite.lirmm.fr/lordec/lordec-releases/wikis/home) for installation procedures.
