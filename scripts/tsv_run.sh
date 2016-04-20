A="
idr0001-graml-sysgro
idr0002-heriche-condensation
idr0003-breker-plasticity
idr0004-thorpe-rad52
idr0005-toret-adhesion
idr0006-fong-nuclearbodies
idr0007-srikumar-sumo
idr0008-rohn-actinome
idr0009-simpson-secretion
idr0010-doil-dnadamage
idr0012-fuchs-cellmorph
idr0013-neumann-mitocheck
idr0015-UNKNOWN-taraoceans
idr0017-breinig-drugscreen
"

B="
idr0005-toret-adhesion
idr0008-rohn-actinome
idr0009-simpson-secretion
idr0012-fuchs-cellmorph
idr0013-neumann-mitocheck
"
C="
idr0008-rohn-actinome
idr0012-fuchs-cellmorph
"

set -e
set -u

L=C
for x in $C;
do
    scr=${x%%-**}
    out=$x/screen$L/$scr-screen$L-plates.tsv
    in=$x/screen$L/plates
    scripts/tsv_plates.py $out $in/*
    git add $out
    git rm -rf $in
    git commit -m "$scr: convert plates to tsv"
done
