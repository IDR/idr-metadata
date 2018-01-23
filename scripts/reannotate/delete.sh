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


delete_ann () {
    local object=${1:-};
    local ns=${2:-};
    if [ -n "$object" ] && [ -n "$ns" ]; then
        # delete annotations
        echo "delete $ns annotations $object"
        $OMERO_DIST/bin/omero metadata populate --batch 100 --wait 120 --context deletemap --localcfg "{\"ns\":\"$ns\"}" $object --report >> "log_delete_ann_$object" 2>&1
    fi
}

delete_all () {
    local object=${1:-};
    local path=${2:-};
    if [ -n "$object" ] && [ -n "$path" ]; then
        # delete annotations
        echo "delete all annotations $object"
        $OMERO_DIST/bin/omero metadata populate --batch 100 --wait 120 --context deletemap --cfg $path-bulkmap-config.yml $object --report >> "log_delete_ann_$object" 2>&1
    fi
}


while read -r obj path ns; do
    echo "#####  BEGINNING $obj $path $ns  #####"

    # delete annotations
    set +x
    $OMERO_DIST/bin/omero login -u $username -w "$password" -s $host -C
    echo "Logged in $username@$host"
    set -x
    if [[ ! -z "$ns" ]]; then
        delete_ann $obj $ns
    else
        delete_all $obj "$IDR_METADATA/$path"
    fi
    $OMERO_DIST/bin/omero logout

    echo "#####  $obj DONE  #####"
done < $inputname
# IMPORTANT EOL
