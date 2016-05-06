#!/bin/bash

# Populate a cache by requesting all thumbnails from a list of IDs.
# For example run `list-thumbnails.sh` to create lists of image ids for
# each screen.
# Edit `WEB_HOST` in web_public_session.sh and run it to ensure you can
# obtain a session cookie
# Then run this script, passing in one of the lists of Image IDs as the
# only parameter

set -eu

if [ $# -ne 1  ]; then
    echo "USAGE: $(basename $0) input-file"
    exit 2
fi
INPUT="$1"

source web_public_session.sh

THUMBNAIL_TEMPLATE="$WEB_HOST/webgateway/render_thumbnail/:iid:/96/"

# http://stackoverflow.com/a/10929511
while read -r line || [[ -n "$line" ]]; do
    IID="$line"
    echo -n "$IID "
    $CURL_GET -D - -o /dev/null "${THUMBNAIL_TEMPLATE/:iid:/$IID}" | grep 'X-Proxy-Cache:'
done < "$INPUT"
