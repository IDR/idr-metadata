#!/bin/bash
# Rendering settings

date
OMERO_SERVER=/home/omero/OMERO.server
omero="$OMERO_SERVER/bin/omero"

pushd idr-metadata
# Fetch rendering definitions
git fetch origin pull/75/head && git merge FETCH_HEAD -m 'Get rendering definitions'

# Don't forget hql -q outputs the row number as the first column
$omero login -s localhost -u demo -w ome
$omero hql 'select id,name from Screen' --limit -1 -q --style plain | \
    while IFS='' read -r line; do
        IFS=, read -a arr <<< "$line"
        echo "id:${arr[1]} name:${arr[2]}"

        # Get the first image in each screen
        IFS=, read -a iarr <<<$( $omero hql -q --limit 1 --style plain "\
            SELECT spl.parent.id,spl.parent.name,ws.image.id \
            FROM WellSample ws, Plate p, ScreenPlateLink spl \
            WHERE spl.child=p AND ws.well.plate=p \
            AND spl.parent.id=${arr[1]}" )

        stat ${arr[2]}/idr*-renderdef.yml >/dev/null 2> /dev/null|| continue
        $omero render edit Image:${iarr[3]} ${arr[2]}/idr*-renderdef.yml
        $omero render copy Image:${iarr[3]} Screen:${arr[1]}
    done

popd
date
echo DONE
