import os
import unittest
from cStringIO import StringIO
import ConfigParser

from pyidr.screenio import ScreenWriter, ScreenReader, ScreenError


class TestScreenIO(unittest.TestCase):

    def setUp(self, screen_name=None):
        self.name, self.rows, self.columns, self.fields = "Foo", 3, 4, 2
        self.screen_name = screen_name
        self.size = self.rows * self.columns
        self.all_field_values = []

    def _field_values(self, idx):
        values = [
            "%s_%d_%d.fake" % (self.name, idx, _) for _ in xrange(self.fields)
        ]
        self.all_field_values.append(values)
        return values


class TestScreenWriter(TestScreenIO):

    def setUp(self, screen_name=None):
        super(TestScreenWriter, self).setUp(screen_name=screen_name)
        fout = StringIO()
        self.all_field_values = []
        self.extra_kv = {"Dimensions": "ZCT"}
        kwargs = {"screen_name": screen_name} if screen_name else {}
        writer = ScreenWriter(
            self.name, self.rows, self.columns, self.fields, **kwargs
        )
        for i in xrange(self.size):
            writer.add_well(self._field_values(i), extra_kv=self.extra_kv)
        writer.write(fout)
        fout.seek(0)
        self.cp = ConfigParser.ConfigParser()
        self.cp.readfp(fout)

    def test_sections(self):
        self.assertEqual(
            self.cp.sections(),
            ['Plate'] + ['Well %d' % _ for _ in xrange(self.size)]
        )

    def test_plate(self):
        sec = 'Plate'
        self.assertTrue(self.cp.has_section(sec))
        for k, v in [
                ("Name", self.name),
                ("Rows", self.rows),
                ("Columns", self.columns),
                ("Fields", self.fields),
        ]:
            self.assertTrue(self.cp.has_option(sec, k))
            self.assertEqual(self.cp.get(sec, k), str(v))
        if self.screen_name:
            self.assertEqual(self.cp.get(sec, "ScreenName"), self.screen_name)
        else:
            self.assertRaises(
                ConfigParser.NoOptionError, self.cp.get, sec, "ScreenName"
            )

    def test_wells(self):
        for i in xrange(self.rows):
            for j in xrange(self.columns):
                idx = i * self.columns + j
                sec = 'Well %d' % idx
                self.assertTrue(self.cp.has_section(sec))
                for k, v in [("Row", i), ("Column", j)]:
                    self.assertTrue(self.cp.has_option(sec, k))
                    self.assertEqual(self.cp.get(sec, k), str(v))
                for f in xrange(self.fields):
                    k = 'Field_%d' % f
                    self.assertTrue(self.cp.has_option(sec, k))
                    self.assertEqual(self.cp.get(sec, k),
                                     self.all_field_values[idx][f])
                    for ek, ev in self.extra_kv.iteritems():
                        self.assertTrue(self.cp.has_option(sec, ek))
                        self.assertEqual(self.cp.get(sec, ek), ev)


class TestScreenWriterName(TestScreenWriter):

    def setUp(self):
        super(TestScreenWriterName, self).setUp(screen_name="FooScreen")


class TestScreenReader(TestScreenIO):

    def setUp(self, screen_name=None):
        super(TestScreenReader, self).setUp(screen_name=screen_name)
        self.conf_lines = [
            "[Plate]",
            "Name = %s" % self.name,
            "Rows = %d" % self.rows,
            "Columns = %d" % self.columns,
            "Fields = %d" % self.fields,
        ]
        if screen_name:
            self.conf_lines.append("ScreenName = %s" % screen_name)
        self.conf_lines.append("")
        for i in xrange(self.rows):
            for j in xrange(self.columns):
                idx = (i * self.columns + j)
                self.conf_lines.extend([
                    "[Well %d]" % idx,
                    "Row = %d" % i,
                    "Column = %d" % j,
                ])
                for k, v in enumerate(self._field_values(idx)):
                    self.conf_lines.append("Field_%d = %s" % (k, v))
                self.conf_lines.append("")
        self.f = StringIO()
        self.f.write(os.linesep.join(self.conf_lines))
        self.f.seek(0)
        self.reader = ScreenReader(self.f)

    def test_plate(self):
        for a in "name", "screen_name", "rows", "columns", "fields":
            self.assertEqual(getattr(self.reader, a), getattr(self, a))

    def test_wells(self):
        for idx, w in enumerate(self.reader.wells):
            self.assertEqual(w['Fields'], self.all_field_values[idx])


class TestScreenReaderName(TestScreenReader):

    def setUp(self):
        super(TestScreenReaderName, self).setUp(screen_name="FooScreen")


class TestScreenReaderBad(unittest.TestCase):

    def test_bad_conf(self):
        self.assertRaises(ConfigParser.Error, ScreenReader, StringIO("foo"))

    def test_missing_sections(self):
        missing_well = os.linesep.join([
            "[Plate]",
            "Name = Foo",
            "Rows = 1",
            "Columns = 1",
            "Fields = 1",
        ])
        for bad_content in "", "[Foo]", missing_well:
            bad_f = StringIO(bad_content)
            self.assertRaises(ScreenError, ScreenReader, bad_f)

    def test_missing_plate_options(self):
        conf_lines = [
            "[Plate]",
            "Name = Foo",
            "Rows = 0",
            "Columns = 0",
            "Fields = 0",
        ]
        for i in xrange(1, len(conf_lines)):
            copy = conf_lines[:]
            del copy[i]
            bad_f = StringIO(os.linesep.join(copy))
            self.assertRaises(ScreenError, ScreenReader, bad_f)

    def test_bad_plate_options(self):
        conf_lines = [
            "[Plate]",
            "Name = Foo",
            "Rows = 0",
            "Columns = 0",
            "Fields = 0",
        ]
        for i in xrange(2, len(conf_lines)):
            copy = conf_lines[:]
            copy[i] = copy[i].replace("0", "0.5")
            bad_f = StringIO(os.linesep.join(copy))
            self.assertRaises(ScreenError, ScreenReader, bad_f)

    def test_bad_well_idx(self):
        conf_lines = [
            "[Plate]",
            "Name = Foo",
            "Rows = 1",
            "Columns = 1",
            "Fields = 0",
            "",
            "[Well 0]",
            "Row = 0",
            "Column = 1",
        ]
        bad_f = StringIO(os.linesep.join(conf_lines))
        self.assertRaises(ScreenError, ScreenReader, bad_f)


def load_tests(loader, tests, pattern):
    test_cases = (
        TestScreenWriter,
        TestScreenWriterName,
        TestScreenReader,
        TestScreenReaderName,
        TestScreenReaderBad,
    )
    suite = unittest.TestSuite()
    for tc in test_cases:
        suite.addTests(loader.loadTestsFromTestCase(tc))
    return suite


if __name__ == "__main__":
    suite = load_tests(unittest.defaultTestLoader, None, None)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
