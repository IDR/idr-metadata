#!/usr/bin/env python

r"""\
Run a pydoop-features calc job on Celery using
https://github.com/openmicroscopy/ansible-role-celery-docker

Any arguments after '--' will be passed to pyfeatures calc.

Example: ./calc.py
  --user celery --out-dir /uod/idr-scratch
  --broker redis://:PASSWORD@example.org:6379
  /uod/idr/features/idr0013-neumann-mitocheck/screenA/input/ --
  -l -W 672 -H 512 --offset-x 336 --offset-y 256 -x 1344 -y 1024

Assumes an input directory with one subdirectory (containing the Avro
input files) per plate.

If provided, the argument to the --include option must be a text file
containing a list of (subdir, file) pairs as whitespace-separated
basenames, e.g., "plate1\tplate1_0.avro". Tasks will be submitted only
for the specified pairs.
"""

import sys
import os
import argparse
import errno
from celery import Celery


def iter_input(input_dir):
    for subdir_bn in os.listdir(input_dir):
        path = os.path.join(input_dir, subdir_bn)
        try:
            basenames = os.listdir(path)
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                pass
        for avro_bn in basenames:
            if avro_bn.endswith(".avro"):
                yield subdir_bn, avro_bn


def get_whitelist(include_fn):
    with open(include_fn) as f:
        return set(tuple(_.split()) for _ in f)


def make_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_dir', metavar="DIR", help="input dir")
    parser.add_argument('--broker', help="Celery broker URL",
                        default='redis://')
    parser.add_argument("-o", "--out-dir", metavar="DIR", help="output dir")
    parser.add_argument("-u", "--user", help="run-as user", default="celery")
    parser.add_argument("-l", "--log", help="log task ids to this file",
                        default="taskid-calc.log")
    parser.add_argument("-i", "--docker-img", help="docker image name",
                        default="manics/pyfeatures:merge")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="print celery args and exit")
    parser.add_argument("--limit", type=int, metavar="INT",
                        help="max number of tasks to submit")
    parser.add_argument("--include", metavar="FILE",
                        help="run only for listed dir/input files")
    return parser


def get_celery_args(args, calc_opts, subdir_bn, avro_bn):
    celery_args = dict(
        image=args.docker_img,
        # We need to create the output directories, which can only be done
        # on the worker, so mount the top-level directory (this will be
        # mounted as /output, and must be writeable by the container user)
        outputpath=args.out_dir,
    )

    if args.user:
        celery_args['user'] = str(args.user)

    in_path = os.path.join(args.input_dir, subdir_bn)
    celery_args['inputpath'] = in_path

    tag, _ = os.path.splitext(avro_bn)

    # This must be writeable by the celery-worker (not the docker user)
    out_subdir = os.path.join(args.out_dir, subdir_bn)
    celery_args['logoutfile'] = os.path.join(
        out_subdir, '%s.log' % tag)

    cmd = ['calc']
    if calc_opts:
        cmd.extend(calc_opts)

    # The parent dir of the input avro file will be mounted as /input
    # Top-level output dir is mounted as /output inside the container
    cmd.extend([
        os.path.join('/input', avro_bn),
        '--out-dir',
        os.path.join('/output', subdir_bn)
    ])

    # TODO: quote these arguments?
    celery_args['command'] = ' '.join(cmd)

    return celery_args


def main(argv):
    try:
        idx = argv.index("--")
    except ValueError:
        calc_opts = []
    else:
        calc_opts = argv[(idx + 1):]
        del argv[idx:]
    parser = make_parser()
    args = parser.parse_args(argv[1:])
    whitelist = get_whitelist(args.include) if args.include else None

    celery = Celery(broker=args.broker)

    with open(args.log, "w") as fo:
        for i, (subdir_bn, avro_bn) in enumerate(iter_input(args.input_dir)):
            if whitelist and (subdir_bn, avro_bn) not in whitelist:
                continue
            if args.limit and i >= args.limit:
                break

            celery_args = get_celery_args(args, calc_opts, subdir_bn, avro_bn)

            if args.dry_run:
                print celery_args
            else:
                r = celery.send_task('tasks.run_docker', kwargs=celery_args)
                fo.write(str(r) + "\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
