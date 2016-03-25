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

$omero login -s localhost -u root -w omero
$omero group add --type read-only demo
$omero user add --group-name demo -P ome demo idr demo
$omero logout

# Get metadata
git clone https://github.com/IDR/idr-metadata.git
sed -i -re "s|^bin = .+|bin = '$omero'|" idr-metadata/screen_import.py

# Import
sudo -u omero $omero login -s localhost -u demo -w ome

PLATES="
    idr-metadata/idr0005-toret-adhesion/screenA/plates/Primary_001
    idr-metadata/idr0006-fong-nuclearbodies/screenA/plates/11001
"
for plate in $PLATES; do
    sed -i -re "s|^/idr/|/uod/idr/|" "$plate"
    sudo -u omero idr-metadata/screen_import.py "$plate"
done

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
