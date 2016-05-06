#!/bin/bash

# Populate a cache by requesting all metadata from lists of IDs.
# For example run `list-metadata.sh` to create lists of image ids for
# each screen.
# Edit `WEB_HOST` in web_public_session.sh and run it to ensure you can
# obtain a session cookie
# Then run this script, passing in one of the lists of Image IDs as the
# only parameter

set -eu

if [ $# -ne 1  ]; then
    echo "USAGE: $(basename $0) input-{Screen,Plate,PlateAcquisition}.txt"
    exit 2
fi
INPUT="$1"

source "$(dirname $0)/web_public_session.sh"

case "$INPUT" in
*PlateAcquisition.*)
    objtype=acquisition
    ;;
*Plate.*)
    objtype=plate
    ;;
*Screen.*)
    objtype=screen
    ;;
*)
    echo "ERROR: Unknown objtype: $INPUT"
    exit 2
    ;;
esac

METADATA_TEMPLATE="$WEB_HOST/webclient/metadata_details/screen/:id:/"

# http://stackoverflow.com/a/10929511
while read -r line || [[ -n "$line" ]]; do
    ID="$line"
    echo -n "$ID "
    $CURL_GET -D - -o /dev/null "${THUMBNAIL_TEMPLATE/:id:/$ID}" | grep 'X-Proxy-Cache:' || :
done < "$INPUT"
