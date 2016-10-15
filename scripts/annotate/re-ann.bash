# Delete all map annotations and re-apply
export PATH=$PATH:/home/omero/OMERO.server/bin
export IDR=../../

set -e
set -u

omero -q login demo@localhost
ARGS=$(sed "$1"'q;d' input)
YML=$IDR/$(echo $ARGS | cut -f1 -d" ")
CSV=${YML/bulkmap-config.yml/annotation.csv}
OBJID=$(echo $ARGS | cut -f2 -d" ")

omero metadata populate --context deletemap $OBJID
omero metadata populate --context deletemap --cfg $YML $OBJID

omero metadata populate --file $CSV $OBJID
omero metadata populate --context bulkmap --cfg $YML $OBJID
