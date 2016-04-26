#!/bin/bash
# Features and ROIs
# Currently sysgro only

date
OMERO_SERVER=/home/omero/OMERO.server
omero="$OMERO_SERVER/bin/omero"

VIRTUALENV="$PWD/venv-idr-setup-5"
[ -d "$VIRTUALENV" ] || virtualenv --system-site-packages "$VIRTUALENV"
[ -d "$VIRTUALENV/lib/python2.7/site-packages/omero.pth" ] || \
    echo "$OMERO_SERVER/lib/python" > "$VIRTUALENV/lib/python2.7/site-packages/omero.pth"

"$VIRTUALENV/bin/pip" install git+https://github.com/IDR/omero-features.git@IDR-0.0.3

pushd idr-metadata/idr0001-graml-sysgro/features

# Don't forget hql -q outputs the row number as the first column
$omero login -s localhost -u demo -w ome
line=$($omero hql "select id,name from Screen where name like 'idr0001-graml-sysgro%'" --limit 1 -q --style plain)
IFS=, read -a arr <<< "$line"
echo "id:${arr[1]} name:${arr[2]}"
features_file=/uod/idr/filesets/idr0001-graml-sysgro/20151110-features/smc_data_with_header_190515.tsv

sed -i -r \
    -e "s%^(\s+host:).*%\1 localhost%" \
    -e "s%^(\s+user:).*%\1 demo%" \
    -e "s%^(\s+password:).*%\1 ome%" \
    -e "s%^(screenid:).*%\1 ${arr[1]}%" \
    -e "s%^(features:).*%\1 $features_file%" \
    input-sysgro.yml

"$VIRTUALENV/bin/python" load_features.py input-sysgro.yml

popd
date
echo DONE
