idr0015-UNKNOWN-taraoceans
==========================

Bulk-annotations CSV file
-------------------------

    virtualenv venv --system-site-packages
    venv/bin/pip install -r requirements
    venv/bin/python create_bulkanns.py

This should create a file `taraoceans.BULK_ANNOTATION.csv`.

Plate MapAnnotations
--------------------

    source venv/bin/activate
    ~/OMERO.server/bin/omero shell --login
    
    execfile('annotation_plates.py')
