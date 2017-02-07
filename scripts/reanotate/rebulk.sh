#!/bin/bash

#set -e -u -x

OMERO_DIST='/home/omero/workspace/OMERO-server/OMERO.server'
IDR_METADATA='/tmp/idr-metadata'


create_bulk () {
    object=${1:-};
    path=${2:-};
    if [ -n "$object" ] &&[ -n "$path" ]; then
        # generate new table
        echo "create_bulk for $object $path"
        echo $OMERO_DIST/bin/omero metadata populate --file $path-annotation.csv $object
    fi
}


while read -r obj path; do
    echo $obj $path

    # generate new table
    create_bulk $obj "$IDR_METADATA/$path"

done < input_bulk.txt
