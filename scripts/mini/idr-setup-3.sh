#!/bin/bash
# Create bulk annotations

date
OMERO_SERVER=/home/omero/OMERO.server
omero="$OMERO_SERVER/bin/omero"

pushd idr-metadata
export OMERO_DEV_PLUGINS=1

$omero login -s localhost -u demo -w ome
$omero hql 'select id,name from Screen' --limit -1 -q --style plain | \
    while IFS='' read -r line; do
        IFS=, read -a arr <<< "$line"
        echo "id:${arr[1]} name:${arr[2]}"

        $omero metadata populate --file ${arr[2]}/idr*-annotation.csv Screen:${arr[1]}
        $omero metadata populate --context bulkmap --cfg ${arr[2]}/idr*-bulkmap-config.yml Screen:${arr[1]}
    done

popd
date
echo DONE
