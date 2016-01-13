"""
Bio-Formats style file patterns.

www.openmicroscopy.org/site/support/bio-formats5.1/formats/pattern-file.html
"""

import re
import string
import difflib
from itertools import product, izip_longest


class InvertedRangeError(Exception):
    pass


def _expand_letter_range(start, stop, step):
    if not(start.isalpha() and stop.isalpha()):
        raise ValueError("non-literal range: %s-%s" % (start, stop))
    if (start.isupper() != stop.isupper()):
        raise ValueError("mixed case range: %s-%s" % (start, stop))
    letters = string.uppercase if start.isupper() else string.lowercase
    start = letters.index(start)
    stop = letters.index(stop) + 1
    if stop <= start:
        raise InvertedRangeError
    return [letters[_] for _ in xrange(start, stop, step)]


def expand_range(r):
    try:
        r, step = r.strip().split(":")
    except ValueError:
        step = 1
    else:
        try:
            step = int(step)
        except ValueError:
            raise ValueError("non-numeric step: %r" % (step,))
    r = r.strip()
    try:
        start, stop = r.split("-")
    except ValueError:
        return [r]
    try:
        start_str = start
        start = int(start)
    except ValueError:
        try:
            return _expand_letter_range(start, stop, step)
        except InvertedRangeError:
            raise ValueError("inverted range: %s" % r)
    else:
        stop_str = stop
        stop = int(stop) + 1
        if stop <= start:
            raise ValueError("inverted range: %s" % r)
        step = int(step)
        if len(start_str) != len(stop_str):
            return map(str, range(start, stop, step))
        else:
            fmt = "%%0%dd" % len(start_str)
            return [fmt % _ for _ in xrange(start, stop, step)]


def expand_block(block):
    return sum((expand_range(_.strip()) for _ in block.split(",")), [])


def find_pattern_2seq(s1, s2):
    """\
    Find a pattern string that describes the given sequences.

    >>> find_pattern_2seq('z9.tif', 'z10.tif')
    'z<9,10>.tif'

    **FIXME:** currently, if there is more than one variable block,
    the returned pattern represents a *superset* of ``set((s1, s2))``,
    corresponding to the cartesian product of all variable blocks.
    For instance, ``find_pattern_2seq('cBz10.tif', 'cRz9.tif')``
    returns ``'c<B,R>z<10,9>.tif'``, which expands to ``'cBz10.tif',
    'cBz9.tif', 'cRz10.tif', 'cRz9.tif'``.  While incorrect, this can
    be useful to get a hint on the overall pattern for a large file
    list (e.g., ``fnames = sorted(glob.glob("/tmp/*.tif"))`` and then
    ``find_pattern_2seq(fnames[0], fnames[-1])`` ).
    """
    sm = difflib.SequenceMatcher(None, s1, s2, False)
    blocks = sm.get_matching_blocks()
    pattern = [(sm.a[:blocks[0].a], sm.b[:blocks[0].b])]
    for i in xrange(len(blocks) - 1):
        l, r = blocks[i], blocks[i+1]
        pattern.append(sm.a[l.a:l.a+l.size])
        pattern.append((sm.a[l.a+l.size:r.a], sm.b[l.b+l.size:r.b]))
    for i in xrange(len(pattern) - 1, -1, -1):
        if isinstance(pattern[i], tuple):
            if set(pattern[i]) == {""}:
                del pattern[i]
            else:
                pattern[i] = "<%s,%s>" % pattern[i]
    return "".join(pattern)


class FilePattern(object):

    def __init__(self, pattern):
        self.pattern = pattern

    def blocks(self):
        return re.findall(r"<(.+?)>", self.pattern)

    def filenames(self):
        fixed = re.split(r"<.+?>", self.pattern)
        for repl in product(*(expand_block(_) for _ in self.blocks())):
            yield "".join(sum(izip_longest(fixed, repl, fillvalue=""), ()))
