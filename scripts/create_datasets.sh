#!/bin/bash

if [ "$#" -ne 2 ]
then
    echo "
This script iterates over the filePaths.tsv, creates all
Datasets and links them to the Project.

Usage:
./create_datasets.sh [PROJECT ID] [PATH TO filePaths.tsv]
"
    exit 1
fi

projectId=$1
filePaths=$2

# The path to the omero CLI
omero=/opt/omero/server/OMERO.server/bin/omero

#######################

# Create a session
$omero login

# Create a list of dataset names
datasets=`cut -f1 $filePaths | cut -d ':' -f3 | sort -u`

IFS=$'\n'
for dataset in $datasets
do
  datasetId=`$omero hql --ids-only --limit 1 --style plain "select d from Dataset d where d.name='$dataset'"`
  if [ -z $datasetId ]; then
    datasetId=`$omero obj new Dataset name=$dataset`
    echo "Created dataset $dataset , $datasetId"
  else
    datasetId=`echo $datasetId | cut -d ',' -f2 | cut -d ':' -f2`
    proj=`$omero hql --ids-only --limit 1 --style plain "select l.parent from ProjectDatasetLink l where l.child.id='$datasetId'"`
    proj=`echo $proj | cut -d ',' -f2 | cut -d ':' -f2`
    if [ "$proj" != "$projectId" ]
    then
      datasetId=`$omero obj new Dataset name=$dataset`
      echo "Created dataset $dataset , $datasetId"
      echo "Note: At least one dataset with the same name already exists in another Project"
    else
      echo "Dataset $dataset exists, DatasetI:$datasetId"
      continue
    fi
  fi

  linkId=`$omero hql --ids-only --limit 1 --style plain "select l from ProjectDatasetLink l join l.child as ds where ds.name='$dataset' and l.parent.id='$projectId'"`
  if [ -z $linkId ]; then
    linkId=`$omero obj new ProjectDatasetLink parent=ProjectI:$projectId child=$datasetId`
    echo "Created ProjectDatasetLink ProjectI:$projectId $datasetId, $linkId"
  fi
done
