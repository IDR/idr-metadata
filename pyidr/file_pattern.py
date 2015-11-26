"""
Bio-Formats style file patterns.

www.openmicroscopy.org/site/support/bio-formats5.1/formats/pattern-file.html
"""

import re
import string


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
        start = int(start)
    except ValueError:
        try:
            return _expand_letter_range(start, stop, step)
        except InvertedRangeError:
            raise ValueError("inverted range: %s" % r)
    else:
        stop = int(stop) + 1
        if stop <= start:
            raise ValueError("inverted range: %s" % r)
        step = int(step)
        # TODO: support leading zeros
        return map(str, range(start, stop, step))


def expand_block(block):
    return sum((expand_range(_.strip()) for _ in block.split(",")), [])


class FilePattern(object):

    BLOCK_START = "<"
    BLOCK_END = ">"
    BLOCK = re.compile(r"<(.+?)>")

    def __init__(self, pattern):
        self.pattern = pattern

    def blocks(self):
        return re.findall(self.BLOCK, self.pattern)

    # TODO: add iterator through expanded filenames
