#!/bin/bash

set -e

read -p 'Server:' host
host="${host:=localhost:4064}"

read -p 'Username: ' username
username="${username:=demo}"

read -sp 'Password: ' password

echo "Logged in $username@$host"

set -x

OMERO_DIST='/home/omero/OMERO.server'
IDR_METADATA='/tmp/idr-metadata'


delete_ann () {
    object=${1:-};
    ns=${2:-};
    if [ -n "$object" ] && [ -n "$ns" ]; then
        # delete annotations
        echo "delete $ns annotations $object"
        $OMERO_DIST/bin/omero metadata populate --batch 10 --wait 600 --context deletemap --localcfg "{\"ns\":\"$ns\"}" $object --report
    fi
}


populate_ann () {
    object=${1:-};
    path=${2:-};
    ns=${3:-};
    if [ -n "$object" ] && [ -n "$path" ] && [ -n "$ns" ]; then
        # populate new annotations
        echo "populate new $ns annotations $object $path"
        $OMERO_DIST/bin/omero metadata populate --context bulkmap --cfg $path-bulkmap-config.yml $object --localcfg "{\"ns\":\"$ns\"}" --report
    fi
}


while read -r obj path ns; do
    # IMPORTANT EOL
    echo "$obj $path $ns #######################"

    # delete annotations
    set +x
    $OMERO_DIST/bin/omero login -u $username -w "$password" -s $host
    set -x
    delete_ann $obj $ns
    $OMERO_DIST/bin/omero logout

    # populate new annotations
    set +x
    $OMERO_DIST/bin/omero login -u $username -w "$password" -s $host
    set -x
    populate_ann $obj "$IDR_METADATA/$path" $ns
    $OMERO_DIST/bin/omero logout

    echo "$obj DONE ##################################"
done < demo33_input.txt
