Mini IDR test scripts
=====================

These scripts are intended to setup a mini-IDR for testing and development.

OMERO.server
------------

These scripts assume you either have a newly installed OMERO.server on CentOS 7
with access to the network shares containing the IDR filesets *or* a running
Docker image (omero-ssh-systemd).

If you are starting from a fresh CentOS 7 machine you can download and run
https://github.com/manics/infrastructure/blob/omego/openstack/examples/idr-example-omero-bootstrap.sh
to setup OMERO.server. (This script has been added to this gist)

System configuration:`00_openstack.sh` (optional)
-------------------------------------------------

Edit the first few lines of this script to point to the IDR network share.
This script will mount the IDR data directories and assumes selinux.

System installation :`01_install.sh`
------------------------------------

Install OMERO and create several OMERO users including a public OMERO.web user.

Import data: `idr-setup-2.sh`
-----------------------------

Run this script to import a hard-coded list of plates, one from each fileset.
Alternatively you can run `idr-setup-2random.sh` to import randomly chosen plates from each fileset specified as an argument (see the header text in `idr-setup-2random.sh`).
This latter script can be run multiple times to import multiple random plates.


Bulk annotations: `idr-setup-3.sh`
----------------------------------

Run this script to create the bulk/map annotations for each fileset.


Rendering settings: `idr-setup-4.sh`
------------------------------------

Run this script to set the predefined rendering settings for each fileset.
