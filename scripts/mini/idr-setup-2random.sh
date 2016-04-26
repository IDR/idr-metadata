#!/bin/bash
# Import random plates from the directories specified in args
#
# For convenience `idr-metadata/` will be removed from the start of paths
# so that shell-completion can be used
#
# For example
#   idr-setup-2random.sh idr0004-thorpe-rad52 idr0017-breinig-drugscreen
# will import one randomly chosen plate from each of those screens
#
# For example
#   idr-setup-2random.sh idr-metadata/idr*
# will import one randomly chosen plate from every screen

date
OMERO_SERVER=/home/omero/OMERO.server
omero="$OMERO_SERVER/bin/omero"

# Get metadata
git config user.email || \
    git config --global user.email "ome-devel@lists.openmicroscopy.org.uk"
git config user.name || \
    git config --global user.name "IDR Project"

[ -d idr-metadata ] || git clone https://github.com/IDR/idr-metadata.git
pushd idr-metadata
# Convert /idr to /uod/idr
git fetch origin pull/73/head && git merge FETCH_HEAD -m 'Update paths'
# Get idr0016 metadata
git fetch origin pull/76/head && git merge FETCH_HEAD -m 'idr0016 metadata'

sed -i -re "s|^bin = .+|bin = '$omero'|" screen_import.py

mkdir -p logs
sudo -u omero $omero login -s localhost -u demo -w ome
for idr in "$@"; do
    idr="${idr#idr-metadata/}"
    plate="$(find "$idr" -ipath "*/plates/*" | shuf -n 1)"
    # Print and log stdout and stderr http://stackoverflow.com/a/692407
    logprefix="$(echo "$plate" | tr / -)"
    echo
    echo "***** $logprefix $plate *****"
    echo
    sudo -u omero ./screen_import.py "$plate" > \
        >(tee logs/$logprefix.log) 2> >(tee logs/$logprefix.err >&2)
done

popd
date
echo DONE
