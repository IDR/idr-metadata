#!/bin/bash
# Run a script, looping through a set of files and idr identifiers

#set -eux

date
OMERO_SERVER=/home/omero/OMERO.server
omero="$OMERO_SERVER/bin/omero"

export PYTHONPATH="$OMERO_SERVER/lib/python:$PYTHONPATH"
pushd "$(dirname "$0")/.."

# Don't forget hql -q outputs the row number as the first column
$omero login

$omero hql 'select id,name from Screen' --limit -1 -q --style plain | \
    while IFS='' read -r line; do
        IFS=, read -a arr <<< "$line"
        echo "id:${arr[1]} name:${arr[2]}"
        # Only want the top-level name, not screenA etc
        name=${arr[2]%%/*}

        stat ${name}/idr*-study.txt >/dev/null 2> /dev/null # || continue
        python scripts/annotate_study.py \
            ${name}/idr*-study.txt Screen:${arr[1]}
    done

$omero hql 'select id,name from Project' --limit -1 -q --style plain | \
    while IFS='' read -r line; do
        IFS=, read -a arr <<< "$line"
        echo "id:${arr[1]} name:${arr[2]}"
        # Only want the top-level name, not experimentA etc
        name=${arr[2]%%/*}

        stat ${arr[2]}/idr*-study.txt >/dev/null 2> /dev/null # || continue
        python scripts/annotate_study.py \
            ${arr[2]}/idr*-study.txt Project:${arr[1]}
    done

popd
date
echo DONE
