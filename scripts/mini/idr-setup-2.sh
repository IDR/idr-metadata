#!/bin/bash
# Import- you may want to do this in screen in case your connection is broken

date
OMERO_SERVER=/home/omero/OMERO.server
omero="$OMERO_SERVER/bin/omero"

# Get metadata
git config user.email || \
    git config --global user.email "ome-devel@lists.openmicroscopy.org.uk"
git config user.name || \
    git config --global user.name "IDR Project"

git clone https://github.com/IDR/idr-metadata.git
pushd idr-metadata
# Convert /idr to /uod/idr
git fetch origin pull/73/head && git merge FETCH_HEAD -m 'Update paths'

sed -i -re "s|^bin = .+|bin = '$omero'|" idr-metadata/screen_import.py

plate_0001=idr0001-graml-sysgro/screenA/plates/X_110222_S1
plate_0002=idr0002-heriche-condensation/screenA/plates/plate1_1_013
plate_0003="idr0003-breker-plasticity/screenA/plates/DTT p1"
plate_0004=idr0004-thorpe-rad52/screenA/plates/P101
plate_0005=idr0005-toret-adhesion/screenA/plates/Primary_001
plate_0006=idr0006-fong-nuclearbodies/screenA/plates/11001
plate_0007=idr0007-srikumar-sumo/screenA/plates/pro-smt3allR_plate1
plate_0008=idr0008-rohn-actinome/screenA/plates/001B30_S2R
plate_0009=idr0009-simpson-secretion/screenA/plates/0001-03--2005-08-01
plate_0010=idr0010-doil-dnadamage/screenA/plates/1-23
#plate_0011=
plate_0012=idr0012-fuchs-cellmorph/screenA/plates/HT01
plate_0013=idr0013-neumann-mitocheck/screenA/plates/LT0001_02
#plate_0014=
plate_0015=idr0015-UNKNOWN-taraoceans/screenA/plates/TARA_HCS1_H5_G100001472_G100001473--2013_09_28_19_45_25_chamber--U00--V01
#plate_0016=
plate_0017=idr0017-breinig-drugscreen/screenA/plates/2011-11-17_X-Man_LOPAC_X01_LP_S01_1

mkdir logs
sudo -u omero $omero login -s localhost -u demo -w ome
for plate in $plate_0001 $plate_0002 "$plate_0003" $plate_0004 $plate_0005 \
        $plate_0006 $plate_0007 $plate_0008 $plate_0009 $plate_0010 \
        $plate_0012 $plate_0013 $plate_0015 $plate_0017; do
    # Print and log stdout and stderr http://stackoverflow.com/a/692407
    logprefix="${plate%%-*}"
    echo
    echo "***** $logprefix $plate *****"
    echo
    sudo -u omero ./screen_import.py "$plate" > \
        >(tee logs/$logprefix.log) 2> >(tee logs/$logprefix.err >&2)
done

popd
date
echo DONE
