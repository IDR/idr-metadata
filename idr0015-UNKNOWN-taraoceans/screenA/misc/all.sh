#!/bin/bash
while read -r line;
do
	#/idr/filesets/idr0015-UNKNOWN-taraoceans/20150918-tara/RAW_DATA/TARA_HCS1_H5_G100011084_G100010958--2013_10_04_09_31_04/slide--S00/chamber--U00--V01
	CHAMBER=$(basename $line)
	PLATE=$(dirname $line)
	PLATE=$(dirname $PLATE)
	PLATE=$(basename $PLATE)
	NAME="$PLATE"_"$CHAMBER"
	FILE=$(realpath ../patterns/"$NAME".screen)
	echo $FILE
	./make_screen.py $line/field* > $FILE
	echo "$FILE" > ../plates/$NAME
done < raw
