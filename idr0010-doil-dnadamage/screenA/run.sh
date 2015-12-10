#!/bin/bash
cd plates
for x in /idr/filesets/idr0010-doil-dnadamage/20150501-original/Restored\ GW\ screen/*; do X=$(basename "$x") && ls "$x" > $X; done
for plate in [0-9]*;
do
    # "001-23 <53bp1,dapi>.stk"
    BP=$(grep -iE "b[bp]1" "$plate" | cut -f2- -d" ")
    DAPI=$(grep -iE "dapi" "$plate" | cut -f2- -d" ")
    echo "# generated $(date)" > $plate.pattern
    echo "$plate <${BP%.stk},${DAPI%.stk}>.stk" >> $plate.pattern
done
