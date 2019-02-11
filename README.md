# IDR studies

[![Published screens](https://img.shields.io/badge/dynamic/json.svg?label=Published%20&url=http%3A%2F%2Fidr.openmicroscopy.org%2Fapi%2Fv0%2Fm%2Fscreens%2F%3Flimit%3D0&query=meta.totalCount&colorB=blue&suffix=%20high%20content%20screens)](https://idr.openmicroscopy.org) [![Published experiments](https://img.shields.io/badge/dynamic/json.svg?label=Published%20&url=http%3A%2F%2Fidr.openmicroscopy.org%2Fapi%2Fv0%2Fm%2Fprojects%2F%3Flimit%3D0&query=meta.totalCount&colorB=blue&suffix=%20experiments)](https://idr.openmicroscopy.org)

All metadata associated with published studies in IDR is managed in this
repository.

## Study name 

After acceptance, IDR studies must be named as `idr<NNNN>-<name>-<description>`
where `idr<NNNN>` is the accession number of the study using an incremental
four digits integer, `<name>` is the name of one of the authors associated
with the publication, usually the first author, and `<description>` is a short
description of the study or the name of the project/consortium. The study name
should be lowercase.

## Study repository 

For each new study, a repository must be created on GitHub under the
[IDR](http://github.com/IDR/) organization using the study name as defined
above. When ready for publication in the IDR, the study repository must be
registered in the top-level idr-metadata repository as a submodule.

A study repository contains all original and curated metadata files associated
with a study. The
[idr0000-lastname-example](https://github.com/IDR/idr0000-lastname-example)
repository contains the templates that should be used by submitters
when sending original metadata files for screen or experiment studies. The
structure of each study repository should use the following layout:

    .travis.yml                                  # Travis CI configuration file, used for validation (mandatory)
    bulk.yml                                     # Import configuration file for multi-experiment or multi-screen studies (optional)
    experimentA/                                 # Curated metadata for experimentA (if applicable)
        idrNNNN-experimentA-annotation.csv       # Curated annotation file (mandatory)
        idrNNNN-experimentA-assays.txt           # Original annotation file (recommended)
        idrNNNN-experimentA-bulk.yml             # Configuration file for import (mandatory)
        idrNNNN-experimentA-bulkmap-config.yml   # Configuration file for annotation (mandatory)
        idrNNNN-experimentA-filePaths.tsv        # Files/folder to be imported (mandatory)
    experimentB/                                 # Curated metadata for experimentB (if applicable)
       ...
    idrNNNN-study.txt                            # Top-level metadata file describing the study (mandatory)
    screenA/                                     # Curated metadata for screenA if applicable
        idrNNNN-screenA-annotation.csv           # Curated annotation file (mandatory)
        idrNNNN-screenA-bulk.yml                 # Configuration file for import (mandatory)
        idrNNNN-screenA-bulkmap-config.yml       # Configuration file for annotation (mandatory)
        idrNNNN-screenA-library.txt              # Original annotation file (recommended)
        idrNNNN-screenA-plates.tsv               # Plates to be imported (mandatory)
    screenB/                                     # Curated metadata for screenB if applicable
       ...
    scripts/                                     # Folder containing custom scripts associated with the study (optional)
    README.md                                    # Optional top-level readme (optional)
    requirements.txt                             # Python dependencies used for Travis or scripts (recommended)
