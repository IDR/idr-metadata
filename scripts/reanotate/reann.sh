#!/bin/bash

set -e -u -x

OMERO_DIST='/home/omero/workspace/OMERO-server/OMERO.server'
IDR_METADATA='/tmp/idr-metadata'


delete_ann () {
    object=${1:-};
    ns=${2:-};
    if [ -n "$object" ] && [ -n "$ns" ]; then
        # delete gene annotations
        echo "delete_ann for $object $ns"
        echo $OMERO_DIST/bin/omero metadata populate --batch 10 --wait 600 --context deletemap --localcfg $ns $object --report
    fi
}


populate_ann () {
    object=${1:-};
    path=${2:-};
    ns=${3:-};
    if [ -n "$object" ] && [ -n "$path" ] && [ -n "$ns" ]; then
        # populate new gene annotations
        echo "populate_ann for $object $path $ns"
        echo $OMERO_DIST/bin/omero metadata populate --context bulkmap --cfg $path-bulkmap-config.yml $object --localcfg $ns --report
    fi
}


while read -r obj path ns skip; do
    echo $obj $path $ns $skip

    # delete gene annotations
    delete_ann $obj $ns

    # populate new gene annotations
    populate_ann $obj "$IDR_METADATA/$path" $ns

    echo "$obj DONE"
done < input.txt
