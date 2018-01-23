#!/bin/bash

set -e

inputname="$1"

read -p 'Server(localhost:4064):' host
host="${host:=localhost:4064}"

read -p 'Username(demo): ' username
username="${username:=demo}"

read -sp 'Password: ' password

set -x

OMERO_DIST='/opt/omero/server/OMERO.server'
IDR_METADATA=$(dirname $(dirname $(dirname $0)))

populate_ann () {
    local object=${1:-};
    local path=${2:-};
    local ns=${3:-};
    if [ -n "$object" ] && [ -n "$path" ] ; then
        # populate new annotations
        echo "populate new $ns annotations $object $path"
        if [ -n "$ns" ]; then
            $OMERO_DIST/bin/omero metadata populate --context bulkmap --cfg $path-bulkmap-config.yml $object --localcfg "{\"ns\":\"$ns\"}" --report >> "log_populate_ann_$object" 2>&1
        else
            $OMERO_DIST/bin/omero metadata populate --context bulkmap --cfg $path-bulkmap-config.yml $object --report >> "log_populate_ann_$object" 2>&1
        fi
    fi
}


while read -r obj path ns; do
    echo "#####  BEGINNING $obj $path $ns  #####"

    # populate new annotations
    set +x
    $OMERO_DIST/bin/omero login -u $username -w "$password" -s $host -C
    echo "Logged in $username@$host"
    set -x
    populate_ann $obj "$IDR_METADATA/$path" $ns
    $OMERO_DIST/bin/omero logout

    echo "#####  $obj DONE  #####"
done < $inputname
# IMPORTANT EOL
