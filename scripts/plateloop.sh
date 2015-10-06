#!/bin/sh
# USAGE: plateloop.sh path/to/bulkmap-config.yml ScreenID

set -eu

CFG="$1"
SCREEN="$2"
LOG="screen-$SCREEN.log"
OMERO=~/omero-test/OMERO-TEST/bin/omero

$OMERO login

$OMERO metadata populate --context bulkmap --report \
    --cfg "$CFG" "Screen:$SCREEN" --dry-run 2> /dev/null || true

fid=$($OMERO metadata allanns Screen:$SCREEN --report \
    | grep '    file: OriginalFile:' | cut -d: -f3-)
if [ -z "$fid" ]; then
    echo "ERROR: Configuration OriginalFile ID not found"
    exit 2
else
    echo "Configuration OriginalFile:$fid"
fi

PLATEIDS=$($OMERO hql "SELECT child.id FROM ScreenPlateLink WHERE \
    parent=$SCREEN ORDER BY child.id" \
    --limit 100000 -q --style plain | cut -f2 -d,)

echo >> "$LOG"
echo -n "Started" >> "$LOG"
for pid in $PLATEIDS; do
    $OMERO metadata populate --context bulkmap --report \
        --cfg OriginalFile:$fid Plate:$pid 2>&1 | tee -a "$LOG"
done
echo -n "Finished" >> "$LOG"
date >> "$LOG"
