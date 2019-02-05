# IDR studies

[![Published screens](https://img.shields.io/badge/dynamic/json.svg?label=Published%20&url=http%3A%2F%2Fidr.openmicroscopy.org%2Fapi%2Fv0%2Fm%2Fscreens%2F%3Flimit%3D0&query=meta.totalCount&colorB=blue&suffix=%20high%20content%20screens)](https://idr.openmicroscopy.org) [![Published experiments](https://img.shields.io/badge/dynamic/json.svg?label=Published%20&url=http%3A%2F%2Fidr.openmicroscopy.org%2Fapi%2Fv0%2Fm%2Fprojects%2F%3Flimit%3D0&query=meta.totalCount&colorB=blue&suffix=%20experiments)](https://idr.openmicroscopy.org)

All metadata associated with published studies in IDR is managed

## Study name 

After acceptance, IDR studies must be named as `idr<NNNN>-<name>-<description>`
where `idr<NNNN>` is the accession number of the study using an incremental
four digits integer, `<author>` is the name of one of the authors associated
with the publication, usually the first author, and `<description>` is a short
description of the study. The name should be lowercase.

## Study repository 

For each new IDR study, a repository must be created on GitHub under the [IDR](http://github.com/IDR/) organization using the study name as defined above. When ready for publication in the IDR, the study repository must be
registered in the top-level idr-metadata repository.

Study repository contain all curated metadata files associated with a study.
The structure of each study repository should use the following layout:

    .travis.yml         # Travis CI configuration file, used for validation
    bulk.yml            # Optional import configuration file for multi-experiment or multi-screen studies
    experimentA/        # Curated metadata for experimentA if applicable
        idrNNNN-experimentA-annotation.csv       # Curated image annotations
        idrNNNN-experimentA-bulk.yml             # Configuration file for import
        idrNNNN-experimentA-bulkmap-config.yml   # Configuration file for annotation
        idrNNNN-experimentA-filePaths.tsv        # Files/folder to be imported
    experimentB/        # Curated metadata for experimentA if applicable
       ...
    idrNNNN-study.txt.  # Top-level metadata file describing the study
    screenA/            # Curated metadata for screenA if applicable
        idrNNNN-screenA-annotation.csv           # Curated well annotations
        idrNNNN-screenA-bulk.yml                 # Configuration file for import
        idrNNNN-screenA-bulkmap-config.yml       # Configuration file for annotation
        idrNNNN-screenA-plates.tsv               # Plates to be imported
    screenB/            # Curated metadata for screenA if applicable
       ...
    scripts/            # Folder containing custom scripts associated with the study
    README.md           # Optional top-level readme
    requirements.txt    # Python dependencies used for Travis or scripts
