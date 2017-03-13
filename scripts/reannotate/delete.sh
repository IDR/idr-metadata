#!/bin/bash

set -e

inputname="$1"

read -p 'Server:' host
host="${host:=localhost:4064}"

read -p 'Username: ' username
username="${username:=demo}"

read -sp 'Password: ' password

set -x

OMERO_DIST='/home/omero/OMERO.server'
IDR_METADATA='/tmp/idr-metadata'


delete_ann () {
    local object=${1:-};
    local ns=${2:-};
    if [ -n "$object" ] && [ -n "$ns" ]; then
        # delete annotations
        echo "delete $ns annotations $object"
        $OMERO_DIST/bin/omero metadata populate --batch 100 --wait 120 --context deletemap --localcfg "{\"ns\":\"$ns\"}" $object --report >> "log_delete_ann_$object" 2>&1
    fi
}

while read -r obj path ns; do
    echo "#####  BEGINNING $obj $path $ns  #####"

    # delete annotations
    set +x
    $OMERO_DIST/bin/omero login -u $username -w "$password" -s $host -C
    echo "Logged in $username@$host"
    set -x
    delete_ann $obj $ns
    $OMERO_DIST/bin/omero logout

    echo "#####  $obj DONE  #####"
done < $inputname
# IMPORTANT EOL
