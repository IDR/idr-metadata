#!/bin/sh

# Mount network shares
SMB_USER=username
SMB_SHARE1=//orca-3.openmicroscopy.org/idr
SMB_SHARE2=//orca-3.openmicroscopy.org/idr-homes

sudo mkdir -p /uod/idr /idr-homes
sudo mount -t cifs -o username="$SMB_USER" "$SMB_SHARE1" /uod/idr
sudo mount -t cifs -o username="$SMB_USER" "$SMB_SHARE2" /idr-homes

sudo chmod a+x /home/*

OMERO_SERVER=/home/omero/server/OMERO.server

# Download the render.py plugin if it's not present in this build
if [ ! -f "$OMERO_SERVER/lib/python/omero/plugins/render.py" ]; then
    sudo -u omero sh -c "curl https://raw.githubusercontent.com/manics/openmicroscopy/metadata52-render/components/tools/OmeroPy/src/omero/plugins/render.py > '$OMERO_SERVER/lib/python/omero/plugins/render.py'"
fi

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

# Import
pushd idr-metadata

sudo -u omero $omero login -s localhost -u demo -w ome

plate_0005=idr0005-toret-adhesion/screenA/plates/Primary_001
plate_0006=idr0006-fong-nuclearbodies/screenA/plates/11001
plate_0002=idr0002-heriche-condensation/screenA/plates/plate1_1_013
plate_0015=idr0015-UNKNOWN-taraoceans/screenA/plates/TARA_HCS1_H5_G100001472_G100001473--2013_09_28_19_45_25_chamber--U00--V01

sed -i -re "s|^/idr/|/uod/idr/|" "$plate_0005"
sudo -u omero ./screen_import.py "$plate_0005"

sed -i -re "s|^/idr/|/uod/idr/|" "$plate_0006"
sudo -u omero ./screen_import.py "$plate_0006"

sed -i -re "s|^/idr/|/uod/idr/|" "$plate_0002"
# FAILS
sudo -u omero ./screen_import.py "$plate_0002"

sed -i -re "s| /idr/| /uod/idr/|" "$(cat "$plate_0015")"
sudo -u omero ./screen_import.py "$plate_0015"



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
