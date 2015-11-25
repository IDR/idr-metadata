import string
from ConfigParser import ConfigParser


class ScreenWriter(object):

    PLATE = "Plate"
    WELL = "Well %d"

    def __init__(self, name, rows, columns, fields, screen_name=None):
        self.name = name
        self.rows = int(rows)
        self.columns = int(columns)
        self.fields = int(fields)
        self.screen_name = screen_name
        self.alpha_map = dict(enumerate(string.uppercase))
        self.reset()

    def reset(self):
        self.cp = ConfigParser()
        self.cp.optionxform = str  # case-sensitive option names
        self.__add_plate_entry()
        self.__well_count = 0

    def __add_plate_entry(self):
        self.cp.add_section(self.PLATE)
        self.cp.set(self.PLATE, "Name", self.name)
        if self.screen_name:
            self.cp.set(self.PLATE, "ScreenName", self.screen_name)
        self.cp.set(self.PLATE, "Rows", "%d" % self.rows)
        self.cp.set(self.PLATE, "Columns", "%d" % self.columns)
        self.cp.set(self.PLATE, "Fields", "%d" % self.fields)

    def index1d(self, i, j):
        return i * self.columns + j

    def index2d(self, idx):
        return divmod(idx, self.columns)

    def coordinates(self, idx):
        i, j = self.index2d(idx)
        return (self.alpha_map[i], j + 1)

    def add_well(self, field_values=None, i=None, j=None, extra_kv=None):
        if self.__well_count >= self.rows * self.columns:
            raise ValueError("too many wells")
        if field_values is None:
            field_values = []
        if field_values and len(field_values) != self.fields:
            raise ValueError(
                "expected %d fields, got %d" % (self.fields, len(field_values))
            )
        if i is None:
            idx = self.__well_count
            i, j = self.index2d(idx)
        elif j is None:
            idx = i
            i, j = self.index2d(idx)
        else:
            idx = self.index1d(i, j)
        if extra_kv is None:
            extra_kv = {}
        #--
        sec = self.WELL % idx
        self.cp.add_section(sec)
        self.cp.set(sec, "Row", "%d" % i)
        self.cp.set(sec, "Column", "%d" % j)
        for k, v in extra_kv.iteritems():
            self.cp.set(sec, k, v)
        for f, v in enumerate(field_values):
            self.cp.set(sec, "Field_%d" % f, v)
        #--
        self.__well_count += 1

    def write(self, outf):
        self.cp.write(outf)
