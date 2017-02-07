#!/bin/bash

read -p 'Server:' host
host="${host:=localhost:4064}"

read -p 'Username: ' username
username="${username:=demo}"

read -sp 'Password: ' password

echo "Logged in $username@$host"


set -x

OMERO_DIST='/home/omero/OMERO.server'
IDR_METADATA='/tmp/idr-metadata'


create_bulk () {
    object=${1:-};
    path=${2:-};
    if [ -n "$object" ] &&[ -n "$path" ]; then
        # generate new table
        echo "generate new bulk annotation $object $path"
        $OMERO_DIST/bin/omero metadata populate --file $path-annotation.csv $object
    fi
}

set +x
$OMERO_DIST/bin/omero login -u $username -w "$password" -s $host
set -x

while read -r obj path; do
    # IMPORTANT EOL
    echo $obj $path

    # generate new table
    create_bulk $obj "$IDR_METADATA/$path"

done < demo33_input_bulk.txt

$OMERO_DIST/bin/omero logout
