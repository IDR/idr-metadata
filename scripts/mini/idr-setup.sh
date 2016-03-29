#!/bin/bash

# Install extra utilities
# TODO: Use ansible
sudo yum install -y screen

# Mount network shares
SMB_USER=username
SMB_SHARE1=//orca-3.openmicroscopy.org/idr
SMB_SHARE2=//orca-3.openmicroscopy.org/idr-homes

sudo mkdir -p /uod/idr /idr-homes
sudo mount -t cifs -o username="$SMB_USER" "$SMB_SHARE1" /uod/idr
sudo mount -t cifs -o username="$SMB_USER" "$SMB_SHARE2" /idr-homes

sudo chmod a+x /home/*

OMERO_SERVER=/home/omero/OMERO.server

# Download the render.py plugin if it's not present in this build
if [ ! -f "$OMERO_SERVER/lib/python/omero/plugins/render.py" ]; then
    sudo -u omero sh -c "curl https://raw.githubusercontent.com/manics/openmicroscopy/metadata52-render/components/tools/OmeroPy/src/omero/plugins/render.py > '$OMERO_SERVER/lib/python/omero/plugins/render.py'"
fi

# Setup server settings
sudo -u omero $omero << EOF
config set omero.jvmcfg.heap_size.blitz 16G
admin restart
EOF

# Create users and groups
omero="$OMERO_SERVER/bin/omero"
PUBLIC_PASS="$(openssl rand -base64 12)"

$omero login -s localhost -u root -w omero
$omero group add --type read-only demo
$omero user add --group-name demo -P ome demo idr demo
$omero user add --group-name demo -P "$PUBLIC_PASS" public Public User
$omero logout

# Setup public user
sudo -u omero $omero << EOF
config set omero.web.public.url_filter '^/(webadmin/myphoto/|webclient/(?!(action|annotate_(file|tags|comment|rating|map)|script_ui|ome_tiff|figure_script))|webgateway/(?!(archived_files|download_as)))'
config set omero.web.public.enabled True
config set omero.web.public.user public
config set omero.web.public.password "$PUBLIC_PASS"
config set omero.web.public.server_id 1
config set omero.web.login_redirect '{"redirect": ["webindex"], "viewname": "load_template", "args":["userdata"], "query_string": "experimenter=2"}'
web restart
EOF


# Get metadata
git clone https://github.com/IDR/idr-metadata.git
sed -i -re "s|^bin = .+|bin = '$omero'|" idr-metadata/screen_import.py

# Import- you may want to do this in screen in case your connection is broken
pushd idr-metadata

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

# Convert /idr to /uod/idr for the chosen plates
for plate in $plate_0001 $plate_0002 "$plate_0003" $plate_0005 $plate_0006 \
        $plate_0007 $plate_0008 $plate_0009 $plate_0010 $plate_0017; do
    sed -i -re "s%(^| )/idr/%\1/uod/idr/%" "$plate"
done
for plate in $plate_0004 $plate_0012 $plate_0013 $plate_0015; do
    sed -i -re "s%(^| )/idr/%\1/uod/idr/%" "$(cat "$plate")"
done

mkdir logs
sudo -u omero $omero login -s localhost -u demo -w ome
for plate in $plate_0001 $plate_0002 "$plate_0003" $plate_0004 $plate_0005 \
        $plate_0006 $plate_0007 $plate_0008 $plate_0009 $plate_0010 \
        $plate_0012 $plate_0013 $plate_0015 $plate_007; do
    # Print and log stdout and stderr http://stackoverflow.com/a/692407
    logprefix="${plate%%-*}"
    echo
    echo "***** $logprefix $plate *****"
    echo
    sudo -u omero ./screen_import.py "$plate" > \
        >(tee logs/$logprefix.log) 2> >(tee logs/$logprefix.err >&2)
done




popd


# Rendering
# Manually set channel limits on first image (first plate/run/well):
$omero login -s localhost -u demo -w ome

# idr0005 Image:1
# Hoechst, FF0000, 127, 4095, Greyscale
$omero render copy Image:1 Screen:1

# irc0006 Image:289
# DAPI, 0000FF, 0, 1000
# TRITC, FF0000, 50, 800
$omero render copy Image:289 Screen:2

# Bulk metadata
export OMERO_DEV_PLUGINS=1

$omero metadata populate --file idr-metadata/idr0005-toret-adhesion/screenA/idr0005-screenA-annotation.csv Screen:1
$omero metadata populate --context bulkmap --cfg idr-metadata/idr0005-toret-adhesion/screenA/idr0005-screenA-bulkmap-config.yml Screen:1

$omero metadata populate --file idr-metadata/idr0006-fong-nuclearbodies/screenA/idr0006-screenA-annotation.csv Screen:2
$omero metadata populate --context bulkmap --cfg idr-metadata/idr0006-fong-nuclearbodies/screenA/idr0006-screenA-bulkmap-config.yml Screen:2
