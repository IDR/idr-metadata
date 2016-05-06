#!/bin/bash

set -eu

# The caching proxy server
WEB_HOST=http://10.0.51.111

LOGIN_URL="$WEB_HOST/webclient/userdata/?experimenter=-1"
COOKIES=cookies.txt

rm -f $COOKIES
CURL_BIN="curl -i -k -s -c $COOKIES -b $COOKIES -e $LOGIN_URL"
CURL_GET="curl -i -k -s -b $COOKIES -e $LOGIN_URL"

echo -n "Getting CRSF token and session ID "
# Retry for 2 mins
i=0
csrf_token=
session_id=
while [ \( -z "$csrf_token" -o -z "$session_id" \) -a $i -lt 60 ]; do
    sleep 2
    $CURL_BIN $LOGIN_URL > /dev/null || true
    csrf_token=$(grep csrftoken cookies.txt | awk '{print $7}')
    session_id=$(grep sessionid cookies.txt | awk '{print $7}')
    echo -n "."
    let ++i
done
echo

if [ -z "$csrf_token" ]; then
    echo "Failed to get CSRF token"
    exit 2
fi
if [ -z "$session_id" ]; then
    echo "Failed to get seesion id"
    exit 2
fi

echo "CSRF token: $csrf_token"
echo "Session id: $session_id"
