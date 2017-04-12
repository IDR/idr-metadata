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


def get_data_dirs(root=ROOT):
    data_dirs = glob.glob("%s/treatment*/mouse*/day*/time lapse/*" % root)
    data_dirs = [_ for _ in data_dirs if "mouse 64/day 6-3" not in _]
    data_dirs.append(
        "%s/treatment start day 3/mouse 64/day 6-3/time lapse" % root
    )
    return data_dirs


def get_processed_fnames(root=ROOT):
    fnames = glob.glob("%s/treatment*/mouse*/day*/processed*/*.tif" % root)
    fnames.extend(
        glob.glob("%s/treatment*/mouse*/day*/processed*/*/*.tif" % root)
    )
    return fnames


def map_dir_names(data_dirs):
    name_map = {}
    for d in data_dirs:
        parts = d.split("/")
        assert len(parts) >= 4
        if parts[-1] == "time lapse":  # mouse 64/day 6-3 exception
            treatment, mouse, day = [
                _.rsplit(" ", 1)[-1] for _ in parts[-4:-1]
            ]
            t = "NONE"
        else:
            treatment, mouse, day = [
                _.rsplit(" ", 1)[-1] for _ in parts[-5:-2]
            ]
            t = parts[-1]
        # use '.' since '_' and '-' are already present in the parts
        name_map[d] = ".".join([treatment, mouse, day, t])
    return name_map
