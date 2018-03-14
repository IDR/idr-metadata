#!/bin/bash
file="mapping.tsv"
omero="/opt/omero/server/OMERO.server/bin/omero"

while IFS='	' read -r f1 f2
do
	imageids=`$omero hql --ids-only --limit 100 --style csv -q "select img from DatasetImageLink l join l.parent as ds join l.child as img where ds.name = '$f1'"`
	IFS=',' read -r -a array <<< $imageids
	
	for imageid in "${array[@]}"
	do
		imageid=${imageid/ */}
		if [[ $imageid == Image* ]]
		then
			printf 'Applying rendering settings %s (dataset %s) to %s \n' "$f2" "$f1" "$imageid"
			$omero render edit $imageid $f2
		fi
	done
done <"$file"

