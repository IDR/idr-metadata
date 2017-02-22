import os
import errno
import glob


ROOT = ("/uod/idr/filesets/idr0026-weigelin-immunotherapy/20160701-original/"
        "PNAS_2015")


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise


def get_data_dirs():
    data_dirs = glob.glob("%s/treatment*/mouse*/day*/time lapse/*" % ROOT)
    data_dirs = [_ for _ in data_dirs if "mouse 64/day 6-3" not in _]
    data_dirs.append(
        "%s/treatment start day 3/mouse 64/day 6-3/time lapse" % ROOT
    )
    return data_dirs
