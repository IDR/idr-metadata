#!/bin/bash

set -e -u -x

OMERO_DIST='/home/omero/workspace/OMERO-server/OMERO.server'
IDR_METADATA='/tmp/idr-metadata'


delete_ann () {
    object=$1;
    ns=$2;

    # delete gene annotations
    $OMERO_DIST/bin/omero metadata populate --batch 10 --wait 600 --context deletemap --localcfg $ns $object --report
}


create_bulk () {
    object=$1;
    path=$2;

    # generate new table
    $OMERO_DIST/bin/omero metadata populate --file $path-annotation.csv $object
}

populate_ann () {
    object=$1;
    path=$2;
    ns=$3;

    # populate new gene annotations
    $OMERO_DIST/bin/omero metadata populate --context bulkmap --cfg $path-bulkmap-config.yml $object --localcfg $ns --report
}


while read -r obj path ns; do
    $obj $path $ns

    # delete gene annotations
    delete_ann $obj $ns

    # generate new table
    create_bulk $obj "$IDR_METADATA/$path"

    # populate new gene annotations
    populate_ann $obj "$IDR_METADATA/$path" $ns

done < input.txt
