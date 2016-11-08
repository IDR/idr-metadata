# annotate

These scripts are for use with GNU parallel
(https://www.gnu.org/software/parallel/) to
re-generate the map annotations for an IDR
instance in parallel.

Steps
-----

 * Install parallel if not already installed.
 * Setup your input file as desired.
 * Optionally create a `jobs` file with the number
   of simultaneous calls to re-ann.bash that should run.
 * Call `run`.
