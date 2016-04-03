Mini IDR test scripts
=====================

These scripts are intended to setup a mini-IDR for testing and development.


OMERO.server
------------

These scripts assume you have a newly installed OMERO.server on CentOS 7, and have access to the network shares containing the IDR filesets.
If you are starting from a fresh CentOS 7 machine you can download and run https://github.com/manics/infrastructure/blob/omego/openstack/examples/idr-example-omero-bootstrap.sh to setup OMERO.server.

Run the following scripts as `root`.


System configuration:`idr-setup-1.sh`
-------------------------------------

Edit the first few lines of this script to point to the IDR network share.
This script will mount the IDR data directories, configure OMERO and create several OMERO users including a public OMERO.web user.


Import data: `idr-setup-2.sh`
-----------------------------

Run this script to import a hard-coded list of plates, one from each fileset.
Alternatively you can run `idr-setup-2random.sh` to import a randomly chosen plate from each fileset- this script can be run multiple times to import multiple random plates.


Bulk annotations: `idr-setup-3.sh`
----------------------------------

Run this script to create the bulk/map annotations for each fileset.


Rendering settings: `idr-setup-4.sh`
------------------------------------

Run this script to set the predefined rendering settings for each fileset.
