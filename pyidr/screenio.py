import string
import ConfigParser
import abc


PLATE = "Plate"
WELL = "Well %d"


class ScreenError(Exception):
    pass


class ScreenIO(object):

    @abc.abstractmethod
    def __init__(self):
        self.name = None
        self.screen_name = None
        self.rows = 0
        self.columns = 0
        self.fields = 0

    def index1d(self, i, j):
        return i * self.columns + j

    def index2d(self, idx):
        return divmod(idx, self.columns)

    def well_sec(self, idx):
        return WELL % idx


class ScreenWriter(ScreenIO):

    def __init__(self, name, rows, columns, fields, screen_name=None,
                 exclude_readers=None):
        super(ScreenWriter, self).__init__()
        self.name = name
        self.rows = int(rows)
        self.columns = int(columns)
        self.fields = int(fields)
        self.screen_name = screen_name
        self.exclude_readers = exclude_readers
        self.alpha_map = dict(enumerate(string.uppercase))
        self.reset()

    def reset(self):
        self.cp = ConfigParser.ConfigParser()
        self.cp.optionxform = str  # case-sensitive option names
        self.__add_plate_entry()
        self.__well_count = 0

    def __add_plate_entry(self):
        self.cp.add_section(PLATE)
        self.cp.set(PLATE, "Name", self.name)
        if self.screen_name:
            self.cp.set(PLATE, "ScreenName", self.screen_name)
        self.cp.set(PLATE, "Rows", "%d" % self.rows)
        self.cp.set(PLATE, "Columns", "%d" % self.columns)
        self.cp.set(PLATE, "Fields", "%d" % self.fields)
        if self.exclude_readers:
            self.cp.set(PLATE, "ExcludeReaders",
                        ",".join(self.exclude_readers))

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
        sec = self.well_sec(idx)
        self.cp.add_section(sec)
        self.cp.set(sec, "Row", "%d" % i)
        self.cp.set(sec, "Column", "%d" % j)
        for k, v in extra_kv.iteritems():
            self.cp.set(sec, k, v)
        for f, v in enumerate(field_values):
            if v:
                self.cp.set(sec, "Field_%d" % f, v)
        self.__well_count += 1

    def write(self, outf):
        self.cp.write(outf)


class ScreenReader(ScreenIO):

    def __init__(self, f):
        super(ScreenReader, self).__init__()
        self.__f = f
        self.cp = ConfigParser.ConfigParser()
        self.cp.optionxform = str
        self.wells = []
        self.__read()

    @property
    def f(self):
        return self.__f

    def __assert_sec(self, sec):
        if not self.cp.has_section(sec):
            raise ScreenError("%r section missing" % (sec,))

    def __checked_get(self, sec, opt, getter_name="get"):
        getter = getattr(self.cp, getter_name)
        try:
            return getter(sec, opt)
        except ConfigParser.NoOptionError:
            raise ScreenError("Required %r option missing in %r" % (opt, sec))

    def get(self, sec, opt):
        return self.__checked_get(sec, opt)

    def getint(self, sec, opt):
        try:
            return self.__checked_get(sec, opt, getter_name="getint")
        except ValueError:
            raise ScreenError("%r must be an integer" % (opt,))

    def __read(self):
        self.cp.readfp(self.__f)
        self.__read_plate()
        for idx in xrange(self.rows * self.columns):
            self.__read_well(idx)

    def __read_plate(self):
        self.__assert_sec(PLATE)
        self.name = self.get(PLATE, "Name")
        try:
            self.screen_name = self.get(PLATE, "ScreenName")
        except ScreenError:
            pass
        self.rows = self.getint(PLATE, "Rows")
        self.columns = self.getint(PLATE, "Columns")
        self.fields = self.getint(PLATE, "Fields")

    def __read_well(self, idx):
        sec = self.well_sec(idx)
        self.__assert_sec(sec)
        row = self.getint(sec, "Row")
        column = self.getint(sec, "Column")
        exp_r, exp_c = self.index2d(idx)
        if (row, column) != (exp_r, exp_c):
            raise ScreenError(
                "%r: bad (row, column), should be %r" % (sec, (exp_r, exp_c))
            )
        w = dict(self.cp.items(sec))
        fields = []
        for i in xrange(self.fields):
            field_key = "Field_%d" % i
            try:
                fields.append(self.get(sec, field_key))
            except ScreenError:
                pass
            else:
                del w[field_key]
        w['Fields'] = fields
        self.wells.append(w)
